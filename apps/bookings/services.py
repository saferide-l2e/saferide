import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import BoardingCredential, WaitlistEntry

OFFER_WINDOW = timedelta(seconds=120)


def hash_boarding_code(raw_code):
    """Return a salted Django password hash; callers must never log the raw code."""
    return make_password(raw_code)


def verify_boarding_code(raw_code, code_digest):
    """Constant-time verification helper for backend boarding flows."""
    return check_password(raw_code, code_digest)


def issue_boarding_credential(booking):
    """Create one credential and return it with its one-time raw code."""
    raw_code = secrets.token_urlsafe(16)
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
        .filter(departure=departure, status=WaitlistEntry.Status.WAITING)
        .fifo()
        .first()
    )
    if entry is None:
        return None

    entry.status = WaitlistEntry.Status.OFFERED
    entry.offered_at = now
    entry.offer_expires_at = now + offer_window
    entry.save(update_fields=["status", "offered_at", "offer_expires_at"])
    return entry
