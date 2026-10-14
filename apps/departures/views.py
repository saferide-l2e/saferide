from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.bookings.models import Booking, BookingStatus, WaitlistEntry, WaitlistStatus
from apps.bookings.services import available_seats, check_in, passenger_eligible
from apps.core.exceptions import SafeRideError
from apps.core.permissions import driver_required, passenger_required
from apps.vehicles.services import get_or_create_driver_profile

from .forms import DepartureForm
from .models import Departure, DepartureStatus
from .services import apply_transition, create_departure


@passenger_required
def search(request):
    origin = (request.GET.get("origin") or "").strip()
    destination = (request.GET.get("destination") or "").strip()
    departures = []
    eligible = passenger_eligible(request.user)
    if eligible and (origin or destination):
        query = Departure.objects.filter(status=DepartureStatus.BOARDING_OPEN).select_related(
            "route", "driver", "vehicle"
        )
        if origin:
            query = query.filter(route__origin_name__icontains=origin)
        if destination:
            query = query.filter(route__destination_name__icontains=destination)
        now = timezone.now()
        for departure in query:
            departure.available = available_seats(departure, now)
            departures.append(departure)
    return render(
        request,
        "passenger/search.html",
        {
            "origin": origin,
            "destination": destination,
            "departures": departures,
            "eligible": eligible,
        },
    )


@passenger_required
def departure_detail(request, departure_id):
    departure = get_object_or_404(
        Departure.objects.select_related("route", "driver", "vehicle"), pk=departure_id
    )
    departure.available = available_seats(departure, timezone.now())
    my_booking = Booking.objects.filter(
        departure=departure,
        passenger=request.user,
        status__in=[BookingStatus.HELD, BookingStatus.BOARDED],
    ).first()
    my_entry = WaitlistEntry.objects.filter(
        departure=departure,
        passenger=request.user,
        status__in=[WaitlistStatus.WAITING, WaitlistStatus.OFFERED],
    ).first()
    return render(
        request,
        "passenger/departure_detail.html",
        {
            "departure": departure,
            "my_booking": my_booking,
            "my_entry": my_entry,
            "eligible": passenger_eligible(request.user),
        },
    )


@passenger_required
def availability(request, departure_id):
    """JSON seat/status feed for polling by the search and detail pages."""
    departure = get_object_or_404(Departure, pk=departure_id)
    return JsonResponse(
        {
            "status": departure.status,
            "status_display": departure.get_status_display(),
            "available": available_seats(departure, timezone.now()),
            "capacity": departure.snapshot_capacity,
        }
    )


@driver_required
def driver_dashboard(request):
    profile = get_or_create_driver_profile(request.user)
    departures = Departure.objects.filter(driver=request.user).select_related("route", "vehicle")
    now = timezone.now()
    for departure in departures:
        departure.available = available_seats(departure, now)
    return render(
        request,
        "driver/dashboard.html",
        {"profile": profile, "departures": departures},
    )


@driver_required
@require_http_methods(["GET", "POST"])
def departure_create(request):
    form = DepartureForm(request.POST or None, driver=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            departure = create_departure(
                request.user,
                vehicle=form.cleaned_data["vehicle"],
                route=form.cleaned_data["route"],
                scheduled_departure_at=form.cleaned_data["scheduled_departure_at"],
            )
            messages.success(request, "Draft departure created. Publish it when ready.")
            return redirect("departures:manage", departure_id=departure.id)
        except PermissionDenied:
            raise
        except (ValidationError, SafeRideError) as exc:
            text = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
            messages.error(request, text)
    return render(request, "driver/departure_form.html", {"form": form})


@driver_required
def departure_manage(request, departure_id):
    departure = get_object_or_404(
        Departure.objects.select_related("route", "vehicle"), pk=departure_id
    )
    if departure.driver_id != request.user.id:
        raise PermissionDenied("This departure belongs to another driver.")
    departure.available = available_seats(departure, timezone.now())
    roster = departure.bookings.select_related("passenger").exclude(
        status__in=[BookingStatus.EXPIRED, BookingStatus.CANCELLED]
    )
    offers = departure.waitlist_entries.filter(status=WaitlistStatus.OFFERED)
    return render(
        request,
        "driver/departure_manage.html",
        {"departure": departure, "roster": roster, "offers": offers},
    )


@driver_required
@require_http_methods(["POST"])
def departure_transition(request, departure_id):
    departure = get_object_or_404(Departure, pk=departure_id)
    action = request.POST.get("action", "")
    try:
        apply_transition(departure, request.user, action)
        messages.success(request, "Departure updated.")
    except PermissionDenied:
        raise
    except SafeRideError as exc:
        messages.error(request, str(exc))
    return redirect("departures:manage", departure_id=departure.id)


@driver_required
@require_http_methods(["POST"])
def departure_check_in(request, departure_id):
    departure = get_object_or_404(Departure, pk=departure_id)
    booking = get_object_or_404(
        Booking, pk=request.POST.get("booking_id", ""), departure=departure
    )
    try:
        check_in(booking, request.user, request.POST.get("code", ""))
        messages.success(request, "Passenger boarded.")
    except PermissionDenied:
        raise
    except SafeRideError as exc:
        messages.error(request, str(exc))
    return redirect("departures:manage", departure_id=departure.id)
