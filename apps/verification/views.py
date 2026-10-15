from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import VerificationDeclarationForm
from .services import ensure_verification, submit


@login_required
def status(request):
    return _status_page(request)


def _status_page(request, form=None, http_status=200):
    verification = ensure_verification(request.user)
    return render(request, "accounts/verification.html", {
        "verification": verification,
        "status": verification.status,
        "can_submit": verification.status in {"NOT_SUBMITTED", "REJECTED"},
        "submit_action": reverse("verification:submit"),
        "next_url": reverse("core:dashboard"),
        "rejection_reason": verification.note,
        "form": form if form is not None else VerificationDeclarationForm(),
    }, status=http_status)


@login_required
@require_http_methods(["POST"])
def submit_request(request):
    form = VerificationDeclarationForm(request.POST)
    if not form.is_valid():
        return _status_page(request, form=form, http_status=400)
    try:
        submit(request.user)
        messages.success(request, "Verification submitted for simulated review.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("verification:status")
