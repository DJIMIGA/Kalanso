"""Routes de premier niveau. Chaque application déclare les siennes dans son propre urls.py."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
