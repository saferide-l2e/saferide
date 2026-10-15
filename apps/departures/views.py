from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Value
from django.db.models.functions import Replace
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.bookings.models import Booking, BookingStatus, WaitlistEntry, WaitlistStatus
from apps.bookings.services import available_seats, check_in, passenger_eligible
from apps.core.exceptions import SafeRideError
from apps.core.permissions import driver_required, passenger_required
from apps.core.presentation import departure_card, driver_card, roster_card
from apps.vehicles.services import get_or_create_driver_profile

from .demo_discovery import clean_stop, sample_buses
from .forms import DepartureForm
from .models import Departure, DepartureStatus
from .services import apply_transition, create_departure


@require_http_methods(["GET"])
def search(request):
    """Browse database departures; fictional examples require a local opt-in."""
    origin = clean_stop(request.GET.get("origin", ""))
    destination = clean_stop(request.GET.get("destination", ""))
    has_searched = bool(origin or destination)
    valid_search = bool(
        origin and destination and origin.casefold() != destination.casefold()
    )
    eligible = passenger_eligible(request.user)
    departures = []
    now = timezone.now()
    if valid_search:
        query = (
            Departure.objects.filter(
                status=DepartureStatus.BOARDING_OPEN,
                scheduled_departure_at__gt=now + timedelta(seconds=600),
            )
            .annotate(
                origin_compact=Replace("route__origin_name", Value(" "), Value("")),
                destination_compact=Replace("route__destination_name", Value(" "), Value("")),
            )
            .filter(
                origin_compact__icontains=origin.replace(" ", ""),
                destination_compact__icontains=destination.replace(" ", ""),
            )
            .select_related("route", "driver", "vehicle")[:20]
        )
        for departure in query:
            departure.available = available_seats(departure, now)
            departures.append(departure)

    cards = [departure_card(d, d.available) for d in departures]
    preview_requested = settings.DEBUG and request.GET.get("preview") == "1"
    previews = sample_buses(origin, destination, now=now) if preview_requested and valid_search and not cards else []
    if has_searched and not valid_search:
        error_message = "Enter two different Lagos stops to find published departures."
    else:
        error_message = ""

    if has_searched and not eligible:
        eligibility_message = (
            "Only staff-approved passengers can reserve a seat. You can still browse "
            "published journeys and review driver and vehicle information."
        )
    else:
        eligibility_message = ""

    return render(request, "passenger/search.html", {
        "origin": origin,
        "destination": destination,
        "departures": departures,
        "buses": cards,
        "sample_buses": previews,
        "eligible": eligible,
        "has_searched": has_searched,
        "valid_search": valid_search,
        "is_pilot_route": (not valid_search or (
            origin.casefold().replace(" ", "") == "jibowu"
            and destination.casefold().replace(" ", "") == "mile2"
        )),
        "search_url": reverse("departures:search"),
        "eligibility_message": eligibility_message,
        "error_message": error_message,
    })


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
            "bus": departure_card(departure, departure.available),
            "search_url": reverse("departures:search"),
            "can_reserve": passenger_eligible(request.user) and not my_booking and not my_entry,
            "reserve_action": reverse("bookings:reserve", args=[departure.pk]),
            "can_join_waitlist": passenger_eligible(request.user) and not my_booking and not my_entry,
            "waitlist_action": reverse("bookings:join_waitlist", args=[departure.pk]),
            "verification_url": reverse("verification:status"),
            "booking_url": reverse("bookings:detail", args=[my_booking.pk]) if my_booking else None,
            "route_notices": [],
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
    cards = [driver_card(d, d.available) for d in departures]
    can_publish = request.user.is_verified and profile.vehicles.filter(
        approval_status="APPROVED"
    ).exists()
    return render(
        request,
        "driver/dashboard.html",
        {
            "profile": profile,
            "departures": cards,
            "can_publish": can_publish,
            "publish_url": reverse("departures:create"),
            "vehicle_list_url": reverse("vehicles:list"),
            "verification_url": reverse("verification:status"),
            "upcoming_count": len(cards),
            "approved_vehicle_count": profile.vehicles.filter(
                approval_status="APPROVED"
            ).count(),
            "boarded_today_count": sum(d["boarded_count"] for d in cards),
        },
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
    return render(request, "driver/departure_form.html", {
        "form": form,
        "form_action": reverse("departures:create"),
        "can_publish": request.user.is_verified,
        "dashboard_url": reverse("departures:dashboard"),
        "vehicle_list_url": reverse("vehicles:list"),
        "time_zone_label": "UTC (server time)",
    })


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
    card = driver_card(departure, departure.available)
    card["scheduled_departure_at"] = departure.scheduled_departure_at
    card["status"] = departure.status
    return render(
        request,
        "driver/departure_manage.html",
        {
            "departure": card,
            "roster": [roster_card(b) for b in roster],
            "offers": offers,
            "dashboard_url": reverse("departures:dashboard"),
            "transition_action": reverse("departures:transition", args=[departure.pk]),
            "checkin_action": reverse("departures:check_in", args=[departure.pk]),
            "can_close": departure.status == "BOARDING_OPEN",
            "can_start": departure.status == "BOARDING_CLOSED",
            "can_arrive": departure.status == "EN_ROUTE",
            "can_cancel": departure.status in {"DRAFT", "BOARDING_OPEN", "BOARDING_CLOSED"},
        },
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


@require_http_methods(["GET"])
def sample_ride(request):
    """Read-only fictional itinerary screen, never a bookable Departure."""
    origin = clean_stop(request.GET.get("origin", ""))
    destination = clean_stop(request.GET.get("destination", ""))
    try:
        option = int(request.GET.get("option", "1"))
    except (ValueError, TypeError):
        raise Http404("Choose a valid ride option.") from None
    if option not in (1, 2, 3, 4):
        raise Http404("Choose a valid ride option.")
    examples = sample_buses(origin, destination)
    if not examples:
        raise Http404("Select two different locations.")
    return render(request, "passenger/sample_ride.html", {
        "ride": examples[option - 1],
        "origin": origin,
        "destination": destination,
        "search_url": reverse("departures:search"),
        "history_url": reverse("bookings:index"),
        "safety_url": reverse("safety:report"),
    })
