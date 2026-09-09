"""Django settings for the corydegarmo site backend.

Every environment-specific value is read from the environment. Local
development reads them from a `.env` file at the repository root; Render
supplies them as service environment variables.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

load_dotenv(REPO_ROOT / ".env")


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str) -> list[str]:
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


DEBUG = env_flag("DEBUG", default=False)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "SECRET_KEY must be set when DEBUG is off. Generate one with: "
            'python -c "from django.core.management.utils import '
            'get_random_secret_key; print(get_random_secret_key())"'
        )
    # Development only. Production takes the branch above and refuses to start.
    SECRET_KEY = "django-insecure-local-development-key-not-for-production"

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# The React app is served from its own origin, so every browser call to this
# service is cross-origin and needs an explicit entry here.
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
if DEBUG and not CORS_ALLOWED_ORIGINS:
    # Vite's dev server (5173) and its preview server (4173).
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if not host.startswith(".")
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "agent",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if not DEBUG:
    # Serves the admin's own CSS/JS in production. The public site is a
    # separate static site and never goes through Django. In development
    # runserver handles static files, so WhiteNoise stays out of the way.
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    if not DEBUG:
        raise ImproperlyConfigured("DATABASE_URL must be set when DEBUG is off.")
    database_url = "postgres://localhost:5432/secondchair"

DATABASES = {
    "default": dj_database_url.parse(
        database_url,
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}

# Throttle counters live in the database so every gunicorn worker shares one
# count. The table is created by agent migration 0002.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Chicago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_RATES": {"interview": "20/hour", "speech": "60/hour"},
    "EXCEPTION_HANDLER": "agent.exceptions.friendly_exception_handler",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "agent": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# --- Interview agent -------------------------------------------------------

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# Only needed when ANTHROPIC_API_KEY is an account-level key rather than one
# created inside a workspace. Such keys are rejected by /v1/messages with
# "not scoped to a workspace" unless this id travels with the request. Leave
# unset for a workspace-scoped key, which is the simpler setup.
ANTHROPIC_WORKSPACE_ID = os.environ.get("ANTHROPIC_WORKSPACE_ID") or ""
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL") or "claude-sonnet-5"
ANTHROPIC_MAX_TOKENS = int(os.environ.get("ANTHROPIC_MAX_TOKENS") or 600)
ANTHROPIC_TIMEOUT_SECONDS = float(os.environ.get("ANTHROPIC_TIMEOUT_SECONDS") or 45)

KNOWLEDGE_BASE_PATH = Path(
    os.environ.get("KNOWLEDGE_BASE_PATH") or (BASE_DIR / "kb" / "KNOWLEDGE_BASE.md")
)

# Turns of prior conversation sent back to the model, counted server-side.
INTERVIEW_HISTORY_LIMIT = 12
INTERVIEW_QUESTION_MAX_LENGTH = 500

# Shown to visitors when the agent cannot answer (rate limit, upstream error).
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL") or "degarmo@gmail.com"

# --- Spoken answers (ElevenLabs) -------------------------------------------
#
# Optional. With no key or no voice id the site simply never offers to speak:
# the frontend hides the play button rather than showing one that fails.
# List the voices on the account with: python manage.py list_voices

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2"
ELEVENLABS_OUTPUT_FORMAT = (
    os.environ.get("ELEVENLABS_OUTPUT_FORMAT") or "mp3_44100_128"
)
ELEVENLABS_TIMEOUT_SECONDS = float(
    os.environ.get("ELEVENLABS_TIMEOUT_SECONDS") or 30
)

# Longest answer that will be sent for synthesis. Answers are already capped
# by ANTHROPIC_MAX_TOKENS; this bounds the bill if that cap ever changes.
SPEECH_MAX_CHARS = int(os.environ.get("SPEECH_MAX_CHARS") or 3000)

# Synthesized audio is cached so replaying an answer costs nothing.
SPEECH_CACHE_SECONDS = int(os.environ.get("SPEECH_CACHE_SECONDS") or 60 * 60 * 24 * 7)

# --- Production hardening --------------------------------------------------

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
