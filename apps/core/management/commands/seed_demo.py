"""Create synthetic demo data (DB-08).

Everything here is fictional. Safe to run repeatedly: existing rows are reused.
"""

import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from apps.accounts.models import Role, User
from apps.departures.models import Departure, DepartureStatus
from apps.routes.models import Route
from apps.vehicles.models import ApprovalStatus, DriverProfile, Vehicle
from apps.verification.models import Verification, VerificationStatus
from apps.safety.models import IncidentCategory, IncidentReport, IncidentStatus

DEMO_PASSWORD = "saferide-demo-123"


class Command(BaseCommand):
    help = "Create fictional demo accounts, a route, a vehicle, and a departure."

    def add_arguments(self, parser):
        # Adding the mandatory explicit opt-in argument required by DB-08
        parser.add_argument(
            '--reset-safe-demo',
            action='store_true',
            help='Explicit opt-in required to execute the seeding logic.',
        )

    def handle(self, *args, **options):
        # 1. Production Safeguard block check
        if not settings.DEBUG and not getattr(settings, 'ALLOW_PRODUCTION_DEMO_SEED', False):
            raise CommandError(
                "Execution Refused: Seeding is blocked in production environments "
                "unless ALLOW_PRODUCTION_DEMO_SEED is explicitly set to True."
            )

        # 2. Check for the safety argument flag
        if not options.get('reset_safe_demo'):
            raise CommandError("You must provide the --reset-safe-demo flag to run this command.")

        self.stdout.write("Starting idempotent demo seeding execution...")

        with transaction.atomic():
            # --- USERS ---
            admin = self._ensure_user(
                "admin@example.test", "Demo Admin", Role.PASSENGER, staff=True, superuser=True
            )
            
            # Passengers: Two verified, one pending
            passenger_1 = self._ensure_user("passenger@example.test", "Demo Passenger 1", Role.PASSENGER)
            passenger_2 = self._ensure_user("passenger2@example.test", "Demo Passenger 2", Role.PASSENGER)
            passenger_pending = self._ensure_user("pending@example.test", "Pending Passenger", Role.PASSENGER)
            
            driver = self._ensure_user("driver@example.test", "Demo Driver", Role.DRIVER)

            # Mark users as verified
            for user in (passenger_1, passenger_2, driver):
                verification, _ = Verification.objects.get_or_create(user=user)
                verification.status = VerificationStatus.VERIFIED
                verification.reviewed_by = admin
                verification.reviewed_at = timezone.now()
                verification.note = "Seeded demo decision"
                verification.save()

            # Ensure the pending passenger has an unverified state
            verification_p, _ = Verification.objects.get_or_create(user=passenger_pending)
            verification_p.status = VerificationStatus.PENDING
            verification_p.save()

            # --- DRIVER PROFILE ---
            profile, _ = DriverProfile.objects.get_or_create(user=driver)
            profile.licence_review_status = ApprovalStatus.APPROVED
            profile.approved_display_name = profile.approved_display_name or "Demo Driver"
            profile.save()

            # --- ROUTE ---
            route, _ = Route.objects.get_or_create(
                origin_name="Jibowu",
                destination_name="Mile 2",
                boarding_point="Jibowu bus terminal",
                destination_point="Mile 2 park",
                defaults={"is_active": True},
            )

            # --- VEHICLE (Updated capacity to exactly 1 seat as requested) ---
            vehicle, _ = Vehicle.objects.get_or_create(
                plate_normalized="DEMO001",
                defaults={
                    "driver": profile,
                    "plate_display": "DEMO-001",
                    "vehicle_type": "Toyota Hiace bus",
                    "capacity": 1,  # Strict DB-08 constraint: 1-seat bus
                    "approval_status": ApprovalStatus.APPROVED,
                },
            )
            vehicle.capacity = 1
            vehicle.approval_status = ApprovalStatus.APPROVED
            vehicle.save(update_fields=["capacity", "approval_status"])

            # --- DEPARTURE (Fixed time to Friday 16 October 2026) ---
            demo_departure_time = timezone.make_aware(
                datetime.datetime(2026, 10, 16, 8, 0, 0)
            )

            departure, created = Departure.objects.get_or_create(
                route=route,
                driver=driver,
                scheduled_departure_at=demo_departure_time,
                defaults={
                    "vehicle": vehicle,
                    "snapshot_capacity": vehicle.capacity,
                    "status": DepartureStatus.BOARDING_OPEN,
                }
            )

            # --- PENDING DEMO REPORT ---
            IncidentReport.objects.get_or_create(
                reporter=passenger_1,
                defaults={
                    "category": IncidentCategory.SAFETY,
                    "description": "Fictional demo delay event notation.",
                    "status": IncidentStatus.PENDING,
                }
            )

        self.stdout.write(self.style.SUCCESS("Seeded synthetic demo data successfully without duplicates."))

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
