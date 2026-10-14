"""Post-trip reviews, private misconduct reports and moderated route updates.

Allegations are never published automatically. Only APPROVED route updates are
shown publicly, and they carry timestamps and a demo-data badge.
"""

import uuid

from django.conf import settings
from django.db import models


class IncidentCategory(models.TextChoices):
    SAFETY = "SAFETY", "Safety concern"
    CONDUCT = "CONDUCT", "Conduct"
    VEHICLE = "VEHICLE", "Vehicle condition"
    OTHER = "OTHER", "Other"


class IncidentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending review"
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        "bookings.Booking", on_delete=models.PROTECT, related_name="review"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reviews_written"
    )
    stars = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stars__gte=1) & models.Q(stars__lte=5), name="review_stars_1_to_5"
            )
        ]

    def __str__(self):
        return f"{self.stars}★ by {self.author}"


class IncidentReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        "bookings.Booking",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="incident_reports",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="incidents_filed"
    )
    subject = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incidents_about",
    )
    category = models.CharField(max_length=16, choices=IncidentCategory.choices)
    description = models.TextField()
    status = models.CharField(
        max_length=16, choices=IncidentStatus.choices, default=IncidentStatus.PENDING
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
        return f"{self.get_category_display()} report ({self.get_status_display()})"


class RouteUpdate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(
        "routes.Route", on_delete=models.PROTECT, related_name="updates"
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="route_updates"
    )
    type = models.CharField(max_length=16, choices=RouteUpdateType.choices)
    note = models.TextField()
    occurred_at = models.DateTimeField()
    status = models.CharField(
        max_length=16, choices=RouteUpdateStatus.choices, default=RouteUpdateStatus.PENDING
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
        indexes = [models.Index(fields=["route", "status", "occurred_at"])]

    def __str__(self):
        return f"{self.get_type_display()} update on {self.route}"
