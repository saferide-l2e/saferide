"""Lagos ride-product integration: interactive map UI, sample itinerary and profile privacy."""
import pytest
from django.urls import reverse

from apps.departures.demo_discovery import sample_buses
from apps.departures.models import Departure
from apps.verification.models import VerificationStatus

pytestmark = pytest.mark.django_db


def test_home_has_dynamic_lagos_stop_and_dark_mode_controls(client):
    page = client.get(reverse("core:home"))
    assert page.status_code == 200
    html = page.content.decode()
    for required in (
        "data-map-origin", "data-map-destination", "site-from",
        "lagos_experience.css", "lagos_experience.js", "lagos-park.svg",
        "data-theme-toggle", "Victoria Island", "Lekki Phase 1",
        "View directions",
    ):
        assert required in html, required


def test_illustrative_bus_choice_is_informational_and_does_not_write_departures(client):
    before = Departure.objects.count()
    response = client.get(reverse("departures:sample_ride"), {
        "origin": "Agege", "destination": "Lekki Phase 1", "option": 2,
    })
    assert response.status_code == 200
    sample = sample_buses("Agege", "Lekki Phase 1")[1]
    html = response.content.decode()
    assert sample["ride_class"] in html
    assert str(sample["fare_estimate_naira"]) in html
    assert "No payment is collected" in html
    assert "not an actual bookable service" in html
    assert "/reserve/" not in html
    assert Departure.objects.count() == before


@pytest.mark.parametrize("option", ["-1", "5", "not-an-integer"])
def test_sample_invalid_option_is_not_found(client, option):
    response = client.get(reverse("departures:sample_ride"), {
        "origin": "Yaba", "destination": "Ikeja", "option": option,
    })
    assert response.status_code == 404


def test_profile_can_be_updated_while_pending_without_auto_approval(client, unverified_passenger):
    client.force_login(unverified_passenger)
    initial = {
        "fictional_data": "on", "simulated_review": "on",
        "profile_name": "Penny Driver", "home_area": "Yaba", "preferred_stop": "Jibowu",
    }
    assert client.post(reverse("verification:submit"), initial).status_code == 302
    profile = unverified_passenger.verification
    profile.refresh_from_db()
    assert profile.status == VerificationStatus.PENDING
    assert profile.profile_name == "Penny Driver"
    assert profile.home_area == "Yaba"
    next_data = {**initial, "home_area": "Ikeja", "preferred_stop": "Mile 2"}
    assert client.post(reverse("verification:submit"), next_data).status_code == 302
    profile.refresh_from_db()
    assert profile.status == VerificationStatus.PENDING
    assert profile.home_area == "Ikeja"
    assert profile.preferred_stop == "Mile 2"
    assert not unverified_passenger.is_verified
