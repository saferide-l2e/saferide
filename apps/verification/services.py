"""Verification status transition service (BE-02).

Staff decisions and the separately audited timed-approval policy manage eligibility.
Users may only submit their own record for review. Every transition is audited.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record

from .models import Verification, VerificationStatus


def ensure_verification(user):
    """Return the user's verification row, creating a NOT_SUBMITTED one if absent."""
    verification, _ = Verification.objects.get_or_create(user=user)
    return verification


@transaction.atomic
def submit(user, *, profile_name="", home_area="", preferred_stop=""):
    """Passenger/driver submits their own demo verification request."""
    verification = ensure_verification(user)
    if verification.status == VerificationStatus.VERIFIED:
        raise ValidationError("Your account is already verified.")
    if verification.status == VerificationStatus.PENDING:
        raise ValidationError("Your verification is already awaiting review.")
    if verification.status == VerificationStatus.SUSPENDED:
        raise ValidationError("Your account is suspended and cannot be submitted.")
    verification.status = VerificationStatus.PENDING
    verification.submitted_at = timezone.now()
    verification.reviewed_by = None
    verification.reviewed_at = None
    verification.note = ""
    verification.profile_name = (profile_name or "")[:80]
    verification.home_area = (home_area or "")[:80]
    verification.preferred_stop = (preferred_stop or "")[:80]
    verification.save(update_fields=[
        "status", "submitted_at", "reviewed_by", "reviewed_at", "note",
        "profile_name", "home_area", "preferred_stop",
    ])
    if user.role == "DRIVER":
        from apps.vehicles.services import get_or_create_driver_profile

        get_or_create_driver_profile(user)
    record(user, "verification.submitted", verification)
    return verification


@transaction.atomic
def update_pending_profile(user, *, profile_name="", home_area="", preferred_stop=""):
    """Save travel-profile details without granting eligibility."""
    verification = ensure_verification(user)
    if verification.status != VerificationStatus.PENDING:
        raise ValidationError("Only a submitted profile may be updated here.")
    verification.profile_name = (profile_name or "")[:80]
    verification.home_area = (home_area or "")[:80]
    verification.preferred_stop = (preferred_stop or "")[:80]
    verification.save(update_fields=["profile_name", "home_area", "preferred_stop"])
    record(user, "verification.profile_updated", verification)
    return verification


def _require_staff(actor):
    if actor is None or not getattr(actor, "is_staff", False) or not actor.is_active:
        raise PermissionDenied("Only authorized staff may review verification.")


def _decide(verification, actor, new_status, note=""):
    _require_staff(actor)
    if verification.status in (VerificationStatus.NOT_SUBMITTED,):
        raise ValidationError("This verification has not been submitted.")
    if verification.user.is_staff and new_status != VerificationStatus.VERIFIED:
        raise ValidationError("Staff reviewers cannot be rejected through this endpoint.")
    verification.status = new_status
    verification.reviewed_by = actor
    verification.reviewed_at = timezone.now()
    verification.note = (note or "")[:280]
    verification.save(update_fields=["status", "reviewed_by", "reviewed_at", "note"])
    record(actor, f"verification.{new_status.lower()}", verification, {"user": str(verification.user_id)})
    return verification


@transaction.atomic
def approve(verification, actor, note=""):
    return _decide(verification, actor, VerificationStatus.VERIFIED, note)


@transaction.atomic
def reject(verification, actor, note=""):
    return _decide(verification, actor, VerificationStatus.REJECTED, note)


@transaction.atomic
def suspend(verification, actor, note=""):
    return _decide(verification, actor, VerificationStatus.SUSPENDED, note)


def is_verified(user):
    return bool(user and user.is_active and user.verification_status == VerificationStatus.VERIFIED)
