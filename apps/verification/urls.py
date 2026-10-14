from django.urls import path

from . import views

app_name = "verification"

urlpatterns = [
    path("", views.status, name="status"),
    path("submit/", views.submit_request, name="submit"),
]
