"""Reviews, private incident reports and moderated route updates (BE-10, BE-11)."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record
from apps.bookings.models import BookingStatus
from apps.verification.services import is_verified

from .models import (
    IncidentReport,
    IncidentStatus,
    Review,
    RouteUpdate,
    RouteUpdateStatus,
)


@transaction.atomic
def create_review(booking, actor, *, stars, comment=""):
    """A completed passenger leaves one 1–5 star review for their booking."""
    if not getattr(actor, "is_authenticated", False) or booking.passenger_id != actor.id:
        raise PermissionDenied("Only the passenger on this booking can review it.")
    if booking.status != BookingStatus.COMPLETED:
        raise ValidationError("You can only review a completed ride.")
    if Review.objects.filter(booking=booking).exists():
        raise ValidationError("You have already reviewed this ride.")
    try:
        stars = int(stars)
    except (TypeError, ValueError):
        raise ValidationError("Choose a star rating from 1 to 5.") from None
    if not 1 <= stars <= 5:
        raise ValidationError("Choose a star rating from 1 to 5.")

    review = Review.objects.create(
        booking=booking, author=actor, stars=stars, comment=(comment or "").strip()[:2000]
    )
    record(actor, "review.created", review, {"stars": stars})
    return review


@transaction.atomic
def create_incident(actor, *, category, description, booking=None, subject=None):
    """File a private misconduct/route report. Never published automatically."""
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Sign in first.")
    if not description or not description.strip():
        raise ValidationError("Describe what happened.")

    if booking is not None:
        involved = {booking.passenger_id, booking.departure.driver_id}
        if actor.id not in involved:
            raise PermissionDenied("You can only report a trip you were part of.")
        if subject is None:
            subject = (
                booking.departure.driver
                if actor.id == booking.passenger_id
                else booking.passenger
            )

    report = IncidentReport.objects.create(
        booking=booking,
        reporter=actor,
        subject=subject,
        category=category,
        description=description.strip()[:4000],
        status=IncidentStatus.PENDING,
    )
    record(actor, "incident.filed", report, {"category": category})
    return report


@transaction.atomic
def create_route_update(actor, *, route, type, note, occurred_at):
    """A verified user submits route/traffic information for moderation."""
    if not is_verified(actor):
        raise PermissionDenied("Only verified users can submit route updates.")
    if not note or not note.strip():
        raise ValidationError("Add a short note.")
    if occurred_at is None:
        raise ValidationError("When did this happen?")
    if timezone.is_naive(occurred_at):
        occurred_at = timezone.make_aware(occurred_at, timezone.get_current_timezone())

    update = RouteUpdate.objects.create(
        route=route,
        reporter=actor,
        type=type,
        note=note.strip()[:2000],
        occurred_at=occurred_at,
        status=RouteUpdateStatus.PENDING,
    )
    record(actor, "route_update.submitted", update, {"type": type})
    return update


def _require_staff(actor):
    if not (actor and actor.is_staff and actor.is_active):
        raise PermissionDenied("Only authorized staff may moderate reports.")


@transaction.atomic
def moderate_incident(report, actor, new_status):
    _require_staff(actor)
    if new_status not in IncidentStatus.values:
        raise ValidationError("Unknown incident status.")
    report.status = new_status
    report.reviewed_by = actor
    report.reviewed_at = timezone.now()
    report.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    record(actor, "incident.moderated", report, {"status": new_status})
    return report


@transaction.atomic
def moderate_route_update(update, actor, *, approve):
    _require_staff(actor)
    update.status = RouteUpdateStatus.APPROVED if approve else RouteUpdateStatus.REJECTED
    update.reviewed_by = actor
    update.reviewed_at = timezone.now()
    update.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    record(actor, "route_update.moderated", update, {"status": update.status})
    return update
