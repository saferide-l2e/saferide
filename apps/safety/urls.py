from django.urls import path

from . import views

app_name = "safety"

urlpatterns = [
    path("reviews/<uuid:booking_id>/", views.review_booking, name="review"),
    path("reports/", views.report_incident, name="report"),
    path("reports/<uuid:booking_id>/", views.report_incident, name="report_booking"),
    path("route-updates/", views.route_updates, name="route_updates"),
    path("route-updates/new/", views.route_update, name="route_update_new"),
]
