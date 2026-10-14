from datetime import UTC

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.departures.models import Departure
from apps.vehicles.models import Vehicle

ALLOWED_TRANSITIONS = {
    Departure.Status.DRAFT: {Departure.Status.BOARDING_OPEN, Departure.Status.CANCELLED},
    Departure.Status.BOARDING_OPEN: {
        Departure.Status.BOARDING_CLOSED,
        Departure.Status.CANCELLED,
    },
    Departure.Status.BOARDING_CLOSED: {
        Departure.Status.EN_ROUTE,
        Departure.Status.CANCELLED,
    },
    Departure.Status.EN_ROUTE: {Departure.Status.ARRIVED},
    Departure.Status.ARRIVED: set(),
    Departure.Status.CANCELLED: set(),
}


def _ensure_vehicle_owner(departure):
    if departure.vehicle.driver_id != departure.driver_id:
        raise ValidationError("The vehicle must belong to the departure's driver.")


def _ensure_publishable(departure):
    _ensure_vehicle_owner(departure)
    if departure.vehicle.approval_status != Vehicle.ApprovalStatus.APPROVED:
        raise ValidationError("Only an approved vehicle can be published.")


def create_departure(*, route, driver, vehicle, scheduled_departure_at, walk_in_count=0):
    """Create a draft and snapshot vehicle capacity at creation time."""
    if vehicle.driver_id != driver.id:
        raise ValidationError("The vehicle must belong to the departure's driver.")
    if walk_in_count < 0:
        raise ValidationError({"walk_in_count": "Walk-in count cannot be negative."})
    if not timezone.is_aware(scheduled_departure_at):
        raise ValidationError(
            {"scheduled_departure_at": "A timezone-aware departure time is required."}
        )

    departure = Departure.objects.create(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=scheduled_departure_at.astimezone(UTC),
        capacity_snapshot=vehicle.seat_capacity,
        walk_in_count=walk_in_count,
    )
    return departure


@transaction.atomic
def transition_departure(departure, new_status):
    """Apply one valid lifecycle transition, checking publication guards."""
    try:
        target = Departure.Status(new_status)
    except ValueError as exc:
        raise ValidationError({"status": "Unknown departure status."}) from exc

    current = (
        Departure.objects.select_for_update()
        .select_related("driver", "vehicle")
        .get(pk=departure.pk)
    )
    if target not in ALLOWED_TRANSITIONS[current.status]:
        raise ValidationError(f"Cannot move a departure from {current.status} to {target}.")
    if target == Departure.Status.BOARDING_OPEN:
        _ensure_publishable(current)
    else:
        _ensure_vehicle_owner(current)

    current.status = target
    current.save(update_fields=["status"])
    return current
