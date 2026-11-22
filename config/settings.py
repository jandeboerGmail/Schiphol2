import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "flights",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

WSGI_APPLICATION = "config.wsgi.application"

# No database needed: flights come from the Schiphol API and are cached.
DATABASES = {}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Schiphol API, OAuth 2.0 client-credentials flow (https://developer.schiphol.nl).
# Read lazily so the project still starts without them; the board then shows a setup hint.
SCHIPHOL_CLIENT_ID = os.environ.get("SCHIPHOL_CLIENT_ID", "")
SCHIPHOL_CLIENT_SECRET = os.environ.get("SCHIPHOL_CLIENT_SECRET", "")
SCHIPHOL_TOKEN_URL = os.environ.get("SCHIPHOL_TOKEN_URL", "https://api.auth.schiphol.nl/oauth/token")
# The audience must match the API tier you subscribed to (public tier shown here).
SCHIPHOL_AUDIENCE = os.environ.get("SCHIPHOL_AUDIENCE", "https://api.schiphol.nl/public")
SCHIPHOL_FLIGHTS_URL = os.environ.get(
    "SCHIPHOL_FLIGHTS_URL", "https://api.schiphol.nl/public/public-flights/v4/flights"
)
SCHIPHOL_CACHE_SECONDS = int(os.environ.get("SCHIPHOL_CACHE_SECONDS", "60"))
