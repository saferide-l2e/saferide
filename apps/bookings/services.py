import secrets

from django.contrib.auth.hashers import check_password, make_password

from apps.bookings.models import BoardingCredential


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
