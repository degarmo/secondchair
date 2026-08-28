"""Development settings.

Used by ``manage.py`` unless ``DJANGO_SETTINGS_MODULE`` says otherwise.
"""

from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS, SECRET_KEY

# Development only: let the project start without a .env so a fresh clone
# can run `manage.py` immediately. Production supplies a real key or refuses
# to boot.
if not SECRET_KEY:
    SECRET_KEY = "django-insecure-local-development-key-not-for-deployment"

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
