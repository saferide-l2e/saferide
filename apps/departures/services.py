"""Departure publishing and lifecycle transitions (BE-03, BE-09).

Only the assigned driver (or staff) may advance a departure. Transitions are
guarded so a bus cannot enter EN_ROUTE while valid seat holds are outstanding,
and inventory is reconciled under row lock whenever it changes.
"""

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role
from apps.audit.services import record
from apps.core.exceptions import StateError

from .models import Departure, DepartureStatus


def _require_owner(departure, actor):
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Sign in first.")
    if departure.driver_id != actor.id and not actor.is_staff:
        raise PermissionDenied("Only the assigned driver may manage this departure.")


def _require_driver_eligible(user):
    if user.role != Role.DRIVER:
        raise PermissionDenied("Only drivers can publish departures.")
    if not user.is_verified:
        raise PermissionDenied("Your driver verification must be approved first.")


@transaction.atomic
def create_departure(user, *, vehicle, route, scheduled_departure_at):
    """Create a DRAFT departure with a capacity snapshot.

    Rejects departures that leave less than the hold window, because no seat may
    be promised inside the 600-second boarding window.
    """
    _require_driver_eligible(user)
    if vehicle.driver.user_id != user.id:
        raise PermissionDenied("You can only publish your own approved vehicle.")
    if vehicle.approval_status != "APPROVED":
        raise ValidationError("Your vehicle must be approved before publishing.")
    if not route.is_active:
        raise ValidationError("That route is not active.")

    now = timezone.now()
    if scheduled_departure_at is None:
        raise ValidationError("Choose a departure time.")
    if scheduled_departure_at <= now + timezone.timedelta(seconds=settings.SAFERIDE_HOLD_SECONDS):
        raise ValidationError(
            "Departure must be at least 10 minutes away so a hold can be honoured."
        )

    departure = Departure.objects.create(
        route=route,
        driver=user,
        vehicle=vehicle,
        scheduled_departure_at=scheduled_departure_at,
        snapshot_capacity=vehicle.capacity,
        status=DepartureStatus.DRAFT,
    )
    record(user, "departure.created", departure, {"route": str(route.id), "capacity": vehicle.capacity})
    return departure


@transaction.atomic
def publish(departure, actor):
    departure = Departure.objects.select_for_update().get(pk=departure.pk)
    _require_owner(departure, actor)
    if not departure.can_transition_to(DepartureStatus.BOARDING_OPEN):
        raise StateError("This departure cannot be opened for boarding now.")
    departure.status = DepartureStatus.BOARDING_OPEN
    departure.save(update_fields=["status", "updated_at"])
    record(actor, "departure.published", departure)
    return departure


@transaction.atomic
def close_boarding(departure, actor):
    from apps.bookings.services import reconcile

    departure = Departure.objects.select_for_update().get(pk=departure.pk)
    _require_owner(departure, actor)
    if not departure.can_transition_to(DepartureStatus.BOARDING_CLOSED):
        raise StateError("Boarding cannot be closed from the current status.")
    reconcile(departure, timezone.now())
    departure.status = DepartureStatus.BOARDING_CLOSED
    departure.save(update_fields=["status", "updated_at"])
    record(actor, "departure.boarding_closed", departure)
    return departure


@transaction.atomic
def start_trip(departure, actor):
    """Advance to EN_ROUTE. Blocked while valid holds remain."""
    from apps.bookings.models import Booking, BookingStatus
    from apps.bookings.services import reconcile

    departure = Departure.objects.select_for_update().get(pk=departure.pk)
    _require_owner(departure, actor)
    if not departure.can_transition_to(DepartureStatus.EN_ROUTE):
        raise StateError("The trip cannot start from the current status.")

    now = timezone.now()
    reconcile(departure, now)
    if Booking.objects.filter(
        departure=departure, status=BookingStatus.HELD, expires_at__gt=now
    ).exists():
        raise StateError("Wait for outstanding seat holds to resolve before departing.")

    departure.status = DepartureStatus.EN_ROUTE
    departure.save(update_fields=["status", "updated_at"])
    record(actor, "departure.started", departure)
    return departure


@transaction.atomic
def mark_arrived(departure, actor):
    from apps.bookings.models import Booking, BookingStatus

    departure = Departure.objects.select_for_update().get(pk=departure.pk)
    _require_owner(departure, actor)
    if not departure.can_transition_to(DepartureStatus.ARRIVED):
        raise StateError("Arrival can only be recorded once the trip is underway.")

    now = timezone.now()
    departure.status = DepartureStatus.ARRIVED
    departure.save(update_fields=["status", "updated_at"])
    Booking.objects.filter(departure=departure, status=BookingStatus.BOARDED).update(
        driver_arrived_at=now
    )
    record(actor, "departure.arrived", departure)
    return departure


@transaction.atomic
def cancel_departure(departure, actor):
    from apps.bookings.models import Booking, BookingStatus, WaitlistEntry, WaitlistStatus

    departure = Departure.objects.select_for_update().get(pk=departure.pk)
    _require_owner(departure, actor)
    if departure.status == DepartureStatus.ARRIVED:
        raise StateError("An arrived trip cannot be cancelled.")
    if departure.status == DepartureStatus.CANCELLED:
        raise StateError("This departure is already cancelled.")

    departure.status = DepartureStatus.CANCELLED
    departure.save(update_fields=["status", "updated_at"])
    Booking.objects.filter(
        departure=departure, status__in=[BookingStatus.HELD, BookingStatus.BOARDED]
    ).update(status=BookingStatus.CANCELLED)
    WaitlistEntry.objects.filter(
        departure=departure, status__in=[WaitlistStatus.WAITING, WaitlistStatus.OFFERED]
    ).update(status=WaitlistStatus.CANCELLED, offer_expires_at=None)
    record(actor, "departure.cancelled", departure)
    return departure


TRANSITIONS = {
    "publish": publish,
    "close_boarding": close_boarding,
    "start_trip": start_trip,
    "mark_arrived": mark_arrived,
    "cancel": cancel_departure,
}


def apply_transition(departure, actor, action):
    handler = TRANSITIONS.get(action)
    if handler is None:
        raise StateError("Unknown departure action.")
    return handler(departure, actor)


__all__ = [
    "Departure",
    "DepartureStatus",
    "apply_transition",
    "cancel_departure",
    "close_boarding",
    "create_departure",
    "mark_arrived",
    "publish",
    "start_trip",
]
