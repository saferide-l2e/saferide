"""Booking service contract tests (BE-05 to BE-08)."""

from datetime import timedelta

import pytest
from django.contrib.auth.hashers import check_password
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.bookings.models import BoardingCredential, Booking, BookingStatus, WaitlistStatus
from apps.bookings.services import (
    accept_offer,
    available_seats,
    cancel,
    check_in,
    confirm_arrival,
    join_waitlist,
    reconcile,
    reserve,
)
from apps.core.exceptions import CapacityError, DuplicateError, EligibilityError, SafeRideError
from apps.departures.models import Departure, DepartureStatus

pytestmark = pytest.mark.django_db


def _departure(driver, vehicle, route, status=DepartureStatus.BOARDING_OPEN, capacity=None):
    return Departure.objects.create(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=timezone.now() + timedelta(hours=2),
        snapshot_capacity=capacity or vehicle.capacity,
        status=status,
    )


def test_reserve_holds_exactly_600_seconds(passenger, departure):
    now = timezone.now()
    booking, code = reserve(passenger, departure, now)

    assert booking.status == BookingStatus.HELD
    assert (booking.expires_at - now) == timedelta(seconds=600)
    assert len(code) == 6 and code.isdigit()
    credential = BoardingCredential.objects.get(booking=booking)
    assert credential.code_hash != code
    assert check_password(code, credential.code_hash)
    assert available_seats(departure, now) == departure.snapshot_capacity - 1


def test_unverified_passenger_cannot_reserve(unverified_passenger, departure):
    with pytest.raises(EligibilityError):
        reserve(unverified_passenger, departure)


def test_departure_too_soon_is_rejected(passenger, driver, vehicle, route):
    soon = Departure.objects.create(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=timezone.now() + timedelta(seconds=300),
        snapshot_capacity=vehicle.capacity,
        status=DepartureStatus.BOARDING_OPEN,
    )
    with pytest.raises(SafeRideError):
        reserve(passenger, soon)


def test_duplicate_active_booking_is_rejected(passenger, departure):
    reserve(passenger, departure)
    with pytest.raises(DuplicateError):
        reserve(passenger, departure)


def test_last_seat_only_one_person_succeeds(passenger, other_passenger, driver, vehicle, route):
    one_seat = _departure(driver, vehicle, route, capacity=1)
    reserve(passenger, one_seat)
    with pytest.raises(CapacityError):
        reserve(other_passenger, one_seat)
    assert available_seats(one_seat) == 0


def test_expiry_frees_the_seat_even_without_cron(passenger, other_passenger, departure):
    start = timezone.now()
    booking, _ = reserve(passenger, departure, start)
    assert booking.expires_at == start + timedelta(seconds=600)

    later = start + timedelta(seconds=601)
    # A fresh reserve reconciles the expired hold under lock, then succeeds.
    new_booking, _ = reserve(other_passenger, departure, later)
    assert new_booking.status == BookingStatus.HELD
    booking.refresh_from_db()
    assert booking.status == BookingStatus.EXPIRED
    assert not booking.is_hold_valid


def test_reconcile_expires_stale_holds_and_offers(passenger, other_passenger, driver, vehicle, route):
    one_seat = _departure(driver, vehicle, route, capacity=1)
    start = timezone.now()
    reserve(passenger, one_seat, start)
    join_waitlist(other_passenger, one_seat, start + timedelta(seconds=1))

    reconcile(one_seat, start + timedelta(seconds=601))
    assert Booking.objects.get(passenger=passenger).status == BookingStatus.EXPIRED


def test_waitlist_fifo_and_offer_window(passenger, other_passenger, driver, vehicle, route):
    one_seat = _departure(driver, vehicle, route, capacity=1)
    start = timezone.now()
    booking, _ = reserve(passenger, one_seat, start)

    from apps.accounts.models import Role, User

    third = User.objects.create_user(
        "third@example.test", "x-strong-123", display_name="Tia Third", role=Role.PASSENGER
    )
    from apps.verification.models import Verification, VerificationStatus

    Verification.objects.create(user=third, status=VerificationStatus.VERIFIED)

    entry_b = join_waitlist(other_passenger, one_seat, start + timedelta(seconds=1))
    entry_c = join_waitlist(third, one_seat, start + timedelta(seconds=2))

    cancel(booking, passenger, start + timedelta(seconds=10))
    entry_b.refresh_from_db()
    assert entry_b.status == WaitlistStatus.OFFERED
    assert entry_b.offer_expires_at == start + timedelta(seconds=10) + timedelta(seconds=120)

    # Offer expires and the queue advances to the next eligible person.
    reconcile(one_seat, start + timedelta(seconds=131))
    entry_b.refresh_from_db()
    entry_c.refresh_from_db()
    assert entry_b.status == WaitlistStatus.EXPIRED
    assert entry_c.status == WaitlistStatus.OFFERED


def test_outstanding_offer_consumes_a_slot(passenger, other_passenger, driver, vehicle, route):
    one_seat = _departure(driver, vehicle, route, capacity=1)
    start = timezone.now()
    booking, _ = reserve(passenger, one_seat, start)
    join_waitlist(other_passenger, one_seat, start + timedelta(seconds=1))
    cancel(booking, passenger, start + timedelta(seconds=10))
    assert available_seats(one_seat, start + timedelta(seconds=10)) == 0


def test_accept_offer_creates_fresh_hold(passenger, other_passenger, driver, vehicle, route):
    one_seat = _departure(driver, vehicle, route, capacity=1)
    start = timezone.now()
    booking, _ = reserve(passenger, one_seat, start)
    entry = join_waitlist(other_passenger, one_seat, start + timedelta(seconds=1))
    cancel(booking, passenger, start + timedelta(seconds=10))
    entry.refresh_from_db()

    accepted, code = accept_offer(entry, other_passenger, start + timedelta(seconds=20))
    assert accepted.status == BookingStatus.HELD
    assert accepted.expires_at == start + timedelta(seconds=20) + timedelta(seconds=600)
    entry.refresh_from_db()
    assert entry.status == WaitlistStatus.ACCEPTED
    assert len(code) == 6


def test_accept_offer_wrong_passenger_denied(passenger, other_passenger, driver, vehicle, route):
    one_seat = _departure(driver, vehicle, route, capacity=1)
    start = timezone.now()
    booking, _ = reserve(passenger, one_seat, start)
    entry = join_waitlist(other_passenger, one_seat, start + timedelta(seconds=1))
    cancel(booking, passenger, start + timedelta(seconds=10))
    entry.refresh_from_db()
    from apps.accounts.models import Role, User
    from apps.verification.models import Verification, VerificationStatus

    stranger = User.objects.create_user(
        "stranger@example.test", "y-strong-123", display_name="Sara Stranger", role=Role.PASSENGER
    )
    Verification.objects.create(user=stranger, status=VerificationStatus.VERIFIED)
    with pytest.raises(PermissionDenied):
        accept_offer(entry, stranger)


def test_check_in_consumes_single_use_code(driver, passenger, other_driver, departure):
    start = timezone.now()
    booking, code = reserve(passenger, departure, start)

    with pytest.raises(PermissionDenied):
        check_in(booking, other_driver, code, start + timedelta(seconds=5))

    with pytest.raises(SafeRideError):
        check_in(booking, driver, "000000", start + timedelta(seconds=5))

    boarded = check_in(booking, driver, code, start + timedelta(seconds=5))
    assert boarded.status == BookingStatus.BOARDED
    assert boarded.checked_in_at == start + timedelta(seconds=5)

    # Code is single-use: a second attempt fails.
    with pytest.raises(SafeRideError):
        check_in(booking, driver, code, start + timedelta(seconds=6))


def test_check_in_after_expiry_fails(driver, passenger, departure):
    start = timezone.now()
    booking, code = reserve(passenger, departure, start)
    with pytest.raises(SafeRideError):
        check_in(booking, driver, code, start + timedelta(seconds=601))
    # The failed attempt rolled its transaction back; an explicit reconcile
    # (as the periodic command does) marks the hold expired.
    reconcile(departure, start + timedelta(seconds=602))
    booking.refresh_from_db()
    assert booking.status == BookingStatus.EXPIRED
    assert not booking.is_hold_valid


def test_board_and_arrival_flow(driver, passenger, departure):
    from apps.departures.services import close_boarding, mark_arrived, start_trip

    start = timezone.now()
    booking, code = reserve(passenger, departure, start)
    check_in(booking, driver, code, start)

    close_boarding(departure, driver)
    start_trip(departure, driver)
    mark_arrived(departure, driver)

    booking.refresh_from_db()
    assert booking.driver_arrived_at is not None

    completed = confirm_arrival(booking, passenger, start + timedelta(seconds=30))
    assert completed.status == BookingStatus.COMPLETED
    assert completed.passenger_confirmed_at == start + timedelta(seconds=30)
