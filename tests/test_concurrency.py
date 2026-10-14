"""Concurrency invariants that require real PostgreSQL row locks.

On SQLite ``select_for_update`` is a no-op, so these tests are skipped there.
They run in CI, where the PostgreSQL service is available.
"""

import threading
from datetime import timedelta

import pytest
from django.db import connection, connections
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.bookings.services import reserve
from apps.core.exceptions import CapacityError, SafeRideError
from apps.departures.models import Departure, DepartureStatus
from apps.verification.models import Verification, VerificationStatus


def _verified_user(email, name):
    user = User.objects.create_user(email, "concurrency-123", display_name=name, role=Role.PASSENGER)
    Verification.objects.create(user=user, status=VerificationStatus.VERIFIED)
    return user


@pytest.mark.django_db(transaction=True)
def test_last_seat_one_winner_under_concurrency(driver, vehicle, route):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency requires PostgreSQL.")

    departure = Departure.objects.create(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=timezone.now() + timedelta(hours=2),
        snapshot_capacity=1,
        status=DepartureStatus.BOARDING_OPEN,
    )
    alice = _verified_user("alice@example.test", "Alice A")
    bob = _verified_user("bob@example.test", "Bob B")

    barrier = threading.Barrier(2)
    outcomes = []
    lock = threading.Lock()

    def worker(user):
        try:
            barrier.wait(timeout=10)
            reserve(user, departure)
            result = "ok"
        except CapacityError:
            result = "full"
        except SafeRideError as exc:  # unexpected domain error
            result = f"error:{exc}"
        except Exception as exc:  # noqa: BLE001 - surfaced in the assertion below
            result = f"crashed:{exc!r}"
        finally:
            connections.close_all()
        with lock:
            outcomes.append(result)

    threads = [threading.Thread(target=worker, args=(alice,)), threading.Thread(target=worker, args=(bob,))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(outcomes) == ["full", "ok"], outcomes
    assert departure.bookings.filter(status__in=["HELD", "BOARDED"]).count() == 1
