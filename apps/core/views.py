import os

from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.cache import never_cache

from apps.accounts.models import Role


def home(request):
    # Footage is opt-in as a complete, reviewed asset set. Missing encodes must
    # never create broken requests or conceal the original static composition.
    video_files = {
        f"{size}_{codec}": f"media/saferide-lagos-{size}.{codec}"
        for size in ("desktop", "mobile") for codec in ("webm", "mp4")
    }
    video = (
        {key: static(path) for key, path in video_files.items()}
        if all(finders.find(path) for path in video_files.values()) else None
    )
    return render(request, "home.html", {
        "google_maps_browser_key": os.getenv("GOOGLE_MAPS_BROWSER_KEY", "").strip(),
        "cinematic_video": video,
    })


def how_it_works(request):
    return render(request, "public/how_it_works.html")


def for_drivers(request):
    return render(request, "public/for_drivers.html")


def safety_support(request):
    return render(request, "public/safety_support.html")


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


@never_cache
@login_required
def review_progress(request):
    from .automatic_reviews import review_snapshot

    return JsonResponse(review_snapshot(request.user))
