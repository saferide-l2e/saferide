from datetime import UTC, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.departures.models import Departure
from apps.departures.services import create_departure, transition_departure
from apps.routes.models import Route
from apps.vehicles.models import DriverProfile, Vehicle


@pytest.fixture
def route(db):
    route, _ = Route.objects.get_or_create(
        display_label="DEMO: Jibowu → Mile 2",
        defaults={
            "origin_name": "Jibowu",
            "destination_name": "Mile 2",
            "boarding_point": "DEMO boarding point — Jibowu",
            "destination_point": "DEMO destination point — Mile 2",
            "is_demo": True,
        },
    )
    return route


@pytest.fixture
def driver(db):
    user = User.objects.create_user(
        username="route-driver",
        email="route-driver@example.test",
        password="safe-test-password",
        display_name="Route Driver",
        role=User.Role.DRIVER,
    )
    return DriverProfile.objects.create(
        user=user,
        licence_status=DriverProfile.LicenceStatus.APPROVED,
    )


@pytest.fixture
def vehicle(driver):
    return Vehicle.objects.create(
        driver=driver,
        plate_display="DB03-001",
        vehicle_type=Vehicle.VehicleType.BUS,
        seat_capacity=30,
    )


@pytest.fixture
def scheduled_time():
    return datetime.now(UTC) + timedelta(days=1)


def make_departure(route, driver, vehicle, scheduled_time, **kwargs):
    return create_departure(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=scheduled_time,
        **kwargs,
    )


@pytest.mark.django_db(transaction=True)
def test_departure_snapshots_vehicle_capacity(route, driver, vehicle, scheduled_time):
    departure = make_departure(route, driver, vehicle, scheduled_time)
    vehicle.seat_capacity = 24
    vehicle.save()

    departure.refresh_from_db()
    assert departure.capacity_snapshot == 30
    assert departure.scheduled_departure_at.utcoffset() == timedelta(0)


@pytest.mark.django_db
def test_route_search_indexes_are_present():
    index_fields = {tuple(index.fields) for index in Departure._meta.indexes}

    assert ("route", "status", "scheduled_departure_at") in index_fields
    assert ("driver", "status") in index_fields


@pytest.mark.django_db(transaction=True)
def test_service_rejects_vehicle_owned_by_another_driver(route, driver, vehicle, scheduled_time):
    other_user = User.objects.create_user(
        username="other-driver",
        email="other-driver@example.test",
        password="safe-test-password",
        display_name="Other Driver",
        role=User.Role.DRIVER,
    )
    other_driver = DriverProfile.objects.create(user=other_user)

    with pytest.raises(ValidationError, match="belong"):
        make_departure(route, other_driver, vehicle, scheduled_time)


@pytest.mark.django_db(transaction=True)
def test_only_approved_vehicle_can_be_published(route, driver, vehicle, scheduled_time):
    departure = make_departure(route, driver, vehicle, scheduled_time)

    with pytest.raises(ValidationError, match="approved"):
        transition_departure(departure, Departure.Status.BOARDING_OPEN)

    vehicle.approval_status = Vehicle.ApprovalStatus.APPROVED
    vehicle.save()
    published = transition_departure(departure, Departure.Status.BOARDING_OPEN)
    assert published.status == Departure.Status.BOARDING_OPEN


@pytest.mark.django_db(transaction=True)
def test_service_rejects_naive_departure_timestamp(route, driver, vehicle):
    with pytest.raises(ValidationError, match="timezone-aware"):
        make_departure(route, driver, vehicle, datetime(2026, 10, 16, 8, 0))


@pytest.mark.django_db(transaction=True)
def test_database_rejects_invalid_status_and_negative_walk_ins(
    route, driver, vehicle, scheduled_time
):
    with pytest.raises(IntegrityError), transaction.atomic():
        Departure.objects.create(
            route=route,
            driver=driver,
            vehicle=vehicle,
            scheduled_departure_at=scheduled_time,
            capacity_snapshot=30,
            status="DRIVING",
        )

    with pytest.raises(IntegrityError), transaction.atomic():
        Departure.objects.create(
            route=route,
            driver=driver,
            vehicle=vehicle,
            scheduled_departure_at=scheduled_time,
            capacity_snapshot=30,
            walk_in_count=-1,
        )


@pytest.mark.django_db(transaction=True)
def test_service_rejects_invalid_lifecycle_transition(route, driver, vehicle, scheduled_time):
    departure = make_departure(route, driver, vehicle, scheduled_time)

    with pytest.raises(ValidationError, match="Unknown"):
        transition_departure(departure, "DRIVING")
