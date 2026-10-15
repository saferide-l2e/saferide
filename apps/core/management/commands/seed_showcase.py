"""Load synthetic, clearly labelled showcase identities and route for a short pitch.

Never import real users, scan identity documents or bypass approval of signups.
This management command must be explicitly enabled by the service operator.
"""
import os
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.departures.models import Departure, DepartureStatus
from apps.routes.models import Route
from apps.vehicles.models import ApprovalStatus, DriverProfile, Vehicle
from apps.verification.models import Verification, VerificationStatus


class Command(BaseCommand):
    help = "Seed two fictional pilot accounts and approved synthetic bus route for presentation."

    @transaction.atomic
    def handle(self, *args, **options):
        if os.getenv("SAFERIDE_SEED_SAMPLE_DATA", "").lower() != "true":
            raise CommandError("Set SAFERIDE_SEED_SAMPLE_DATA=true to use this command.")

        def sample_user(prefix, role, display):
            email = os.getenv(f"SAFERIDE_SAMPLE_{prefix}_EMAIL", "").strip().lower()
            password = os.getenv(f"SAFERIDE_SAMPLE_{prefix}_PASSWORD", "")
            if not email or len(password) < 12:
                raise CommandError(f"Provide a unique {prefix} email and 12+ character password.")
            user = User.objects.filter(email=email).first()
            if user and user.role != role:
                raise CommandError(f"Existing {prefix} email belongs to a different role.")
            if not user:
                user = User.objects.create_user(
                    email=email, password=password, display_name=display, role=role,
                )
                Verification.objects.get_or_create(
                    user=user, defaults={"status": VerificationStatus.VERIFIED,
                                         "note": "Synthetic pilot identity; no actual identity check"},
                )
            # Never overwrite the existing user's password or verification decisions.
            return user

        driver = sample_user("DRIVER", Role.DRIVER, "Amina O. (Sample)")
        sample_user("PASSENGER", Role.PASSENGER, "Tomi A. (Sample)")
        profile, _ = DriverProfile.objects.get_or_create(
            user=driver,
            defaults={"approved_display_name": "Amina O. (Sample)",
                      "licence_review_status": ApprovalStatus.APPROVED},
        )
        vehicle, _ = Vehicle.objects.get_or_create(
            plate_normalized="SRD026DEMO",
            defaults={"driver": profile, "plate_display": "SRD-026-DEMO",
                      "vehicle_type": "Minibus (fictional)", "capacity": 14,
                      "approval_status": ApprovalStatus.APPROVED},
        )
        route, _ = Route.objects.get_or_create(
            origin_name="Jibowu", destination_name="Mile 2",
            boarding_point="Jibowu Park (fictional)",
            defaults={"destination_point": "Mile 2 Stop (fictional)"},
        )
        if not Departure.objects.filter(
            driver=driver, route=route, vehicle=vehicle,
            status=DepartureStatus.BOARDING_OPEN,
            scheduled_departure_at__gt=timezone.now() + timedelta(minutes=20),
        ).exists():
            # Standalone walk-through journey; opening occurs via the seed command
            # rather than the driver's normal create->staff approval->publish route.
            Departure.objects.create(
                driver=driver, route=route, vehicle=vehicle,
                scheduled_departure_at=timezone.now() + timedelta(hours=4),
                status=DepartureStatus.BOARDING_OPEN, snapshot_capacity=vehicle.capacity,
            )
        self.stdout.write(self.style.SUCCESS(
            "Synthetic SafeRide account and route data present (no passwords printed)."
        ))
