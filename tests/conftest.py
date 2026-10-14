from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.bookings.services import reserve
from apps.departures.models import Departure, DepartureStatus
from apps.routes.models import Route
from apps.vehicles.models import ApprovalStatus, DriverProfile, Vehicle
from apps.verification.models import Verification, VerificationStatus

PASSWORD = "saferide-test-123"

# The backend's page views render these template names. The frontend team owns
# the files themselves; tests use a stub loader so backend view logic and this
# contract can be verified without shipping frontend assets.
FRONTEND_TEMPLATES = [
    "home.html",
    "dashboard.html",
    "accounts/register.html",
    "accounts/login.html",
    "accounts/profile.html",
    "accounts/verification.html",
    "driver/dashboard.html",
    "driver/vehicles.html",
    "driver/vehicle_form.html",
    "driver/profile.html",
    "driver/departure_form.html",
    "driver/departure_manage.html",
    "passenger/search.html",
    "passenger/departure_detail.html",
    "passenger/routes.html",
    "booking/my_bookings.html",
    "booking/detail.html",
    "safety/review_form.html",
    "safety/incident_form.html",
    "safety/route_update_form.html",
    "safety/route_updates.html",
]


@pytest.fixture
def stub_frontend_templates(settings):
    """Render page views against in-memory placeholder templates.

    This verifies the backend renders its documented template name without
    depending on files owned by the frontend team.
    """
    settings.TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": False,
            "OPTIONS": {
                "loaders": [
                    (
                        "django.template.loaders.locmem.Loader",
                        {name: f"SafeRide stub: {name}" for name in FRONTEND_TEMPLATES},
                    )
                ]
            },
        }
    ]
    return FRONTEND_TEMPLATES


def _verify(user, status=VerificationStatus.VERIFIED):
    verification, _ = Verification.objects.get_or_create(user=user)
    verification.status = status
    verification.save(update_fields=["status"])
    return user


@pytest.fixture
def make_user(db):
    def _make(email, display_name, role, verified=True, active=True, staff=False):
        user = User.objects.create_user(email, PASSWORD, display_name=display_name, role=role)
        user.is_active = active
        if staff:
            user.is_staff = True
        user.save()
        if verified:
            _verify(user)
        else:
            _verify(user, VerificationStatus.NOT_SUBMITTED)
        return user

    return _make


@pytest.fixture
def passenger(make_user):
    return make_user("passenger@example.test", "Penny Passenger", Role.PASSENGER)


@pytest.fixture
def other_passenger(make_user):
    return make_user("other@example.test", "Ola Other", Role.PASSENGER)


@pytest.fixture
def unverified_passenger(make_user):
    return make_user("unverified@example.test", "Umar Unverified", Role.PASSENGER, verified=False)


@pytest.fixture
def other_driver(make_user):
    return make_user("otherdriver@example.test", "Otis Otherdriver", Role.DRIVER)


@pytest.fixture
def staff(make_user):
    return make_user("staff@example.test", "Sam Staff", Role.PASSENGER, staff=True)


@pytest.fixture
def route(db):
    return Route.objects.create(
        origin_name="Jibowu",
        destination_name="Mile 2",
        boarding_point="Jibowu bus terminal",
        destination_point="Mile 2 park",
    )


@pytest.fixture
def driver(make_user):
    user = make_user("driver@example.test", "Dan Driver", Role.DRIVER)
    profile, _ = DriverProfile.objects.get_or_create(user=user)
    profile.licence_review_status = ApprovalStatus.APPROVED
    profile.save()
    return user


@pytest.fixture
def vehicle(driver):
    profile = driver.driver_profile
    return Vehicle.objects.create(
        driver=profile,
        plate_display="DEMO-001",
        plate_normalized="DEMO001",
        vehicle_type="Toyota Hiace bus",
        capacity=4,
        approval_status=ApprovalStatus.APPROVED,
    )


@pytest.fixture
def departure(driver, vehicle, route):
    return Departure.objects.create(
        route=route,
        driver=driver,
        vehicle=vehicle,
        scheduled_departure_at=timezone.now() + timedelta(hours=2),
        snapshot_capacity=vehicle.capacity,
        status=DepartureStatus.BOARDING_OPEN,
    )


@pytest.fixture
def booking(passenger, departure):
    booking, _ = reserve(passenger, departure)
    return booking
