"""SafeRide arbitrary-route demo suggestions and public browse security contracts."""

from datetime import UTC, datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.departures.demo_discovery import clean_stop, sample_buses
from apps.departures.models import Departure

pytestmark = pytest.mark.django_db


def test_demo_buses_are_stable_and_explicitly_non_bookable():
    now = datetime(2026, 10, 15, 15, 0, tzinfo=UTC)
    first = sample_buses("Agege", "Yaba", now=now)
    assert len(first) == 4
    assert first == sample_buses("Agege", "Yaba", now=now)
    assert first != sample_buses("Agege", "Oshodi", now=now)
    assert all(bus["is_simulated"] and not bus["bookable"] for bus in first)
    assert all(bus["scheduled_departure_at"] > now + timedelta(minutes=10) for bus in first)
    assert all(0 < bus["available_seats"] <= bus["capacity"] for bus in first)
    assert all(bus["plate_display"].startswith("DEMO-") for bus in first)
    assert all("Fictional" in bus["driver_public_name"] for bus in first)


@pytest.mark.parametrize("origin,destination", [
    ("", "Mile 2"), ("Jibowu", ""), ("  Mile 2  ", "mile 2"),
    ("", ""), ("Yaba", "yaba"),
])
def test_empty_or_identical_stops_do_not_generate_fictional_options(origin, destination):
    assert sample_buses(origin, destination) == []


def test_arbitrary_route_shows_four_labelled_examples_without_database_writes(client):
    before = Departure.objects.count()
    route = reverse("departures:search")
    response = client.get(route, {"origin": "Agege", "destination": "Lekki Phase 1"})
    assert response.status_code == 200
    html = response.content.decode()
    assert b"Find buses" in response.content
    assert "Agege" in html and "Lekki Phase 1" in html
    assert "Demo suggestions, not live bus availability" in html
    assert "four fictional examples" in html
    assert "See this sample bus" in html
    assert len(response.context["sample_buses"]) == 4
    assert not response.context["buses"]
    assert Departure.objects.count() == before
    assert "/reserve/" not in html
    assert html.count('class="bus-card demo-bus-card"') == 4


def test_unverified_user_can_browse_but_cannot_reserve(client, unverified_passenger, departure):
    client.force_login(unverified_passenger)
    search = client.get(reverse("departures:search"), {"origin": "Jibowu", "destination": "Mile2"})
    assert search.status_code == 200
    assert str(departure.pk) in search.content.decode()
    assert not search.context["sample_buses"]
    assert "Only staff-approved passengers can reserve" in search.content.decode()
    denied = client.post(reverse("bookings:reserve", args=[departure.pk]))
    assert denied.status_code == 302
    assert not departure.bookings.exists()


def test_anonymous_can_discover_real_published_demo_departures(client, departure):
    response = client.get(reverse("departures:search"), {
        "origin": "Jibowu", "destination": "Mile 2",
    })
    assert response.status_code == 200
    assert str(departure.pk) in response.content.decode()
    detail = client.get(reverse("departures:detail", args=[departure.pk]))
    assert detail.status_code == 302
    assert "/accounts/login/" in detail.url


def test_generated_routes_escape_untrusted_text_and_validate_input(client):
    url = reverse("departures:search")
    bad = client.get(url, {"origin": "<script>alert(1)</script>", "destination": "Yaba"})
    assert bad.status_code == 200
    assert "<script>alert(1)</script>" not in bad.content.decode()
    assert "&lt;script&gt;" in bad.content.decode()
    same = client.get(url, {"origin": " Jibowu ", "destination": "jibowu"})
    assert same.context["error_message"]
    assert not same.context["sample_buses"]


def test_stop_names_are_bounded_and_example_count_is_capped():
    assert len(clean_stop("A" * 500)) == 80
    assert clean_stop("  Mile    2  ") == "Mile 2"
    assert len(sample_buses("Jibowu", "Mile 2", count=200)) == 4


def test_browsing_samples_does_not_break_existing_real_booking(client, passenger, departure):
    client.force_login(passenger)
    route = reverse("departures:search")
    resp = client.get(route, {"origin": "Jibowu", "destination": "Mile 2"})
    assert resp.status_code == 200
    assert resp.context["buses"]
    assert not resp.context["sample_buses"]
    booking = client.post(reverse("bookings:reserve", args=[departure.pk]))
    assert booking.status_code == 302
    assert "/bookings/" in booking.url
