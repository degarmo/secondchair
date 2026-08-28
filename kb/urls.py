"""Intake API routes, mounted at /api/intake/.

No authentication: single-user demo, deliberately deferred.
"""

from django.urls import path

from . import views

app_name = "kb"

urlpatterns = [
    path("sessions/", views.create_session, name="session-create"),
    path("sessions/<int:pk>/next/", views.next_question, name="session-next"),
    path(
        "sessions/<int:pk>/complete/",
        views.complete_session,
        name="session-complete",
    ),
    path(
        "sessions/<int:pk>/transcript/",
        views.transcript,
        name="session-transcript",
    ),
    path("turns/", views.create_turn, name="turn-create"),
]
