from django.urls import path

from agent.views import AnswerSpeechView, InterviewView

urlpatterns = [
    path("interview/", InterviewView.as_view(), name="interview"),
    path(
        "interview/<int:log_id>/speech/",
        AnswerSpeechView.as_view(),
        name="answer-speech",
    ),
]
