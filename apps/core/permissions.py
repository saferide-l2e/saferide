"""Reusable access-control decorators (BE-13).

Every view that touches private data must be guarded here. Cross-user and
cross-driver access returns 403 (forbidden) or 404 (not found) rather than
leaking another person's data.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from apps.accounts.models import Role


def _fail(request):
    if request.user.is_authenticated:
        raise PermissionDenied("You do not have access to this resource.")
    return login_required(lambda r: None)(request)


def role_required(*roles):
    """Require an authenticated, active user with one of ``roles``."""

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.is_active or request.user.role not in roles:
                raise PermissionDenied("You do not have access to this resource.")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


passenger_required = role_required(Role.PASSENGER)
driver_required = role_required(Role.DRIVER)


def verified_required(view):
    """Require a verified, active account (passenger or driver)."""

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_verified:
            raise PermissionDenied("Your demo verification must be approved first.")
        return view(request, *args, **kwargs)

    return wrapper


def staff_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_active and request.user.is_staff):
            raise PermissionDenied("Staff access is required.")
        return view(request, *args, **kwargs)

    return wrapper
