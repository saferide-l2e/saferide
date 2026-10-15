from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.core.exceptions import SafeRideError
from apps.core.permissions import passenger_required
from apps.core.presentation import booking_card, route_label
from apps.departures.models import Departure

from .models import Booking, BookingStatus, WaitlistEntry, WaitlistStatus
from .services import accept_offer, cancel, confirm_arrival, join_waitlist, reserve


def _remember_code(request, booking, code):
    request.session[f"boarding_code_{booking.id}"] = code


@passenger_required
def my_bookings(request):
    bookings = (
        Booking.objects.filter(passenger=request.user)
        .select_related("departure__route", "departure__driver", "departure__vehicle")
        .order_by("-created_at")
    )
    offers = WaitlistEntry.objects.filter(
        passenger=request.user, status=WaitlistStatus.OFFERED
    ).select_related("departure__route")
    return render(request, "booking/my_bookings.html", {
        "bookings": bookings,
        "offers": offers,
        "search_url": reverse("departures:search"),
    })


@passenger_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("departure__route", "departure__driver"), pk=booking_id
    )
    if booking.passenger_id != request.user.id:
        raise PermissionDenied("This reservation belongs to another passenger.")
    return render(
        request,
        "booking/detail.html",
        {
            "booking": booking_card(
                booking, request.session.get(f"boarding_code_{booking.id}")
            ),
            "boarding_code": request.session.get(f"boarding_code_{booking.id}"),
            "server_now": timezone.now(),
            "cancel_action": reverse("bookings:cancel", args=[booking.pk]),
            "status_url": reverse("bookings:status", args=[booking.pk]),
            "search_url": reverse("departures:search"),
            "confirm_action": reverse("bookings:confirm_arrival", args=[booking.pk])
            if booking.driver_arrived_at and booking.status == BookingStatus.BOARDED
            else None,
            "review_url": reverse("safety:review", args=[booking.pk])
            if booking.status == BookingStatus.COMPLETED else None,
        },
    )


@passenger_required
def booking_status(request, booking_id):
    """Small JSON endpoint the browser polls for the server-authoritative countdown."""
    booking = get_object_or_404(Booking.objects.select_related("departure"), pk=booking_id)
    if booking.passenger_id != request.user.id:
        raise PermissionDenied("This reservation belongs to another passenger.")
    now = timezone.now()
    remaining = None
    if booking.status == BookingStatus.HELD and booking.expires_at is not None:
        remaining = max(int((booking.expires_at - now).total_seconds()), 0)
    return JsonResponse(
        {
            "status": booking.status,
            "status_display": booking.get_status_display(),
            "expires_at": booking.expires_at.isoformat() if booking.expires_at else None,
            "seconds_remaining": remaining,
            "checked_in_at": booking.checked_in_at.isoformat() if booking.checked_in_at else None,
        }
    )


@passenger_required
@require_http_methods(["POST"])
def reserve_seat(request, departure_id):
    departure = get_object_or_404(Departure, pk=departure_id)
    try:
        booking, code = reserve(request.user, departure)
        _remember_code(request, booking, code)
        messages.success(request, "Seat held for 10 minutes. Boarding code shown below.")
        return redirect("bookings:detail", booking_id=booking.id)
    except SafeRideError as exc:
        messages.error(request, str(exc))
    return redirect("departures:detail", departure_id=departure.id)


@passenger_required
@require_http_methods(["POST"])
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    try:
        cancel(booking, request.user)
        messages.success(request, "Reservation cancelled.")
    except SafeRideError as exc:
        messages.error(request, str(exc))
    return redirect("bookings:detail", booking_id=booking.id)


@passenger_required
@require_http_methods(["POST"])
def join_waitlist_view(request, departure_id):
    departure = get_object_or_404(Departure, pk=departure_id)
    try:
        join_waitlist(request.user, departure)
        messages.success(request, "You joined the waitlist. We will offer you a seat if one frees up.")
    except SafeRideError as exc:
        messages.error(request, str(exc))
    return redirect("departures:detail", departure_id=departure.id)


@passenger_required
@require_http_methods(["POST"])
def accept_offer_view(request, entry_id):
    entry = get_object_or_404(WaitlistEntry, pk=entry_id)
    try:
        booking, code = accept_offer(entry, request.user)
        _remember_code(request, booking, code)
        messages.success(request, "Offer accepted. Seat held for 10 minutes.")
        return redirect("bookings:detail", booking_id=booking.id)
    except SafeRideError as exc:
        messages.error(request, str(exc))
    return redirect("bookings:index")


@passenger_required
@require_http_methods(["POST"])
def confirm_arrival_view(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    try:
        confirm_arrival(booking, request.user)
        messages.success(request, "Arrival confirmed. You can now leave a review.")
    except SafeRideError as exc:
        messages.error(request, str(exc))
    return redirect("bookings:detail", booking_id=booking.id)
