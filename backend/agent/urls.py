from django.urls import path

from agent.views import AnswerSpeechView, InterviewView, interview_config

urlpatterns = [
    path("interview/", InterviewView.as_view(), name="interview"),
    path("interview/config/", interview_config, name="interview-config"),
    path(
        "interview/<int:log_id>/speech/",
        AnswerSpeechView.as_view(),
        name="answer-speech",
    ),
]
