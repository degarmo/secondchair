from django.contrib import admin
from django.urls import include, path

from agent.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("agent.urls")),
    path("healthz/", health, name="health"),
]
