"""Post-trip reviews, private misconduct reports and moderated route updates.

Allegations are never published automatically. Only APPROVED route updates are
shown publicly, and they carry timestamps and a demo-data badge.
"""

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class IncidentCategory(models.TextChoices):
    SAFETY = "SAFETY", "Safety concern"
    CONDUCT = "CONDUCT", "Conduct"
    VEHICLE = "VEHICLE", "Vehicle condition"
    OTHER = "OTHER", "Other"


class IncidentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending review"
    IN_REVIEW = "IN_REVIEW", "Under active review"
    REVIEWED = "REVIEWED", "Reviewed"
    RESOLVED = "RESOLVED", "Resolved"
    DISMISSED = "DISMISSED", "Dismissed"


class RouteUpdateType(models.TextChoices):
    TRAFFIC = "TRAFFIC", "Traffic"
    SAFETY = "SAFETY", "Safety"


class RouteUpdateStatus(models.TextChoices):
    PENDING = "PENDING", "Pending review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class Review(models.Model):
    """DB-06: Feedback system for completed trips.

    Enforces exactly one review per booking and stars bounded 1..5.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.PROTECT,
        related_name="review",
        help_text="The exact trip booking instance being reviewed.",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviews_written",
    )
    stars = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, message="Stars must be at least 1."),
            MaxValueValidator(5, message="Stars cannot exceed 5."),
        ],
        help_text="Rating given from 1 to 5 stars.",
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stars__gte=1) & models.Q(stars__lte=5),
                name="review_stars_1_to_5",
            )
        ]

    def __str__(self):
        return f"{self.stars}★ by {self.author}"


# Backward compatibility alias for DB-06 specification
TripReview = Review


class IncidentReport(models.Model):
    """DB-06: Private operational safety incident logger.

    Survives user deactivation/deletion and keeps contents strictly unpublished.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        "bookings.Booking",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="incident_reports",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="incidents_filed",
        help_text="The person filing the complaint. Kept safely as legal evidence.",
    )
    subject = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incidents_about",
    )
    category = models.CharField(max_length=50)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=IncidentStatus.choices,
        default=IncidentStatus.PENDING,
        help_text="Moderation lifecycle checkpoint stage.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incidents_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self):
        return f"{self.category} report ({self.get_status_display()})"

    @property
    def reported_by(self):
        return self.reporter

    @reported_by.setter
    def reported_by(self, value):
        self.reporter = value

    @property
    def private_narrative(self):
        return self.description

    @private_narrative.setter
    def private_narrative(self, value):
        self.description = value


class RouteUpdate(models.Model):
    """DB-06: Moderated lifecycle tracking for route events."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey("routes.Route", on_delete=models.PROTECT, related_name="updates")
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="route_updates",
    )
    type = models.CharField(max_length=16, choices=RouteUpdateType.choices)
    note = models.TextField()
    occurred_at = models.DateTimeField(help_text="The point in time when the physical event occurred on-road.")
    status = models.CharField(
        max_length=16,
        choices=RouteUpdateStatus.choices,
        default=RouteUpdateStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="route_updates_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(
                fields=["route", "status", "-occurred_at"],
                name="safety_rt_stat_occ_idx",
            ),
            models.Index(fields=["route", "status", "occurred_at"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()} update on {self.route}"

    @property
    def author(self):
        return self.reporter

    @author.setter
    def author(self, value):
        self.reporter = value

    @property
    def update_type(self):
        return self.type

    @update_type.setter
    def update_type(self, value):
        self.type = value

    @property
    def event_timestamp(self):
        return self.occurred_at

    @event_timestamp.setter
    def event_timestamp(self, value):
        self.occurred_at = value
