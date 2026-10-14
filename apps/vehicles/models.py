"""Driver profiles and their vehicles.

Only approved display fields are kept: no licences, ID numbers or documents.
Plates used in the demo are synthetic.
"""

import re
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class ApprovalStatus(models.TextChoices):
    PENDING = "PENDING", "Pending review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    SUSPENDED = "SUSPENDED", "Suspended"


def normalize_plate(value):
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


class DriverProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="driver_profile"
    )
    approved_display_name = models.CharField(max_length=80, blank=True)
    licence_review_status = models.CharField(
        max_length=16, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    bio = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["approved_display_name"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.approved_display_name or self.user.display_name

    @property
    def is_approved(self):
        return self.licence_review_status == ApprovalStatus.APPROVED

    def save(self, *args, **kwargs):
        if not self.approved_display_name:
            self.approved_display_name = self.user.display_name
        super().save(*args, **kwargs)


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(DriverProfile, on_delete=models.PROTECT, related_name="vehicles")
    plate_normalized = models.CharField(max_length=16, unique=True)
    plate_display = models.CharField(max_length=16)
    vehicle_type = models.CharField(max_length=40)
    capacity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    approval_status = models.CharField(
        max_length=16, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["plate_display"]
        constraints = [
            models.CheckConstraint(condition=models.Q(capacity__gt=0), name="vehicle_capacity_positive"),
        ]

    def __str__(self):
        return f"{self.plate_display} ({self.vehicle_type})"

    @property
    def is_approved(self):
        return self.approval_status == ApprovalStatus.APPROVED

    def save(self, *args, **kwargs):
        self.plate_normalized = normalize_plate(self.plate_display)
        super().save(*args, **kwargs)
