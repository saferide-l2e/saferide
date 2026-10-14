from django.contrib import admin
from django.urls import path

from apps.core.views import health, home

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
]

# Development-only visual reviews; disabled by default on main/production.
from django.conf import settings

if settings.PREVIEW_MODE:
    from apps.core.preview_views import gallery, page

    urlpatterns += [
        path("preview/", gallery, name="preview-gallery"),
        path("preview/<slug:slug>/", page, name="preview-page"),
    ]
