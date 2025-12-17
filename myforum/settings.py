import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# helpers
def getenv_bool(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")

# SECURITY
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
DEBUG = getenv_bool("DEBUG", False)

# ALLOWED_HOSTS: comma separated or '*' (for MVP)
_raw_allowed = os.environ.get("ALLOWED_HOSTS", "")
if _raw_allowed:
    ALLOWED_HOSTS = [h.strip() for h in _raw_allowed.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = ["*"] if DEBUG else ["*"]  # for MVP allow all; tighten in prod

# If behind proxy/load balancer (Railway, Render), trust forwarded proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CSRF trusted origins (comma separated, e.g. https://myapp.up.railway.app)
_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# Paths
STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    "django_htmx",
    "ckeditor",
    "forum.apps.ForumConfig",
]

# Middleware - WhiteNoise placed early (after SecurityMiddleware)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

# Use a robust but safe staticfiles storage for quick deploys
# CompressedManifestStaticFilesStorage is stricter (fails if files missing).
# For fast MVP use CompressedStaticFilesStorage to avoid manifest errors.
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

ROOT_URLCONF = "myforum.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "myforum.wsgi.application"

# Database via DATABASE_URL env (Postgres on Railway)
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", "600"))
        )
    }
else:
    DATABASES = {
        "default": dj_database_url.parse(f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}")
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

# Internationalization
LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@myforum.local")

# Login redirects
LOGIN_REDIRECT_URL = "/profile/"
LOGOUT_REDIRECT_URL = "/"

# Hero backgrounds (keep defaults or override in env if you want)
HERO_BACKGROUNDS = [
    "img/hero/bg1.png",
    "img/hero/bg2.jpg",
    "img/hero/bg3.jpg",
]
HERO_BG_MODE = os.environ.get("HERO_BG_MODE", "rotate")
HERO_BG_AUTOPLAY_DELAY = int(os.environ.get("HERO_BG_AUTOPLAY_DELAY", "6000"))
HERO_BG_FADE_SPEED = int(os.environ.get("HERO_BG_FADE_SPEED", "800"))

# Logging to console so Railway/Render UI shows errors
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler",},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

# Helpful for debugging behind proxies
if getenv_bool("SHOW_SQL", False):
    LOGGING["loggers"] = {"django.db.backends": {"level": "DEBUG", "handlers": ["console"]}}

# Optional security tweaks (enable in production)
SESSION_COOKIE_SECURE = getenv_bool("SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = getenv_bool("CSRF_COOKIE_SECURE", True)
SECURE_SSL_REDIRECT = getenv_bool("SECURE_SSL_REDIRECT", False)  # enable after HTTPS