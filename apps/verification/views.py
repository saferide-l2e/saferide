from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .services import ensure_verification, submit


@login_required
def status(request):
    verification = ensure_verification(request.user)
    return render(request, "accounts/verification.html", {
        "verification": verification,
        "status": verification.status,
        "can_submit": verification.status in {"NOT_SUBMITTED", "REJECTED"},
        "submit_action": reverse("verification:submit"),
        "next_url": reverse("core:dashboard"),
        "rejection_reason": verification.note,
    })


@login_required
@require_http_methods(["POST"])
def submit_request(request):
    try:
        submit(request.user)
        messages.success(request, "Verification submitted for simulated review.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("verification:status")
