"""Timed onboarding approvals. Staff decisions and private reports are untouched.

Run from the durable review worker, never from a browser timer or a GET request.
Only submitted PENDING records at least five seconds old are eligible. Audit
records explicitly identify automation; this is not identity or safety screening.
"""
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role
from apps.audit.services import record
from apps.safety.models import RouteUpdate, RouteUpdateStatus
from apps.vehicles.models import ApprovalStatus, DriverProfile, Vehicle
from apps.verification.models import Verification, VerificationStatus

DELAY_SECONDS = 5
BATCH_SIZE = 100


def process_due_reviews(*, now=None):
    counts = {"accounts": 0, "drivers": 0, "vehicles": 0, "route_updates": 0}
    if not settings.SAFERIDE_AUTO_APPROVAL:
        return counts
    now = now or timezone.now()
    cutoff = now - timedelta(seconds=DELAY_SECONDS)
    metadata = {"automatic": True, "delay_seconds": DELAY_SECONDS}
    # Each queue has a bounded transaction. Multiple workers safely skip rows
    # already being processed. A restart picks up the same database timestamps.
    with transaction.atomic():
        accounts = Verification.objects.select_for_update(skip_locked=True, of=("self",)).filter(
            status=VerificationStatus.PENDING, submitted_at__lte=cutoff, user__is_active=True,
        ).order_by("submitted_at")[:BATCH_SIZE]
        for review in accounts:
            review.status = VerificationStatus.VERIFIED
            review.reviewed_by = None
            review.reviewed_at = now
            review.note = "Automatic account access approval; no identity, licence or background check."
            review.save(update_fields=["status", "reviewed_by", "reviewed_at", "note"])
            record(None, "verification.verified", review, metadata)
            counts["accounts"] += 1
    eligible_driver = {
        "user__is_active": True, "user__role": Role.DRIVER,
        "user__verification__status": VerificationStatus.VERIFIED,
    }
    with transaction.atomic():
        drivers = DriverProfile.objects.select_for_update(skip_locked=True, of=("self",)).filter(
            licence_review_status=ApprovalStatus.PENDING, created_at__lte=cutoff, **eligible_driver,
        ).order_by("created_at")[:BATCH_SIZE]
        for profile in drivers:
            profile.licence_review_status = ApprovalStatus.APPROVED
            profile.save(update_fields=["licence_review_status"])
            record(None, "driver_profile.approved", profile, metadata)
            counts["drivers"] += 1
    with transaction.atomic():
        vehicles = Vehicle.objects.select_for_update(skip_locked=True, of=("self",)).filter(
            approval_status=ApprovalStatus.PENDING, created_at__lte=cutoff,
            driver__licence_review_status=ApprovalStatus.APPROVED,
            **{f"driver__{key}": value for key, value in eligible_driver.items()},
        ).order_by("created_at")[:BATCH_SIZE]
        for vehicle in vehicles:
            vehicle.approval_status = ApprovalStatus.APPROVED
            vehicle.save(update_fields=["approval_status"])
            record(None, "vehicle.approved", vehicle, metadata)
            counts["vehicles"] += 1
    with transaction.atomic():
        updates = RouteUpdate.objects.select_for_update(skip_locked=True, of=("self",)).filter(
            status=RouteUpdateStatus.PENDING, created_at__lte=cutoff,
            reporter__is_active=True, reporter__verification__status=VerificationStatus.VERIFIED,
            route__is_active=True,
        ).order_by("created_at")[:BATCH_SIZE]
        for update in updates:
            update.status = RouteUpdateStatus.APPROVED
            update.reviewed_by = None
            update.reviewed_at = now
            update.save(update_fields=["status", "reviewed_by", "reviewed_at"])
            record(None, "route_update.moderated", update, {**metadata, "status": update.status})
            counts["route_updates"] += 1
    return counts


def review_snapshot(user):
    """Read only the current user's status, without processing any approvals."""
    account = Verification.objects.filter(user=user).values_list("status", flat=True).first() or "NOT_SUBMITTED"
    driver = DriverProfile.objects.filter(user=user).values_list("licence_review_status", flat=True).first() or ""
    vehicles = list(Vehicle.objects.filter(driver__user=user).order_by("pk").values_list("pk", "approval_status"))
    updates = list(RouteUpdate.objects.filter(reporter=user, status=RouteUpdateStatus.PENDING).order_by("pk").values_list("pk", flat=True))
    version = "|".join([account, driver, *[f"{pk}:{status}" for pk, status in vehicles], *map(str, updates)])
    return {"version": version}
