"""Intake and answering routes.

No authentication: single-user demo, deliberately deferred.
"""

from django.urls import path

from . import views

app_name = "kb"

urlpatterns = [
    path("intake/sessions/", views.create_session, name="session-create"),
    path(
        "intake/sessions/<int:pk>/next/",
        views.next_question,
        name="session-next",
    ),
    path(
        "intake/sessions/<int:pk>/complete/",
        views.complete_session,
        name="session-complete",
    ),
    path(
        "intake/sessions/<int:pk>/transcript/",
        views.transcript,
        name="session-transcript",
    ),
    path("intake/turns/", views.create_turn, name="turn-create"),
    path("ask/", views.ask, name="ask"),
]
