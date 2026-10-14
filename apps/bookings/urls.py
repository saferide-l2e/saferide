from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.my_bookings, name="index"),
    path("<uuid:booking_id>/", views.booking_detail, name="detail"),
    path("<uuid:booking_id>/status/", views.booking_status, name="status"),
    path("departures/<uuid:departure_id>/reserve/", views.reserve_seat, name="reserve"),
    path("<uuid:booking_id>/cancel/", views.cancel_booking, name="cancel"),
    path("departures/<uuid:departure_id>/waitlist/", views.join_waitlist_view, name="join_waitlist"),
    path("waitlist/<uuid:entry_id>/accept/", views.accept_offer_view, name="accept_offer"),
    path("<uuid:booking_id>/confirm-arrival/", views.confirm_arrival_view, name="confirm_arrival"),
]
