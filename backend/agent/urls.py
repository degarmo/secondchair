from django.urls import path

from agent.views import InterviewView

urlpatterns = [
    path("interview/", InterviewView.as_view(), name="interview"),
]
