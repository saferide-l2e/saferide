from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.bookings.models import Booking

from .forms import IncidentForm, ReviewForm, RouteUpdateForm
from .models import RouteUpdate, RouteUpdateStatus
from .services import create_incident, create_review, create_route_update


@login_required
@require_http_methods(["GET", "POST"])
def review_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if booking.passenger_id != request.user.id:
        raise PermissionDenied("This booking belongs to another passenger.")
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_review(
                booking,
                request.user,
                stars=form.cleaned_data["stars"],
                comment=form.cleaned_data["comment"],
            )
            messages.success(request, "Thanks — your review was saved.")
            return redirect("bookings:detail", booking_id=booking.id)
        except PermissionDenied:
            raise
        except ValidationError as exc:
            form.add_error(None, "; ".join(exc.messages))
    return render(request, "safety/review_form.html", {"form": form, "booking": booking})


@login_required
@require_http_methods(["GET", "POST"])
def report_incident(request, booking_id=None):
    booking = get_object_or_404(Booking, pk=booking_id) if booking_id else None
    if booking is not None and request.user.id not in {
        booking.passenger_id,
        booking.departure.driver_id,
    }:
        raise PermissionDenied("You can only report a trip you were part of.")
    form = IncidentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_incident(
                request.user,
                category=form.cleaned_data["category"],
                description=form.cleaned_data["description"],
                booking=booking,
            )
            messages.success(
                request, "Private report submitted. It will be reviewed by an administrator."
            )
            return redirect("bookings:index" if booking else "core:dashboard")
        except PermissionDenied:
            raise
        except ValidationError as exc:
            form.add_error(None, "; ".join(exc.messages))
    return render(request, "safety/incident_form.html", {"form": form, "booking": booking})


@login_required
@require_http_methods(["GET", "POST"])
def route_update(request):
    form = RouteUpdateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            create_route_update(
                request.user,
                route=form.cleaned_data["route"],
                type=form.cleaned_data["type"],
                note=form.cleaned_data["note"],
                occurred_at=form.cleaned_data["occurred_at"],
            )
            messages.success(request, "Route update submitted for moderation.")
            return redirect("safety:route_updates")
        except PermissionDenied:
            raise
        except ValidationError as exc:
            form.add_error(None, "; ".join(exc.messages))
    return render(request, "safety/route_update_form.html", {"form": form})


def route_updates(request):
    """Public list showing only APPROVED updates, with timestamps."""
    updates = (
        RouteUpdate.objects.filter(status=RouteUpdateStatus.APPROVED)
        .select_related("route", "reporter")
        .order_by("-occurred_at")
    )
    return render(request, "safety/route_updates.html", {"updates": updates})
