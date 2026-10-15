"""Deterministic, read-only *fictional* bus previews for arbitrary demo routes.

No database writes, real seat inventory, trusted drivers, geocoding, or
external services. The result cannot be booked or checked in.
"""

import hashlib
import random
from datetime import timedelta

from django.utils import timezone

DEMO_VEHICLES = (
    "Yellow danfo (illustration)",
    "Lagos-style minibus (illustration)",
    "Shuttle bus (illustration)",
    "City minibus (illustration)",
)


def clean_stop(value):
    """Bound user-provided place labels before rendering/querying."""
    if not isinstance(value, str):
        return ""
    # Ignore control characters rather than allowing misleading invisible labels.
    value = "".join(char for char in value if char.isprintable())
    return " ".join(value.split())[:80].strip()


def sample_buses(origin, destination, *, now=None, count=4):
    """Return stable examples for the same route and UTC day, with future times.

    The synthetic seat numbers are *not* available seats in the booking database.
    Do not add reservation URLs or transform these examples into Departure rows.
    """
    origin, destination = clean_stop(origin), clean_stop(destination)
    if not origin or not destination or origin.casefold() == destination.casefold():
        return []

    now = now or timezone.now()
    bucket = now.astimezone(timezone.utc).date().isoformat()
    key = f"{origin.casefold()}|{destination.casefold()}|{bucket}"
    rng = random.Random(int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest(), "big"))

    result = []
    for index in range(min(max(count, 0), 4)):
        capacity = rng.choice((12, 14, 16, 18))
        seats = rng.randint(2, min(capacity, 9))
        departure = now + timedelta(minutes=35 + index * 34 + rng.randint(0, 12))
        result.append({
            "reference": f"SIM-{index + 1:02d}",
            "route_label": f"{origin} → {destination}",
            "boarding_point": f"{origin} (example pickup)",
            "destination_point": f"{destination} (example drop-off)",
            "vehicle_type_display": DEMO_VEHICLES[rng.randrange(len(DEMO_VEHICLES))],
            "plate_display": f"DEMO-{index + 1:02d}",
            "driver_public_name": f"Fictional driver {index + 1}",
            "scheduled_departure_at": departure,
            "available_seats": seats,
            "capacity": capacity,
            "is_simulated": True,
            "bookable": False,
        })
    return result
