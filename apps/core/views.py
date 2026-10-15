import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from apps.accounts.models import Role


def home(request):
    return render(request, "home.html", {
        "google_maps_browser_key": os.getenv("GOOGLE_MAPS_BROWSER_KEY", "").strip(),
    })


def health(request):
    return JsonResponse({"status": "ok"})


@login_required
def dashboard(request):
    """Role-aware landing page after sign-in."""
    context = {"role": request.user.role}
    if request.user.is_staff:
        context["panel"] = "staff"
    elif request.user.role == Role.DRIVER:
        context["panel"] = "driver"
    else:
        context["panel"] = "passenger"
        from apps.bookings.models import Booking

        completed = Booking.objects.filter(
            passenger=request.user, status=Booking.Status.COMPLETED
        ).count()
        # Earned progress only, not transferable or redeemable currency.
        context["completed_ride_count"] = completed
        context["reward_points"] = completed * 10
        context["reward_progress"] = (completed % 5) * 20
    return render(request, "dashboard.html", context)
