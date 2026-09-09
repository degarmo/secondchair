from django.conf import settings
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def friendly_exception_handler(exc, context):
    """Give throttled visitors a sentence they can act on."""
    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, Throttled):
        response.data = {
            "detail": (
                "That's 20 questions in an hour, which is the limit. "
                f"Email me at {settings.CONTACT_EMAIL} and I'll answer "
                "myself."
            ),
            "code": "throttled",
        }

    return response
