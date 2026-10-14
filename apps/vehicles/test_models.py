import pytest
from django.db import IntegrityError, connection, transaction

from apps.accounts.models import User
from apps.vehicles.models import DriverProfile, Vehicle


@pytest.fixture
def driver(db):
    user = User.objects.create_user(
        username="driver-one",
        email="driver@example.test",
        password="safe-test-password",
        display_name="Demo Driver",
        role=User.Role.DRIVER,
    )
    return DriverProfile.objects.create(
        user=user,
        licence_status=DriverProfile.LicenceStatus.APPROVED,
    )


def make_vehicle(driver, plate="ABC-123DE", **kwargs):
    kwargs.setdefault("seat_capacity", 30)
    return Vehicle.objects.create(
        driver=driver,
        plate_display=plate,
        vehicle_type=Vehicle.VehicleType.BUS,
        **kwargs,
    )


@pytest.mark.django_db(transaction=True)
def test_approved_driver_can_own_multiple_vehicles(driver):
    first = make_vehicle(driver, "ABC-123DE")
    second = make_vehicle(driver, "XYZ-456FG")

    assert driver.licence_status == DriverProfile.LicenceStatus.APPROVED
    assert driver.vehicles.count() == 2
    assert first.approval_status == Vehicle.ApprovalStatus.PENDING
    assert first.plate_normalized == "ABC123DE"
    assert second.driver_id == driver.id


@pytest.mark.django_db(transaction=True)
def test_database_rejects_duplicate_normalized_plates(driver):
    make_vehicle(driver, "ABC-123DE")

    with pytest.raises(IntegrityError), transaction.atomic():
        make_vehicle(driver, "abc 123de")


@pytest.mark.django_db(transaction=True)
def test_database_normalizes_plate_even_when_model_save_is_bypassed(driver):
    make_vehicle(driver, "ABC-123DE")
    if connection.vendor != "postgresql":
        pytest.skip("Plate normalization trigger is enforced by PostgreSQL.")

    with pytest.raises(IntegrityError), transaction.atomic():
        Vehicle.objects.bulk_create(
            [
                Vehicle(
                    driver=driver,
                    plate_display="abc 123de",
                    plate_normalized="different-value",
                    vehicle_type=Vehicle.VehicleType.BUS,
                    seat_capacity=30,
                )
            ]
        )


@pytest.mark.parametrize("capacity", [0, -1])
@pytest.mark.django_db(transaction=True)
def test_database_rejects_non_positive_capacity(driver, capacity):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_vehicle(driver, seat_capacity=capacity)


@pytest.mark.django_db(transaction=True)
def test_database_rejects_driver_profile_for_passenger():
    passenger = User.objects.create_user(
        username="passenger-one",
        email="passenger@example.test",
        password="safe-test-password",
        display_name="Demo Passenger",
        role=User.Role.PASSENGER,
    )

    if connection.vendor != "postgresql":
        pytest.skip("Driver role guard is enforced by a PostgreSQL trigger.")

    with pytest.raises(IntegrityError), transaction.atomic():
        DriverProfile.objects.create(user=passenger)
