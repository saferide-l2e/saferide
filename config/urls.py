from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("verification/", include("apps.verification.urls")),
    path("driver/vehicles/", include("apps.vehicles.urls")),
    path("routes/", include("apps.routes.urls")),
    path("departures/", include("apps.departures.urls")),
    path("bookings/", include("apps.bookings.urls")),
    path("safety/", include("apps.safety.urls")),
]

# Internal reviews stay under /preview/ and never replace real application URLs.
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
