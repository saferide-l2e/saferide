from django.urls import path

from . import views

app_name = "departures"

urlpatterns = [
    path("search/", views.search, name="search"),
    path("<uuid:departure_id>/", views.departure_detail, name="detail"),
    path("<uuid:departure_id>/availability/", views.availability, name="availability"),
    path("driver/", views.driver_dashboard, name="dashboard"),
    path("driver/new/", views.departure_create, name="create"),
    path("driver/<uuid:departure_id>/manage/", views.departure_manage, name="manage"),
    path("driver/<uuid:departure_id>/transition/", views.departure_transition, name="transition"),
    path("driver/<uuid:departure_id>/check-in/", views.departure_check_in, name="check_in"),
]
