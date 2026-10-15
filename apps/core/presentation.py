"""Safe view-models for templates; never change booking or approval state here."""
from django.urls import reverse

from apps.bookings.models import BookingStatus
from apps.departures.models import DepartureStatus


def route_label(route):
    return f"{route.origin_name} → {route.destination_name}"


def departure_card(departure, available):
    profile = getattr(departure.driver, "driver_profile", None)
    seats = max(available, 0)
    return {
        "id": departure.pk,
        "route_label": route_label(departure.route),
        "boarding_point": departure.route.boarding_point,
        "destination_point": departure.route.destination_point,
        "scheduled_departure_at": departure.scheduled_departure_at,
        "vehicle_type_display": departure.vehicle.vehicle_type,
        "plate_display": departure.vehicle.plate_display,
        "driver_name": profile.approved_display_name if profile else "SafeRide driver",
        "driver_public_name": profile.approved_display_name if profile else "SafeRide driver",
        "driver_initials": "".join(
            word[:1].upper()
            for word in (profile.approved_display_name if profile else "SafeRide Driver").split()[:2]
        ),
        "driver_approved": bool(profile and profile.is_approved and departure.driver.is_verified),
        "available_seats": seats,
        "capacity": departure.snapshot_capacity,
        "is_full": seats == 0,
        "is_open": departure.status == DepartureStatus.BOARDING_OPEN,
        "detail_url": reverse("departures:detail", args=[departure.pk]),
        "status": departure.status,
        "status_label": departure.get_status_display(),
    }


def vehicle_card(vehicle):
    return {
        "vehicle_type_display": vehicle.vehicle_type,
        "plate_display": vehicle.plate_display,
        "seat_capacity": vehicle.capacity,
        "approval_status": vehicle.approval_status,
        "can_publish": vehicle.is_approved and vehicle.driver.user.is_verified,
        "publish_url": reverse("departures:create"),
    }


def driver_card(departure, available):
    result = departure_card(departure, available)
    result["detail_url"] = reverse("departures:manage", args=[departure.pk])
    result["boarded_count"] = departure.bookings.filter(status=BookingStatus.BOARDED).count()
    result["held_count"] = departure.bookings.filter(status=BookingStatus.HELD).count()
    return result


def booking_card(booking, code=None):
    departure = booking.departure
    return {
        "reference": str(booking.pk)[:8].upper(),
        "status": booking.status,
        "expires_at": booking.expires_at,
        "route_label": route_label(departure.route),
        "boarding_point": departure.route.boarding_point,
        "plate_display": departure.vehicle.plate_display,
        "boarding_code": code if booking.status == BookingStatus.HELD else None,
    }


def roster_card(booking):
    name = booking.passenger.display_name
    return {
        "id": booking.pk,
        "public_display_name": name,
        "initials": "".join(part[:1].upper() for part in name.split()[:2]),
        "short_reference": str(booking.pk)[:8].upper(),
        "status": booking.status,
        "expires_at": booking.expires_at,
        "verified": booking.passenger.is_verified,
    }
