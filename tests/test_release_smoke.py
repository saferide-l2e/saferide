"""Release-critical SafeRide journeys exercised against isolated test PostgreSQL only."""
from html.parser import HTMLParser
from urllib.parse import urlsplit

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.bookings.models import Booking, BookingStatus
from apps.verification.models import VerificationStatus
from apps.verification.services import approve

pytestmark = pytest.mark.django_db


class _InternalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        if href.startswith("/") and not href.startswith("//"):
            path = urlsplit(href).path
            if path.startswith("/") and not path.startswith("/static/"):
                self.paths.add(path)


def test_public_homepage_links_never_land_on_not_found(client):
    """Follow every internal homepage and footer anchor, not just URL names."""
    page = client.get(reverse("core:home"))
    assert page.status_code == 200
    links = _InternalLinks()
    links.feed(page.content.decode())
    assert reverse("accounts:register") in links.paths
    assert reverse("departures:search") in links.paths
    for path in sorted(links.paths):
        result = client.get(path)
        assert result.status_code in {200, 302}, (path, result.status_code)


def test_demo_signup_to_declaration_to_staff_approval(client, staff):
    registration = reverse("accounts:register")
    initial = client.get(registration, {"role": "DRIVER"})
    assert initial.status_code == 200
    assert initial.context["form"].initial["role"] == "DRIVER"

    registration_data = {
        "role": "PASSENGER",
        "display_name": "QA Demo Passenger",
        "email": "release-smoke@example.test",
        "password1": "StrongPilotPassword!2026",
        "password2": "StrongPilotPassword!2026",
    }
    created = client.post(registration, registration_data)
    assert created.status_code == 302
    assert created.url == reverse("verification:status")
    user = get_user_model().objects.get(email=registration_data["email"])
    assert user.verification_status == VerificationStatus.NOT_SUBMITTED

    verification = client.get(reverse("verification:status"))
    assert verification.status_code == 200
    assert b'name="fictional_data"' in verification.content
    assert b'name="simulated_review"' in verification.content
    assert b'id="verification-declaration"' in verification.content
    assert b"Submit for staff review" in verification.content

    submitted = client.post(reverse("verification:submit"), {
        "fictional_data": "on",
        "simulated_review": "on",
    }, follow=True)
    assert submitted.status_code == 200
    assert b"Awaiting review" in submitted.content
    user.verification.refresh_from_db()
    assert user.verification.status == VerificationStatus.PENDING
    assert not user.is_verified

    approve(user.verification, staff, note="Fictional account for automated QA")
    approved = client.get(reverse("verification:status"))
    assert b"Simulated approval complete" in approved.content
    user.refresh_from_db()
    assert user.is_verified


def test_login_and_signout_are_csrf_safe(client, passenger):
    client.logout()
    response = client.post(reverse("accounts:login"), {
        "email": passenger.email,
        "password": "saferide-test-123",
    })
    assert response.status_code == 302
    assert client.get(reverse("accounts:profile")).status_code == 200
    assert client.get(reverse("accounts:logout")).status_code == 405
    assert client.get(reverse("accounts:profile")).status_code == 200
    assert client.post(reverse("accounts:logout")).status_code == 302
    assert client.get(reverse("accounts:profile")).status_code == 302


def test_passenger_reserves_then_cancels_using_real_pages(client, passenger, departure):
    client.force_login(passenger)
    search = client.get(reverse("departures:search"), {"origin": "Jibowu", "destination": "Mile 2"})
    assert search.status_code == 200
    reserve = client.post(reverse("bookings:reserve", args=[departure.pk]))
    assert reserve.status_code == 302
    booking = Booking.objects.get(passenger=passenger, departure=departure)
    assert booking.status == BookingStatus.HELD
    page = client.get(reverse("bookings:detail", args=[booking.pk]))
    assert page.status_code == 200
    assert b"Your private code" in page.content
    cancel = client.post(reverse("bookings:cancel", args=[booking.pk]))
    assert cancel.status_code == 302
    booking.refresh_from_db()
    assert booking.status == BookingStatus.CANCELLED


def test_driver_and_support_actions_are_reachable(client, driver, departure):
    client.force_login(driver)
    for name in ("vehicles:list", "vehicles:create", "vehicles:profile",
                 "departures:dashboard", "departures:create",
                 "verification:status", "safety:report", "safety:route_update_new"):
        page = client.get(reverse(name))
        assert page.status_code == 200, (name, page.status_code)
    manage = client.get(reverse("departures:manage", args=[departure.pk]))
    assert manage.status_code == 200
    assert b"Private passenger roster" in manage.content
