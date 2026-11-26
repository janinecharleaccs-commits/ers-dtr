# ERS DTR — Django + MySQL (self-hosted, Proxmox)

Your own server version of the DTR system. Django serves the app and the API;
MySQL holds the data. No Google, no PHP. (Signature block intentionally omitted.)

## Project layout

```
manage.py
requirements.txt
dtr_project/        settings.py (edit this), urls, wsgi, asgi
dtr/                models.py, views.py (the API), urls.py
dtr/frontend/index.html   the whole web app (UI + logic)
dtr/migrations/     database tables
```

The only file you normally edit is **`dtr_project/settings.py`** (DB login + app
login), or set the same values as environment variables (shown below).

---

## 1. The Proxmox guest

Create an **Ubuntu 26.04 (or Debian 13) VM** from the ISO — 1 vCPU / 1 GB
RAM / 8 GB disk is plenty. (An LXC container works too.) Give it a static IP on
your LAN. During a Debian netinst, pick only "SSH server" + "standard system
utilities" (no desktop). Then inside it:

```bash
apt update && apt install -y python3-venv python3-pip mariadb-server
```

(MariaDB is a drop-in MySQL; the app works the same.)

## 2. The database

```bash
mysql
```
```sql
CREATE DATABASE ers_dtr CHARACTER SET utf8mb4;
CREATE USER 'ers_dtr'@'localhost' IDENTIFIED BY 'YOUR_DB_PASSWORD';
GRANT ALL PRIVILEGES ON ers_dtr.* TO 'ers_dtr'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 3. The app

```bash
# copy this project to /opt/ers-dtr (scp, git, or Proxmox file push), then:
cd /opt/ers-dtr
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Edit **`dtr_project/settings.py`** — set `DB_PASS`, and change `AUTH_PASS`
(the app login). Also set a long random `SECRET_KEY`. Then create the tables:

```bash
python manage.py migrate
```

Test it:

```bash
python manage.py runserver 0.0.0.0:8000
```

Open `http://<server-ip>:8000/` → login screen → `admin` / `ers2026` (or
whatever you set). The first load seeds the 4 sample employees, 4 shifts, and
the status list.

## 4. Run it for real (gunicorn + systemd)

Stop the test server. Create `/etc/systemd/system/ers-dtr.service`:

```ini
[Unit]
Description=ERS DTR
After=network.target mariadb.service

[Service]
WorkingDirectory=/opt/ers-dtr
ExecStart=/opt/ers-dtr/venv/bin/gunicorn dtr_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
Restart=always
# You can also pass settings via the environment instead of editing settings.py:
# Environment=DTR_DB_PASS=YOUR_DB_PASSWORD
# Environment=DTR_PASS=your-app-password
# Environment=DTR_SECRET_KEY=some-long-random-string

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now ers-dtr
```

Now it runs on boot at `http://<server-ip>:8000/`.

### (Optional) nginx in front, on port 80/443

```nginx
server {
    listen 80;
    server_name dtr.yourdomain.local;   # or the server IP
    client_max_body_size 25m;           # for large DTR uploads
    location / { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; proxy_set_header X-Forwarded-For $remote_addr; }
}
```

Add TLS with certbot if you expose it beyond the LAN.

---

## Settings you can change

In `dtr_project/settings.py` (or as environment variables):

| Setting | Env var | What it is |
| ------- | ------- | ---------- |
| `DB_NAME` / `DB_USER` / `DB_PASS` / `DB_HOST` / `DB_PORT` | `DTR_DB_*` | MySQL connection |
| `AUTH_USER` / `AUTH_PASS` | `DTR_USER` / `DTR_PASS` | the app login |
| `SECRET_KEY` | `DTR_SECRET_KEY` | Django secret — make it long and random |
| `ALLOWED_HOSTS` | `DTR_ALLOWED_HOSTS` | comma-separated hostnames/IPs (default `*`) |

After changing settings (or the login), `systemctl restart ers-dtr`.

## Features

Full current feature set: supervisors, custom shifts with Saturday schedules,
Category + Status, the two per-day dropdowns, Rest Day / No Work tick boxes,
custom From/To date-range reports, alphabetical Excel with gaps between
employees, borders + yellow/orange highlights, Excel/PDF import with the year
tick box, day/night theme, logo, header line and footer. The **signature block
is left out** of this version.

## Notes

- `dtr/frontend/index.html` loads three small JS libraries from CDNs
  (xlsx-js-style for reading uploads, ExcelJS for the styled download, pdf.js for
  PDF uploads). If the server has no internet / your LAN blocks CDNs, tell me and
  I'll bundle them locally so nothing external is needed.
- The API lives at `/api/` and uses Django **session** auth (login stored
  server-side). Same single username/password for everyone, since all browsers
  hit the same server.
- Back up MySQL with `mysqldump ers_dtr > backup.sql` on a cron, or snapshot the
  Proxmox guest.
- The login is a simple shared gate; keep the app on your LAN/VPN, and use the
  nginx+TLS option if it ever needs to be reachable from outside.
