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
