from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("for-drivers/", views.for_drivers, name="for_drivers"),
    path("safety-support/", views.safety_support, name="safety_support"),
    path("health/", views.health, name="health"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
