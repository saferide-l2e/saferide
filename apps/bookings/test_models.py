from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.models import BoardingCredential, Booking
from apps.bookings.services import issue_boarding_credential, verify_boarding_code
from apps.departures.services import create_departure
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
        username="booking-driver",
        email="booking-driver@example.test",
        password="safe-test-password",
        display_name="Booking Driver",
        role=User.Role.DRIVER,
    )
    profile = DriverProfile.objects.create(
        user=user,
        licence_status=DriverProfile.LicenceStatus.APPROVED,
    )
    return profile


@pytest.fixture
def vehicle(driver):
    return Vehicle.objects.create(
        driver=driver,
        plate_display="DB04-001",
        vehicle_type=Vehicle.VehicleType.BUS,
        seat_capacity=30,
        approval_status=Vehicle.ApprovalStatus.APPROVED,
    )


@pytest.fixture
def departure(route, driver, vehicle):
    return create_departure(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=timezone.now() + timedelta(days=1),
    )


@pytest.fixture
def passenger(db):
    return User.objects.create_user(
        username="booking-passenger",
        email="booking-passenger@example.test",
        password="safe-test-password",
        display_name="Booking Passenger",
        role=User.Role.PASSENGER,
    )


def make_booking(departure, passenger, status=Booking.Status.HELD):
    return Booking.objects.create(
        departure=departure,
        passenger=passenger,
        status=status,
        expires_at=timezone.now() + timedelta(minutes=10),
    )


@pytest.mark.django_db(transaction=True)
def test_only_one_active_booking_per_departure_and_passenger(departure, passenger):
    make_booking(departure, passenger)
    with pytest.raises(IntegrityError), transaction.atomic():
        make_booking(departure, passenger, Booking.Status.BOARDED)

    # Terminal history remains available while the active partial unique index applies.
    completed = make_booking(departure, passenger, Booking.Status.COMPLETED)
    assert completed.status == Booking.Status.COMPLETED


@pytest.mark.django_db(transaction=True)
def test_booking_status_choices_and_arrival_timestamps(departure, passenger):
    booking = make_booking(departure, passenger)
    assert set(Booking.Status.values) == {
        "HELD",
        "BOARDED",
        "COMPLETED",
        "CANCELLED",
        "EXPIRED",
        "DISPUTED",
    }
    assert booking.checked_in_at is None
    assert booking.driver_arrived_at is None
    assert booking.passenger_confirmed_at is None

    with pytest.raises(IntegrityError), transaction.atomic():
        make_booking(departure, passenger, "WAITING")


@pytest.mark.django_db(transaction=True)
def test_boarding_code_is_salted_verified_and_stored_only_as_digest(departure, passenger):
    booking = make_booking(departure, passenger)
    credential, raw_code = issue_boarding_credential(booking)

    assert credential.code_digest != raw_code
    assert raw_code not in credential.code_digest
    assert verify_boarding_code(raw_code, credential.code_digest)
    assert not verify_boarding_code("incorrect-code", credential.code_digest)
    assert str(credential) == f"Boarding credential for booking {booking.pk}"


@pytest.mark.django_db(transaction=True)
def test_boarding_credentials_are_unique_by_booking_and_digest(
    departure, passenger
):
    first_booking = make_booking(departure, passenger)
    first_credential, _ = issue_boarding_credential(first_booking)

    with pytest.raises(IntegrityError), transaction.atomic():
        BoardingCredential.objects.create(
            booking=first_booking,
            code_digest="different-salted-digest",
        )

    second_passenger = User.objects.create_user(
        username="booking-passenger-two",
        email="booking-passenger-two@example.test",
        password="safe-test-password",
        display_name="Second Passenger",
        role=User.Role.PASSENGER,
    )
    second_booking = make_booking(departure, second_passenger)
    with pytest.raises(IntegrityError), transaction.atomic():
        BoardingCredential.objects.create(
            booking=second_booking,
            code_digest=first_credential.code_digest,
        )
