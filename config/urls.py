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
    from apps.core.preview_views import app_home, gallery, page, public_page

    urlpatterns += [
        path("preview/", app_home, name="preview-home"),
        path("preview/screens/", gallery, name="preview-gallery"),
        path("preview/how-it-works/", public_page, {"slug": "how-it-works"}, name="preview-how"),
        path("preview/drive/", public_page, {"slug": "drive"}, name="preview-drive"),
        path("preview/support/", public_page, {"slug": "support"}, name="preview-support"),
        path("preview/my-trips/", public_page, {"slug": "my-trips"}, name="preview-passenger-hub"),
        path("preview/<slug:slug>/", page, name="preview-page"),
    ]
