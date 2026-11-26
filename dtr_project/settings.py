"""
Django settings for the ERS DTR system.

EDIT THE 'ERS SETTINGS' BLOCK BELOW — database login and the app login.
Everything else can stay as-is for a normal LAN deployment.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ================================================================= #
#  ERS SETTINGS  — edit these                                       #
# ================================================================= #

# --- MySQL database (create it first, see README) ---
DB_NAME = os.environ.get("DTR_DB_NAME", "ers_dtr")
DB_USER = os.environ.get("DTR_DB_USER", "ers_dtr")
DB_PASS = os.environ.get("DTR_DB_PASS", "CHANGE_THIS_DB_PASSWORD")
DB_HOST = os.environ.get("DTR_DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DTR_DB_PORT", "3306")

# --- App login (one shared username + password) ---
AUTH_USER = os.environ.get("DTR_USER", "admin")
AUTH_PASS = os.environ.get("DTR_PASS", "ers2026")

# --- Server ---
# For a LAN tool this is fine; lock it down to your server's IP/host if you prefer.
ALLOWED_HOSTS = os.environ.get("DTR_ALLOWED_HOSTS", "*").split(",")
SECRET_KEY = os.environ.get("DTR_SECRET_KEY", "change-this-to-a-long-random-string")
DEBUG = os.environ.get("DTR_DEBUG", "0") == "1"

# ================================================================= #

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "dtr",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
]

ROOT_URLCONF = "dtr_project.urls"
WSGI_APPLICATION = "dtr_project.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": []},
}]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASS,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# Sessions in the DB (survives restarts, shared across workers)
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "ers_dtr_sess"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14      # 2 weeks

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Manila"
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
