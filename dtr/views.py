import json

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Employee, Shift, Record, Status

DEFAULT_STATUSES = [
    "ABSENT", "HALF-DAY", "LEAVE WITH PAY", "LEAVE WITHOUT PAY", "LEAVE WITH PAY NOT APPROVED",
    "EXCUSED", "NO WORK", "REST DAY", "OFFICIAL BUSINESS", "FIELD WORK", "WORK FROM HOME",
    "OTHER BRANCH BIO", "UNDERTIME", "FOR HR EVALUATION", "BIO EXCUSED FW", "OTHERS",
]

# ------------------------------------------------------------------ #
#  PAGE                                                               #
# ------------------------------------------------------------------ #
def index(request):
    html = (settings.BASE_DIR / "dtr" / "frontend" / "index.html").read_text(encoding="utf-8")
    return HttpResponse(html)


# ------------------------------------------------------------------ #
#  SEED + SERIALIZE                                                   #
# ------------------------------------------------------------------ #
def seed():
    if Employee.objects.count() == 0:
        for r in [
            ("e1", "1001", "Juan Dela Cruz", "Team Leader A", "shift1", "Active"),
            ("e2", "1002", "Maria Santos", "Team Leader A", "shift2", "Active"),
            ("e3", "1003", "Jose Rizal", "Team Leader B", "shift3", "Active"),
            ("e4", "1004", "Ana Reyes", "Team Leader B", "shift1", "Active"),
        ]:
            Employee.objects.create(id=r[0], employee_id=r[1], name=r[2], supervisor=r[3], shift=r[4], status=r[5])
    if Shift.objects.count() == 0:
        for r in [
            ("shift1", "Shift 1", "07:30", "16:30", "11:30", "12:30", True, "", "15:00"),
            ("shift2", "Shift 2", "08:00", "17:00", "12:00", "13:00", True, "", "15:00"),
            ("shift3", "Shift 3", "09:00", "18:00", "", "", False, "", "15:00"),
            ("shift4", "Shift 4", "07:00", "16:00", "", "", False, "", "15:00"),
        ]:
            Shift.objects.create(key=r[0], label=r[1], start=r[2], end=r[3], lunch_out=r[4],
                                 lunch_in=r[5], has_lunch=r[6], sat_start=r[7], sat_end=r[8])
    if Status.objects.count() == 0:
        for s in DEFAULT_STATUSES:
            Status.objects.create(name=s)


def emp_json(e):
    return {"id": e.id, "employeeId": e.employee_id, "name": e.name,
            "supervisor": e.supervisor, "shift": e.shift, "status": e.status}


def shift_json(s):
    ss, se = s.sat_start or "", s.sat_end or ""
    return {"key": s.key, "label": s.label, "start": s.start, "end": s.end,
            "lunchOut": s.lunch_out, "lunchIn": s.lunch_in, "hasLunch": bool(s.has_lunch),
            "satStart": ss, "satEnd": se, "satEnabled": bool(ss or se)}


def records_json():
    out = {}
    for r in Record.objects.all():
        out.setdefault(r.date, {})[r.emp_id] = {
            "timeIn": r.time_in, "lunchOut": r.lunch_out, "lunchIn": r.lunch_in, "timeOut": r.time_out,
            "dayStatus": r.day_status, "missingReason": r.missing_reason, "remarks": r.remarks, "category": r.category,
        }
    return out


def bootstrap():
    seed()
    return {
        "employees": [emp_json(e) for e in Employee.objects.all().order_by("name")],
        "records": records_json(),
        "shifts": [shift_json(s) for s in Shift.objects.all()],
        "statuses": [s.name for s in Status.objects.all()],
        "dbUrl": "",
    }


# ------------------------------------------------------------------ #
#  WRITE HANDLERS                                                     #
# ------------------------------------------------------------------ #
def upsert_employee(emp):
    name = (emp.get("name") or "").strip()
    if not name:
        raise ValueError("Employee name is required.")
    eid = (emp.get("employeeId") or "").strip()
    _id = emp.get("id") or ""
    dupe = Employee.objects.exclude(id=_id).filter(name__iexact=name)
    if eid:
        dupe = dupe | Employee.objects.exclude(id=_id).filter(employee_id=eid)
    if dupe.exists():
        raise ValueError("Duplicate employee (same name or ID already exists).")
    sup = (emp.get("supervisor") or "").strip()
    sh = emp.get("shift") or "shift1"
    st = emp.get("status") or "Active"
    if _id:
        Employee.objects.filter(id=_id).update(employee_id=eid, name=name, supervisor=sup, shift=sh, status=st)
    else:
        import time
        Employee.objects.create(id="e" + str(int(time.time() * 1000)), employee_id=eid,
                                name=name, supervisor=sup, shift=sh, status=st)
    return bootstrap()


def delete_employee(_id):
    Employee.objects.filter(id=_id).delete()
    return bootstrap()


def upsert_shift(s):
    label = (s.get("label") or "").strip()
    if not label:
        raise ValueError("Shift name is required.")
    if not s.get("start") or not s.get("end"):
        raise ValueError("Start and end time are required.")
    sat = bool(s.get("satEnabled"))
    has_lunch = bool(s.get("hasLunch"))
    fields = dict(
        label=label, start=s["start"], end=s["end"],
        lunch_out=(s.get("lunchOut") or "") if has_lunch else "",
        lunch_in=(s.get("lunchIn") or "") if has_lunch else "",
        has_lunch=has_lunch,
        sat_start=(s.get("satStart") or "") if sat else "",
        sat_end=(s.get("satEnd") or "") if sat else "",
    )
    key = s.get("key") or ""
    if key:
        Shift.objects.filter(key=key).update(**fields)
    else:
        import time
        Shift.objects.create(key="s" + str(int(time.time() * 1000)), **fields)
    return bootstrap()


def delete_shift(key):
    Shift.objects.filter(key=key).delete()
    return bootstrap()


def add_status(name):
    name = (name or "").strip().upper()
    if not name:
        raise ValueError("Status name is required.")
    if Status.objects.filter(name__iexact=name).exists():
        raise ValueError("That status already exists.")
    Status.objects.create(name=name)
    return bootstrap()


def delete_status(name):
    Status.objects.filter(name=name).delete()
    return bootstrap()


@transaction.atomic
def save_day(date, day_obj):
    day_obj = day_obj or {}
    for emp_id, rec in day_obj.items():
        rec = rec or {}
        Record.objects.filter(date=date, emp_id=emp_id).delete()
        has = any(rec.get(k) for k in ("timeIn", "lunchOut", "lunchIn", "timeOut",
                                       "dayStatus", "missingReason", "remarks", "category"))
        if not has:
            continue
        Record.objects.create(
            date=date, emp_id=emp_id,
            time_in=rec.get("timeIn", ""), lunch_out=rec.get("lunchOut", ""),
            lunch_in=rec.get("lunchIn", ""), time_out=rec.get("timeOut", ""),
            day_status=rec.get("dayStatus", ""), missing_reason=rec.get("missingReason", ""),
            remarks=rec.get("remarks", ""), category=rec.get("category", ""),
        )
    return True


@transaction.atomic
def import_records(payload_json, mode):
    payload = json.loads(payload_json)
    fields = ["timeIn", "lunchOut", "lunchIn", "timeOut"]
    fmap = {"timeIn": "time_in", "lunchOut": "lunch_out", "lunchIn": "lunch_in", "timeOut": "time_out"}
    days, emps, count = set(), set(), 0
    for date, by_emp in payload.items():
        days.add(date)
        for emp_id, inc in (by_emp or {}).items():
            emps.add(emp_id)
            inc = inc or {}
            rec, _ = Record.objects.get_or_create(date=date, emp_id=emp_id)
            for f in fields:
                nv = inc.get(f) or ""
                if nv == "":
                    continue
                col = fmap[f]
                if mode == "fill":
                    if not getattr(rec, col):
                        setattr(rec, col, nv)
                else:
                    setattr(rec, col, nv)
            rec.save()
            count += 1
    return {"days": len(days), "employees": len(emps), "records": count}


# ------------------------------------------------------------------ #
#  API DISPATCH                                                       #
# ------------------------------------------------------------------ #
@csrf_exempt
def api(request):
    try:
        body = json.loads(request.body or b"{}")
    except Exception:
        body = {}
    action = body.get("action", "")
    args = body.get("args", []) or []

    if action != "login" and not request.session.get("dtr_auth"):
        return JsonResponse({"error": "Not signed in", "auth": False}, status=401)

    try:
        if action == "login":
            u = (args[0] if len(args) > 0 else "").strip()
            p = args[1] if len(args) > 1 else ""
            ok = (u == settings.AUTH_USER and p == settings.AUTH_PASS)
            if ok:
                request.session["dtr_auth"] = True
            return JsonResponse({"result": {"ok": ok}})
        if action == "logout":
            request.session.flush()
            return JsonResponse({"result": True})
        if action == "getBootstrap":
            return JsonResponse({"result": bootstrap()})
        if action == "upsertEmployee":
            return JsonResponse({"result": upsert_employee(args[0])})
        if action == "deleteEmployee":
            return JsonResponse({"result": delete_employee(args[0])})
        if action == "upsertShift":
            return JsonResponse({"result": upsert_shift(args[0])})
        if action == "deleteShift":
            return JsonResponse({"result": delete_shift(args[0])})
        if action == "addStatus":
            return JsonResponse({"result": add_status(args[0])})
        if action == "deleteStatus":
            return JsonResponse({"result": delete_status(args[0])})
        if action == "saveDay":
            return JsonResponse({"result": save_day(args[0], args[1])})
        if action == "importRecords":
            return JsonResponse({"result": import_records(args[0], args[1] if len(args) > 1 else "overwrite")})
        return JsonResponse({"error": "Unknown action: " + str(action)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
