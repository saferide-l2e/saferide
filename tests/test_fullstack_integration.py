"""Real-template and server-action smoke tests for the full-stack integration PR.

Unlike tests/test_frontend_contract.py these deliberately DON'T stub templates.
All pages use the real Django database fixtures and their actual backend views.
"""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_visitor_pages_use_real_design(client):
    for route in ("core:home", "accounts:login", "accounts:register", "safety:route_updates"):
        response = client.get(reverse(route))
        assert response.status_code == 200, (route, response.status_code)
        assert b"SafeRide" in response.content
        assert b"main-content" in response.content


def test_eligible_passenger_searches_real_published_departure(client, passenger, departure):
    client.force_login(passenger)
    response = client.get(
        reverse("departures:search"),
        {"origin": "Jibowu", "destination": "Mile 2"},
    )
    assert response.status_code == 200
    assert b"Jibowu" in response.content
    assert departure.vehicle.plate_display.encode() in response.content
    assert str(departure.id).encode() in response.content


def test_real_booking_action_and_private_code_end_to_end(client, passenger, departure):
    client.force_login(passenger)
    details = client.get(reverse("departures:detail", args=[departure.id]))
    assert details.status_code == 200
    assert b"Reserve one seat" in details.content
    response = client.post(reverse("bookings:reserve", args=[departure.id]))
    assert response.status_code == 302
    assert "/bookings/" in response.url
    page = client.get(response.url)
    assert page.status_code == 200
    assert b"Your boarding pass" in page.content
    assert b"Cancel my reservation" in page.content
    assert b"Your private code" in page.content
    history = client.get(reverse("bookings:index"))
    assert history.status_code == 200
    assert b"Jibowu" in history.content


def test_driver_can_render_registered_vehicle_and_departure_pages(client, driver, vehicle, departure):
    client.force_login(driver)
    for name in ("vehicles:list", "vehicles:create", "departures:dashboard",
                 "departures:create"):
        response = client.get(reverse(name))
        assert response.status_code == 200, (name, response.status_code)
    manage = client.get(reverse("departures:manage", args=[departure.id]))
    assert manage.status_code == 200
    assert b"Manage departure" in manage.content
    assert b"Private passenger roster" in manage.content


def test_verification_and_private_reporting_pages_work(client, passenger):
    client.force_login(passenger)
    for name in ("verification:status", "accounts:profile", "safety:report",
                 "safety:route_update_new"):
        response = client.get(reverse(name))
        assert response.status_code == 200, (name, response.status_code)


def test_driver_cannot_access_another_departure(client, other_driver, departure):
    client.force_login(other_driver)
    assert client.get(reverse("departures:manage", args=[departure.id])).status_code == 403
