from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from ask.views import ask
from interview.views import next_prompt, submit_answer
from kb.views import ClaimViewSet, EntityViewSet, SourceViewSet

router = DefaultRouter()
router.register("claims", ClaimViewSet, basename="claim")
router.register("entities", EntityViewSet)
router.register("sources", SourceViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Serves the built frontend. In development the Vite dev server owns
    # this route instead and proxies /api through to here.
    path("", TemplateView.as_view(template_name="index.html"), name="app"),
    path("api/", include(router.urls)),
    path("api/interview/next/", next_prompt, name="interview-next"),
    path("api/interview/answer/", submit_answer, name="interview-answer"),
    path("api/ask/", ask, name="ask"),
]
