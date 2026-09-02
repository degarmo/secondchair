"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

from kb.views import VoicePage

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("kb.urls")),
    path("", VoicePage.as_view(), name="voice"),
]
