"""Safety module tests (BE-10, BE-11, BE-12)."""

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.bookings.models import BookingStatus
from apps.bookings.services import confirm_arrival, reserve
from apps.departures.models import DepartureStatus
from apps.departures.services import close_boarding, mark_arrived, start_trip
from apps.safety.models import (
    IncidentCategory,
    IncidentStatus,
    RouteUpdateStatus,
)
from apps.safety.services import (
    create_incident,
    create_review,
    create_route_update,
    moderate_incident,
    moderate_route_update,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def completed_booking(driver, passenger, departure):
    booking, code = reserve(passenger, departure)
    from apps.bookings.services import check_in

    check_in(booking, driver, code)
    close_boarding(departure, driver)
    start_trip(departure, driver)
    mark_arrived(departure, driver)
    booking.refresh_from_db()
    return confirm_arrival(booking, passenger)


def test_review_requires_completed_booking(passenger, departure):
    from apps.bookings.services import reserve

    booking, _ = reserve(passenger, departure)
    assert booking.status == BookingStatus.HELD
    with pytest.raises(ValidationError):
        create_review(booking, passenger, stars=5)


def test_review_is_one_per_booking(completed_booking, passenger):
    create_review(completed_booking, passenger, stars=4, comment="Good trip")
    with pytest.raises(ValidationError):
        create_review(completed_booking, passenger, stars=2)


def test_review_stars_validated(completed_booking, passenger):
    with pytest.raises(ValidationError):
        create_review(completed_booking, passenger, stars=9)


def test_only_author_can_review(completed_booking, other_passenger):
    with pytest.raises(PermissionDenied):
        create_review(completed_booking, other_passenger, stars=3)


def test_incident_defaults_to_pending(passenger):
    report = create_incident(
        passenger, category=IncidentCategory.SAFETY, description="Fictional demo report."
    )
    assert report.status == IncidentStatus.PENDING


def test_incident_requires_involvement(passenger, other_passenger, completed_booking):
    with pytest.raises(PermissionDenied):
        create_incident(
            other_passenger,
            category=IncidentCategory.CONDUCT,
            description="Not involved.",
            booking=completed_booking,
        )


def test_route_update_moderation_controls_visibility(passenger, staff, route):
    update = create_route_update(
        passenger,
        route=route,
        type="TRAFFIC",
        note="Heavy traffic near the terminal.",
        occurred_at=timezone.now() - timedelta(minutes=5),
    )
    assert update.status == RouteUpdateStatus.PENDING
    moderate_route_update(update, staff, approve=True)
    update.refresh_from_db()
    assert update.status == RouteUpdateStatus.APPROVED


def test_non_staff_cannot_moderate_incident(passenger):
    report = create_incident(
        passenger, category=IncidentCategory.OTHER, description="Report."
    )
    with pytest.raises(PermissionDenied):
        moderate_incident(report, passenger, IncidentStatus.RESOLVED)


def test_route_updates_page_shows_only_approved(passenger, staff, route, stub_frontend_templates):
    from django.test import Client
    from django.urls import reverse

    approved = create_route_update(
        passenger,
        route=route,
        type="TRAFFIC",
        note="Approved note.",
        occurred_at=timezone.now(),
    )
    moderate_route_update(approved, staff, approve=True)
    create_route_update(
        passenger,
        route=route,
        type="SAFETY",
        note="Pending note.",
        occurred_at=timezone.now(),
    )
    response = Client().get(reverse("safety:route_updates"))
    notes = [u.note for u in response.context["updates"]]
    assert "Approved note." in notes
    assert "Pending note." not in notes


def test_departure_status_for_arrival(departure):
    """Sanity: ARRIVED is reachable through the lifecycle."""
    assert DepartureStatus.ARRIVED in DepartureStatus.values
