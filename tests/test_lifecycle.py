"""Departure lifecycle tests (BE-09)."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.exceptions import StateError
from apps.departures.models import DepartureStatus
from apps.departures.services import (
    cancel_departure,
    close_boarding,
    create_departure,
    mark_arrived,
    publish,
    start_trip,
)

pytestmark = pytest.mark.django_db


def test_publish_and_transitions(driver, vehicle, route):
    departure = create_departure(
        driver,
        vehicle=vehicle,
        route=route,
        scheduled_departure_at=timezone.now() + timedelta(hours=3),
    )
    assert departure.status == DepartureStatus.DRAFT
    assert departure.snapshot_capacity == vehicle.capacity

    departure = publish(departure, driver)
    assert departure.status == DepartureStatus.BOARDING_OPEN
    departure = close_boarding(departure, driver)
    assert departure.status == DepartureStatus.BOARDING_CLOSED
    departure = start_trip(departure, driver)
    assert departure.status == DepartureStatus.EN_ROUTE
    departure = mark_arrived(departure, driver)
    assert departure.status == DepartureStatus.ARRIVED


def test_create_departure_rejects_short_notice(driver, vehicle, route):
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        create_departure(
            driver,
            vehicle=vehicle,
            route=route,
            scheduled_departure_at=timezone.now() + timedelta(seconds=120),
        )


def test_cannot_start_trip_with_valid_hold(driver, passenger, departure):
    from apps.bookings.services import reserve

    reserve(passenger, departure)
    close_boarding(departure, driver)
    with pytest.raises(StateError):
        start_trip(departure, driver)


def test_cancel_departure_cancels_bookings(driver, passenger, departure):
    from apps.bookings.models import BookingStatus
    from apps.bookings.services import reserve

    booking, _ = reserve(passenger, departure)
    cancel_departure(departure, driver)
    departure.refresh_from_db()
    booking.refresh_from_db()
    assert departure.status == DepartureStatus.CANCELLED
    assert booking.status == BookingStatus.CANCELLED


def test_only_driver_can_create_for_own_vehicle(other_driver, vehicle, route):
    from django.core.exceptions import PermissionDenied

    with pytest.raises(PermissionDenied):
        create_departure(
            other_driver,
            vehicle=vehicle,
            route=route,
            scheduled_departure_at=timezone.now() + timedelta(hours=3),
        )
