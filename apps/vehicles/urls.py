from django.urls import path

from . import views

app_name = "vehicles"

urlpatterns = [
    path("", views.vehicle_list, name="list"),
    path("new/", views.vehicle_create, name="create"),
    path("profile/", views.driver_profile, name="profile"),
]
