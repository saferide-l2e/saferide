"""Booking service contract (BE-05 to BE-08, BE-14).

Public operations:
    reserve(passenger, departure, now_utc)
    cancel(booking, actor, now_utc)
    join_waitlist(passenger, departure, now_utc)
    accept_offer(entry, passenger, now_utc)
    check_in(booking, driver, code, now_utc)
    confirm_arrival(booking, passenger, now_utc)
    reconcile(departure, now_utc)

Boarding-credential and waitlist helpers (database contract, DB-04/DB-05):
    hash_boarding_code(raw_code)
    verify_boarding_code(raw_code, code_digest)
    issue_boarding_credential(booking, raw_code=None)
    offer_next_waitlist_entry(departure, now=None, offer_window=OFFER_WINDOW)

Every inventory-changing operation locks the departure row, reconciles expired
holds/offers, re-checks eligibility and capacity, then writes the change and its
audit event inside one transaction. The 600-second hold and 120-second offer are
measured from server time; browser timers never decide correctness.
"""

import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Role
from apps.audit.services import record
from apps.core.exceptions import (
    CapacityError,
    CodeError,
    DuplicateError,
    EligibilityError,
    ExpiredError,
    StateError,
)
from apps.departures.models import Departure, DepartureStatus
from apps.verification.services import is_verified

from .models import BoardingCredential, Booking, BookingStatus, WaitlistEntry, WaitlistStatus

ACTIVE_BOOKING_STATUSES = (BookingStatus.HELD, BookingStatus.BOARDED)
OFFER_WINDOW = timedelta(seconds=settings.SAFERIDE_OFFER_SECONDS)


def _now(value=None):
    moment = value or timezone.now()
    if timezone.is_naive(moment):
        moment = timezone.make_aware(moment, datetime.timezone.utc)
    return moment


def _hold_duration():
    return timedelta(seconds=settings.SAFERIDE_HOLD_SECONDS)


def _offer_duration():
    return timedelta(seconds=settings.SAFERIDE_OFFER_SECONDS)


# --------------------------------------------------------------------------- #
# Boarding credentials
# --------------------------------------------------------------------------- #
def hash_boarding_code(raw_code):
    """Return a salted Django password hash; callers must never log the raw code."""
    return make_password(raw_code)


def verify_boarding_code(raw_code, code_digest):
    """Constant-time verification helper for backend boarding flows."""
    return check_password(raw_code, code_digest)


def issue_boarding_credential(booking, raw_code=None):
    """Create one credential for ``booking`` and return ``(credential, raw_code)``.

    When ``raw_code`` is omitted a random URL-safe code is generated. Only the
    salted digest is persisted; the raw code is returned once to the caller and
    must not be logged or stored.
    """
    raw_code = raw_code or secrets.token_urlsafe(16)
    credential = BoardingCredential.objects.create(
        booking=booking,
        code_digest=hash_boarding_code(raw_code),
    )
    return credential, raw_code


@transaction.atomic
def offer_next_waitlist_entry(departure, *, now=None, offer_window=OFFER_WINDOW):
    """Offer one released seat to the next FIFO entry.

    Call inside the departure inventory transaction after a seat is released.
    The caller must count unexpired OFFERED entries as occupied inventory.
    """
    now = now or timezone.now()
    if not timezone.is_aware(now):
        raise ValidationError("Offer timestamps must be timezone-aware.")
    if offer_window <= timedelta(0):
        raise ValidationError("Offer duration must be positive.")

    entry = (
        WaitlistEntry.objects.select_for_update(skip_locked=True)
        .filter(departure=departure, status=WaitlistStatus.WAITING)
        .fifo()
        .first()
    )
    if entry is None:
        return None

    entry.status = WaitlistStatus.OFFERED
    entry.offered_at = now
    entry.offer_expires_at = now + offer_window
    entry.save(update_fields=["status", "offered_at", "offer_expires_at"])
    return entry


# --------------------------------------------------------------------------- #
# Eligibility
# --------------------------------------------------------------------------- #
def passenger_eligible(user):
    return bool(
        user
        and user.is_active
        and user.role == Role.PASSENGER
        and is_verified(user)
    )


def _require_passenger_eligible(user):
    if not user or not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Sign in first.")
    if user.role != Role.PASSENGER:
        raise EligibilityError("Only passenger accounts can reserve seats.")
    if not user.is_active:
        raise EligibilityError("This account is inactive.")
    if not is_verified(user):
        raise EligibilityError("Your account must be approved before booking.")


# --------------------------------------------------------------------------- #
# Capacity accounting
# --------------------------------------------------------------------------- #
def held_count(departure, now):
    return Booking.objects.filter(
        departure=departure, status=BookingStatus.HELD, expires_at__gt=now
    ).count()


def boarded_count(departure):
    return Booking.objects.filter(departure=departure, status=BookingStatus.BOARDED).count()


def outstanding_offers(departure, now):
    return WaitlistEntry.objects.filter(
        departure=departure, status=WaitlistStatus.OFFERED, offer_expires_at__gt=now
    ).count()


def available_seats(departure, now_utc=None):
    """Read-only seat count for display. Reconciliation happens under lock."""
    now = _now(now_utc)
    used = (
        held_count(departure, now)
        + boarded_count(departure)
        + outstanding_offers(departure, now)
        + departure.walk_in_count
    )
    return max(departure.snapshot_capacity - used, 0)


# --------------------------------------------------------------------------- #
# Reconciliation
# --------------------------------------------------------------------------- #
def _expire_holds(departure, now):
    stale = Booking.objects.select_for_update().filter(
        departure=departure, status=BookingStatus.HELD, expires_at__lte=now
    )
    for booking in stale:
        booking.status = BookingStatus.EXPIRED
        booking.save(update_fields=["status"])
        BoardingCredential.objects.filter(
            booking=booking, consumed_at__isnull=True, revoked_at__isnull=True
        ).update(revoked_at=now)
        record(None, "booking.expired", booking, {"departure": str(departure.id)})


def _expire_offers(departure, now):
    stale = WaitlistEntry.objects.select_for_update().filter(
        departure=departure, status=WaitlistStatus.OFFERED, offer_expires_at__lte=now
    )
    for entry in stale:
        entry.status = WaitlistStatus.EXPIRED
        entry.save(update_fields=["status"])
        record(None, "waitlist.offer_expired", entry, {"departure": str(departure.id)})


def _advance_offers(departure, now):
    """Offer newly free seats to the FIFO queue, oldest join first."""
    free = available_seats(departure, now)
    if free <= 0:
        return
    waiting = WaitlistEntry.objects.select_for_update().filter(
        departure=departure, status=WaitlistStatus.WAITING
    ).order_by("joined_at", "id")
    for entry in waiting:
        if free <= 0:
            break
        if not passenger_eligible(entry.passenger):
            entry.status = WaitlistStatus.INELIGIBLE
            entry.save(update_fields=["status"])
            continue
        entry.status = WaitlistStatus.OFFERED
        entry.offered_at = now
        entry.offer_expires_at = now + _offer_duration()
        entry.save(update_fields=["status", "offered_at", "offer_expires_at"])
        record(None, "waitlist.offered", entry, {"departure": str(departure.id)})
        free -= 1


def _reconcile_locked(departure, now):
    _expire_holds(departure, now)
    _expire_offers(departure, now)
    _advance_offers(departure, now)


@transaction.atomic
def reconcile(departure, now_utc=None):
    """Expire stale holds/offers and advance the waitlist under row lock."""
    now = _now(now_utc)
    locked = Departure.objects.select_for_update().get(pk=departure.pk)
    _reconcile_locked(locked, now)
    return locked


# --------------------------------------------------------------------------- #
# Guards
# --------------------------------------------------------------------------- #
def _require_departure_bookable(passenger, departure, now):
    _require_passenger_eligible(passenger)
    if departure.status == DepartureStatus.CANCELLED:
        raise StateError("This trip has been cancelled.")
    if departure.status != DepartureStatus.BOARDING_OPEN:
        raise StateError("This trip is not open for booking.")
    if departure.scheduled_departure_at < now + _hold_duration():
        raise StateError("This trip departs too soon to hold a seat.")


def _require_no_duplicate(passenger, departure):
    if Booking.objects.filter(
        departure=departure, passenger=passenger, status__in=ACTIVE_BOOKING_STATUSES
    ).exists():
        raise DuplicateError("You already have an active seat on this trip.")


def _require_no_overlap(passenger, departure, now):
    other = (
        Booking.objects.filter(passenger=passenger, status__in=ACTIVE_BOOKING_STATUSES)
        .exclude(departure=departure)
        .filter(Q(status=BookingStatus.BOARDED) | Q(status=BookingStatus.HELD, expires_at__gt=now))
        .exclude(departure__status__in=[DepartureStatus.ARRIVED, DepartureStatus.CANCELLED])
    )
    if other.exists():
        raise DuplicateError("You already hold a seat on another trip.")


def _issue_credential(booking):
    """Issue the six-digit boarding code the passenger sees for this hold."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    issue_boarding_credential(booking, raw_code=code)
    return code


# --------------------------------------------------------------------------- #
# Public operations
# --------------------------------------------------------------------------- #
def reserve(passenger, departure, now_utc=None):
    """Hold one seat for exactly 600 seconds. Returns ``(booking, boarding_code)``."""
    now = _now(now_utc)
    with transaction.atomic():
        locked = Departure.objects.select_for_update().get(pk=departure.pk)
        _reconcile_locked(locked, now)
        _require_departure_bookable(passenger, locked, now)
        if available_seats(locked, now) <= 0:
            raise CapacityError("This bus is full. You can join the waitlist.")
        _require_no_duplicate(passenger, locked)
        _require_no_overlap(passenger, locked, now)

        booking = Booking.objects.create(
            departure=locked,
            passenger=passenger,
            status=BookingStatus.HELD,
            expires_at=now + _hold_duration(),
        )
        code = _issue_credential(booking)
        record(passenger, "booking.held", booking, {"departure": str(locked.id)})
    return booking, code


def cancel(booking, actor, now_utc=None):
    """Cancel a hold/boarding and release the seat to the waitlist."""
    now = _now(now_utc)
    with transaction.atomic():
        locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
        departure = Departure.objects.select_for_update().get(pk=locked_booking.departure_id)
        _reconcile_locked(departure, now)
        locked_booking.refresh_from_db()

        is_owner = getattr(actor, "is_authenticated", False) and locked_booking.passenger_id == actor.id
        is_driver = getattr(actor, "is_authenticated", False) and departure.driver_id == actor.id
        is_staff = bool(actor and getattr(actor, "is_staff", False))
        if not (is_owner or is_driver or is_staff):
            raise PermissionDenied("You cannot cancel this reservation.")

        if locked_booking.status not in ACTIVE_BOOKING_STATUSES:
            raise StateError("Only an active reservation can be cancelled.")

        locked_booking.status = BookingStatus.CANCELLED
        locked_booking.save(update_fields=["status"])
        BoardingCredential.objects.filter(
            booking=locked_booking, consumed_at__isnull=True, revoked_at__isnull=True
        ).update(revoked_at=now)
        record(actor, "booking.cancelled", locked_booking, {"departure": str(departure.id)})
        _advance_offers(departure, now)
    return locked_booking


def join_waitlist(passenger, departure, now_utc=None):
    """Join the FIFO waitlist for a sold-out trip."""
    now = _now(now_utc)
    with transaction.atomic():
        locked = Departure.objects.select_for_update().get(pk=departure.pk)
        _reconcile_locked(locked, now)
        _require_passenger_eligible(passenger)
        if locked.status != DepartureStatus.BOARDING_OPEN:
            raise StateError("This trip is not open for waitlist entries.")
        if available_seats(locked, now) > 0:
            raise StateError("Seats are still available — reserve one instead.")
        _require_no_duplicate(passenger, locked)
        if WaitlistEntry.objects.filter(
            departure=locked,
            passenger=passenger,
            status__in=[WaitlistStatus.WAITING, WaitlistStatus.OFFERED],
        ).exists():
            raise DuplicateError("You are already on this waitlist.")

        entry = WaitlistEntry.objects.create(
            departure=locked, passenger=passenger, status=WaitlistStatus.WAITING
        )
        record(passenger, "waitlist.joined", entry, {"departure": str(locked.id)})
    return entry


def accept_offer(entry, passenger, now_utc=None):
    """Accept a seat offer, converting it into a fresh 600-second hold."""
    now = _now(now_utc)
    with transaction.atomic():
        departure = Departure.objects.select_for_update().get(pk=entry.departure_id)
        _reconcile_locked(departure, now)
        locked_entry = WaitlistEntry.objects.select_for_update().get(pk=entry.pk)

        if not getattr(passenger, "is_authenticated", False) or locked_entry.passenger_id != passenger.id:
            raise PermissionDenied("This offer belongs to another passenger.")
        if locked_entry.status != WaitlistStatus.OFFERED:
            raise StateError("This offer is no longer available.")
        if locked_entry.offer_expires_at is None or locked_entry.offer_expires_at <= now:
            raise ExpiredError("This offer has expired.")

        booking = Booking.objects.create(
            departure=departure,
            passenger=passenger,
            status=BookingStatus.HELD,
            expires_at=now + _hold_duration(),
        )
        code = _issue_credential(booking)
        # The database requires ACCEPTED entries to name the booking they took,
        # so both columns are written together.
        locked_entry.status = WaitlistStatus.ACCEPTED
        locked_entry.accepted_booking = booking
        locked_entry.save(update_fields=["status", "accepted_booking"])
        record(passenger, "waitlist.accepted", locked_entry, {"departure": str(departure.id)})
    return booking, code


def check_in(booking, driver, code, now_utc=None):
    """Assigned driver validates the single-use code and boards the passenger."""
    now = _now(now_utc)
    with transaction.atomic():
        locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
        departure = Departure.objects.select_for_update().get(pk=locked_booking.departure_id)
        _reconcile_locked(departure, now)
        locked_booking.refresh_from_db()

        if not driver or not getattr(driver, "is_authenticated", False) or departure.driver_id != driver.id:
            raise PermissionDenied("Only the assigned driver can check in passengers.")
        if locked_booking.status != BookingStatus.HELD:
            raise StateError("This reservation is not awaiting boarding.")
        if locked_booking.expires_at is None or locked_booking.expires_at <= now:
            raise ExpiredError("This hold has expired and cannot be boarded.")

        credential = getattr(locked_booking, "boarding_credential", None)
        if credential is None or not credential.is_usable:
            raise CodeError("No valid boarding code for this reservation.")
        if not verify_boarding_code((code or "").strip(), credential.code_digest):
            raise CodeError("The boarding code is incorrect.")

        locked_booking.status = BookingStatus.BOARDED
        locked_booking.checked_in_at = now
        locked_booking.save(update_fields=["status", "checked_in_at"])
        credential.consumed_at = now
        credential.save(update_fields=["consumed_at"])
        record(driver, "booking.boarded", locked_booking, {"departure": str(departure.id)})
    return locked_booking


def confirm_arrival(booking, passenger, now_utc=None):
    """Passenger independently confirms arrival and completes the ride."""
    now = _now(now_utc)
    with transaction.atomic():
        locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
        departure = Departure.objects.select_for_update().get(pk=locked_booking.departure_id)

        is_owner = getattr(passenger, "is_authenticated", False) and locked_booking.passenger_id == passenger.id
        is_staff = bool(passenger and getattr(passenger, "is_staff", False))
        if not (is_owner or is_staff):
            raise PermissionDenied("You cannot confirm this booking.")

        if locked_booking.status == BookingStatus.COMPLETED:
            raise StateError("Arrival has already been confirmed.")
        if departure.status != DepartureStatus.ARRIVED:
            raise StateError("The driver has not marked this trip as arrived.")
        if locked_booking.status not in (BookingStatus.BOARDED, BookingStatus.DISPUTED):
            raise StateError("Only a boarded passenger can confirm arrival.")

        locked_booking.passenger_confirmed_at = now
        locked_booking.status = BookingStatus.COMPLETED
        locked_booking.save(update_fields=["passenger_confirmed_at", "status"])
        record(passenger, "booking.completed", locked_booking, {"departure": str(departure.id)})
    return locked_booking


__all__ = [
    "OFFER_WINDOW",
    "Booking",
    "BookingStatus",
    "WaitlistEntry",
    "WaitlistStatus",
    "accept_offer",
    "available_seats",
    "cancel",
    "check_in",
    "confirm_arrival",
    "hash_boarding_code",
    "issue_boarding_credential",
    "join_waitlist",
    "offer_next_waitlist_entry",
    "passenger_eligible",
    "reconcile",
    "reserve",
    "verify_boarding_code",
]
