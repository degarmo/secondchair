"""Production settings.

Every secret is required here. A missing one raises at import time, which
means a bad deploy fails immediately instead of serving traffic with an
insecure default.
"""

from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS, STORAGES, env, env_bool

SECRET_KEY = env("SECRET_KEY", required=True)
DEBUG = env_bool("DEBUG", default=False)

# Render supplies the service's own hostname at runtime; it is appended
# rather than replacing ALLOWED_HOSTS so a custom domain still works.
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RENDER_EXTERNAL_HOSTNAME]

CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host != "*"]

if not ALLOWED_HOSTS:
    raise RuntimeError(
        "ALLOWED_HOSTS is empty. Set it, or run on Render where "
        "RENDER_EXTERNAL_HOSTNAME is provided automatically."
    )

# Hashed filenames plus pre-compressed variants, served by whitenoise.
STORAGES["staticfiles"] = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

# TLS is terminated at Render's proxy, so Django needs the forwarded header
# to know the original request was HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
