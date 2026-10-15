"""Vehicle registration and admin approval (BE-03)."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import Role
from apps.audit.services import record

from .models import ApprovalStatus, DriverProfile, Vehicle, normalize_plate


def get_or_create_driver_profile(user):
    if user.role != Role.DRIVER:
        raise ValidationError("Only driver accounts have a driver profile.")
    profile, _ = DriverProfile.objects.get_or_create(user=user)
    return profile


@transaction.atomic
def register_vehicle(user, *, plate_display, vehicle_type, capacity):
    """An approved driver submits a vehicle for listing approval."""
    if user.role != Role.DRIVER:
        raise PermissionDenied("Only drivers can register vehicles.")
    if not user.is_verified:
        raise PermissionDenied("Your driver verification must be approved first.")

    plate_display = (plate_display or "").strip().upper()
    normalized = normalize_plate(plate_display)
    if not normalized:
        raise ValidationError("Enter a valid number plate.")
    if Vehicle.objects.filter(plate_normalized=normalized).exists():
        raise ValidationError("That number plate is already registered.")

    try:
        capacity = int(capacity)
    except (TypeError, ValueError):
        raise ValidationError("Capacity must be a whole number.") from None
    if capacity < 1:
        raise ValidationError("Capacity must be at least 1.")

    profile = get_or_create_driver_profile(user)
    try:
        vehicle = Vehicle.objects.create(
            driver=profile,
            plate_display=plate_display,
            plate_normalized=normalized,
            vehicle_type=(vehicle_type or "").strip()[:40],
            capacity=capacity,
            approval_status=ApprovalStatus.PENDING,
        )
    except IntegrityError as exc:
        raise ValidationError("That number plate is already registered.") from exc
    record(user, "vehicle.registered", vehicle, {"plate": vehicle.plate_display})
    return vehicle


def approve_vehicle(vehicle, actor):
    if not (actor and actor.is_staff and actor.is_active):
        raise PermissionDenied("Only authorized staff may approve vehicles.")
    vehicle.approval_status = ApprovalStatus.APPROVED
    vehicle.save(update_fields=["approval_status"])
    record(actor, "vehicle.approved", vehicle, {"plate": vehicle.plate_display})
    return vehicle


def reject_vehicle(vehicle, actor):
    if not (actor and actor.is_staff and actor.is_active):
        raise PermissionDenied("Only authorized staff may reject vehicles.")
    vehicle.approval_status = ApprovalStatus.REJECTED
    vehicle.save(update_fields=["approval_status"])
    record(actor, "vehicle.rejected", vehicle, {"plate": vehicle.plate_display})
    return vehicle
