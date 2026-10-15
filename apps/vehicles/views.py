from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.core.automatic_reviews import review_snapshot
from apps.core.permissions import driver_required
from apps.core.presentation import vehicle_card

from .forms import VehicleForm
from .services import get_or_create_driver_profile, register_vehicle


@driver_required
def vehicle_list(request):
    profile = get_or_create_driver_profile(request.user)
    return render(
        request,
        "driver/vehicles.html",
        {
            "review_pending": profile.vehicles.filter(approval_status="PENDING").exists(),
            "review_version": review_snapshot(request.user)["version"],
            "profile": profile,
            "vehicles": [vehicle_card(v) for v in profile.vehicles.all()],
            "can_register": True,
            "register_url": reverse("vehicles:create"),
        },
    )


@driver_required
@require_http_methods(["GET", "POST"])
def vehicle_create(request):
    form = VehicleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            register_vehicle(
                request.user,
                plate_display=form.cleaned_data["plate_display"],
                vehicle_type=form.cleaned_data["vehicle_type"],
                capacity=form.cleaned_data["capacity"],
            )
            messages.success(request, "Vehicle submitted for approval.")
            return redirect("vehicles:list")
        except PermissionDenied as exc:
            form.add_error(None, str(exc))
        except ValidationError as exc:
            for msg in exc.messages:
                form.add_error(None, msg)
    profile = get_or_create_driver_profile(request.user)
    return render(request, "driver/vehicle_form.html", {
        "form": form, "profile": profile, "can_register": request.user.is_verified,
        "action_message": "Your driver account must be approved before you can submit a vehicle. Review your account status to complete your profile or check progress.",
        "form_action": reverse("vehicles:create"),
        "vehicle_list_url": reverse("vehicles:list"),
        "verification_url": reverse("verification:status"),
    })


@driver_required
def driver_profile(request):
    profile = get_or_create_driver_profile(request.user)
    if request.method == "POST":
        bio = (request.POST.get("bio") or "").strip()[:200]
        display = (request.POST.get("approved_display_name") or "").strip()[:80]
        if display:
            profile.approved_display_name = display
        profile.bio = bio
        profile.save(update_fields=["approved_display_name", "bio"])
        messages.success(request, "Driver profile updated.")
        return redirect("vehicles:profile")
    return render(request, "driver/profile.html", {"profile": profile})
