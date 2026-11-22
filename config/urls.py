from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from sitepages.health import healthz

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("django-admin/", admin.site.urls),
    path("admin/", include("crm.urls")),
    path("", include("sitepages.urls")),
]

if settings.FEATURE_GOOGLE_LOGIN:
    urlpatterns.insert(0, path("accounts/", include("allauth.urls")))
