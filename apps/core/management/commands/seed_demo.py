"""Create synthetic demo data (DB-08).

Everything here is fictional. Safe to run repeatedly: existing rows are reused.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.departures.models import Departure, DepartureStatus
from apps.routes.models import Route
from apps.vehicles.models import ApprovalStatus, DriverProfile, Vehicle
from apps.verification.models import Verification, VerificationStatus

DEMO_PASSWORD = "saferide-demo-123"


class Command(BaseCommand):
    help = "Create fictional demo accounts, a route, a vehicle and a departure."

    def handle(self, *args, **options):
        admin = self._ensure_user(
            "admin@example.test", "Demo Admin", Role.PASSENGER, staff=True, superuser=True
        )
        passenger = self._ensure_user("passenger@example.test", "Demo Passenger", Role.PASSENGER)
        driver = self._ensure_user("driver@example.test", "Demo Driver", Role.DRIVER)

        for user in (passenger, driver):
            verification, _ = Verification.objects.get_or_create(user=user)
            verification.status = VerificationStatus.VERIFIED
            verification.reviewed_by = admin
            verification.reviewed_at = timezone.now()
            verification.note = "Seeded demo decision"
            verification.save()

        profile, _ = DriverProfile.objects.get_or_create(user=driver)
        profile.licence_review_status = ApprovalStatus.APPROVED
        profile.approved_display_name = profile.approved_display_name or "Demo Driver"
        profile.save()

        route, _ = Route.objects.get_or_create(
            origin_name="Jibowu",
            destination_name="Mile 2",
            boarding_point="Jibowu bus terminal",
            destination_point="Mile 2 park",
            defaults={"is_active": True},
        )

        vehicle, _ = Vehicle.objects.get_or_create(
            plate_normalized="DEMO001",
            defaults={
                "driver": profile,
                "plate_display": "DEMO-001",
                "vehicle_type": "Toyota Hiace bus",
                "capacity": 4,
                "approval_status": ApprovalStatus.APPROVED,
            },
        )
        vehicle.approval_status = ApprovalStatus.APPROVED
        vehicle.save(update_fields=["approval_status"])

        now = timezone.now()
        if not Departure.objects.filter(
            driver=driver, status=DepartureStatus.BOARDING_OPEN, scheduled_departure_at__gt=now
        ).exists():
            Departure.objects.create(
                route=route,
                driver=driver,
                vehicle=vehicle,
                scheduled_departure_at=now + timedelta(hours=2),
                snapshot_capacity=vehicle.capacity,
                status=DepartureStatus.BOARDING_OPEN,
            )

        self.stdout.write(self.style.SUCCESS("Seeded synthetic demo data."))
        self.stdout.write(
            f"admin@example.test / passenger@example.test / driver@example.test — password: {DEMO_PASSWORD}"
        )

    def _ensure_user(self, email, display_name, role, staff=False, superuser=False):
        user = User.objects.filter(email=email).first()
        if user:
            return user
        if superuser:
            return User.objects.create_superuser(email, DEMO_PASSWORD, display_name=display_name, role=role)
        user = User.objects.create_user(email, DEMO_PASSWORD, display_name=display_name, role=role)
        if staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])
        return user
