from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.bookings.models import Booking
from apps.departures.models import Departure
from apps.routes.models import Route
from apps.safety.models import IncidentReport, Review, RouteUpdate, TripReview
from apps.vehicles.models import ApprovalStatus, DriverProfile, Vehicle

User = get_user_model()


class SafetyModelConstraintTests(TestCase):
    def setUp(self):
        # Build synthetic base layers for testing boundaries
        self.user = User.objects.create_user(email="user@saferide.test", password="pass123")
        self.driver = User.objects.create_user(email="driver@saferide.test", password="pass123")

        profile, _ = DriverProfile.objects.get_or_create(user=self.driver)
        profile.licence_review_status = ApprovalStatus.APPROVED
        profile.save()

        self.vehicle = Vehicle.objects.create(
            driver=profile,
            plate_display="ABC-123",
            plate_normalized="ABC123",
            vehicle_type="Toyota Hiace",
            capacity=4,
            approval_status=ApprovalStatus.APPROVED,
        )

        self.route = Route.objects.create(
            origin_name="Jibowu",
            destination_name="Mile 2",
            boarding_point="Jibowu terminal",
            destination_point="Mile 2 park",
            is_active=True,
        )
        self.departure = Departure.objects.create(
            route=self.route,
            driver=self.driver,
            vehicle=self.vehicle,
            scheduled_departure_at=timezone.now(),
            snapshot_capacity=4,
        )
        self.booking = Booking.objects.create(
            passenger=self.user,
            departure=self.departure,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )

    def test_star_bounds_rejection(self):
        """Verify that 0-star and 6-star records fail field validator evaluations."""
        invalid_low_review = Review(booking=self.booking, author=self.user, stars=0, comment="Bad experience")
        with self.assertRaises(ValidationError):
            invalid_low_review.full_clean()

        invalid_high_review = Review(booking=self.booking, author=self.user, stars=6, comment="Perfect experience")
        with self.assertRaises(ValidationError):
            invalid_high_review.full_clean()

    def test_one_review_per_booking_enforcement(self):
        """Verify that creating two distinct reviews for a single booking raises an IntegrityError."""
        Review.objects.create(booking=self.booking, author=self.user, stars=4, comment="Good journey")

        # Second creation on identical booking raises IntegrityError
        with self.assertRaises(IntegrityError):
            Review.objects.create(booking=self.booking, author=self.user, stars=2, comment="Duplicated attempt")

    def test_default_pending_moderation_status(self):
        """Verify that IncidentReport and RouteUpdate default cleanly to PENDING status."""
        report = IncidentReport.objects.create(
            reporter=self.user,
            booking=self.booking,
            category="SAFETY",
            description="Private log details",
        )
        route_upd = RouteUpdate.objects.create(
            route=self.route,
            reporter=self.user,
            type="TRAFFIC",
            note="Delay notation",
            occurred_at=timezone.now(),
        )

        self.assertEqual(report.status, "PENDING")
        self.assertEqual(route_upd.status, "PENDING")

    def test_alias_compatibility_trip_review(self):
        """Verify TripReview alias works interchangeably with Review."""
        self.assertIs(TripReview, Review)
