"""Role and object permission tests (BE-13)."""

from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import BookingStatus
from apps.bookings.services import reserve
from apps.departures.models import Departure, DepartureStatus

pytestmark = pytest.mark.django_db


def test_anonymous_is_redirected_to_login(departure):
    response = Client().get(reverse("departures:detail", args=[departure.id]))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


def test_passenger_cannot_open_driver_dashboard(passenger):
    client = Client()
    client.force_login(passenger)
    assert client.get(reverse("departures:dashboard")).status_code == 403


def test_driver_cannot_manage_another_drivers_departure(other_driver, departure):
    client = Client()
    client.force_login(other_driver)
    response = client.get(reverse("departures:manage", args=[departure.id]))
    assert response.status_code == 403


def test_passenger_cannot_read_another_passengers_booking(passenger, other_passenger, departure):
    booking, _ = reserve(passenger, departure)
    client = Client()
    client.force_login(other_passenger)
    response = client.get(reverse("bookings:detail", args=[booking.id]))
    assert response.status_code == 403


def test_unverified_passenger_cannot_reserve_through_view(unverified_passenger, departure):
    client = Client()
    client.force_login(unverified_passenger)
    response = client.post(reverse("bookings:reserve", args=[departure.id]))
    assert response.status_code == 302
    assert not departure.bookings.exists()


def test_published_search_only_lists_open_departures(
    passenger, driver, vehicle, route, stub_frontend_templates
):
    open_dep = Departure.objects.create(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=timezone.now() + timedelta(hours=1),
        snapshot_capacity=4,
        status=DepartureStatus.BOARDING_OPEN,
    )
    Departure.objects.create(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=timezone.now() + timedelta(hours=1),
        snapshot_capacity=4,
        status=DepartureStatus.DRAFT,
    )
    client = Client()
    client.force_login(passenger)
    response = client.get(reverse("departures:search"), {"origin": "Jibowu", "destination": "Mile"})
    assert response.status_code == 200
    ids = [d.id for d in response.context["departures"]]
    assert open_dep.id in ids
    assert len(ids) == 1


def test_booking_status_json_is_owner_only(passenger, other_passenger, departure):
    booking, _ = reserve(passenger, departure)
    client = Client()
    client.force_login(passenger)
    ok = client.get(reverse("bookings:status", args=[booking.id]))
    assert ok.status_code == 200
    assert ok.json()["status"] == BookingStatus.HELD

    client.force_login(other_passenger)
    assert client.get(reverse("bookings:status", args=[booking.id])).status_code == 403
