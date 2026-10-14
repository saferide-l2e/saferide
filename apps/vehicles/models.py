import re
import uuid
from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def normalize_plate(value):
    """Return the case- and separator-insensitive form used for uniqueness."""
    return re.sub(r"[^A-Z0-9]", "", value.upper())


class DriverProfile(models.Model):
    class LicenceStatus(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_profile",
    )
    public_display_name = models.CharField(max_length=150, blank=True)
    licence_status = models.CharField(
        max_length=20,
        choices=LicenceStatus.choices,
        default=LicenceStatus.PENDING,
    )

    class Meta:
        indexes: ClassVar[list] = [models.Index(fields=["licence_status"])]

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != "DRIVER":
            raise ValidationError({"user": "A driver profile requires a DRIVER account."})

    @property
    def safe_display_name(self):
        return self.public_display_name.strip() or self.user.display_name

    def __str__(self):
        return self.safe_display_name


class Vehicle(models.Model):
    class VehicleType(models.TextChoices):
        BUS = "BUS", "Bus"
        MINIBUS = "MINIBUS", "Minibus"

    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.PROTECT,
        related_name="vehicles",
        db_index=False,
    )
    plate_display = models.CharField(max_length=20)
    plate_normalized = models.CharField(max_length=20, unique=True, editable=False)
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices)
    seat_capacity = models.PositiveIntegerField()
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )

    class Meta:
        constraints: ClassVar[list] = [
            models.CheckConstraint(
                condition=Q(seat_capacity__gt=0),
                name="vehicle_seat_capacity_positive",
            ),
        ]
        indexes: ClassVar[list] = [
            models.Index(fields=["driver"], name="vehicle_driver_idx"),
            models.Index(fields=["approval_status"], name="vehicle_approval_idx"),
        ]

    def save(self, *args, **kwargs):
        self.plate_display = self.plate_display.strip()
        self.plate_normalized = normalize_plate(self.plate_display)
        if not self.plate_normalized:
            raise ValidationError({"plate_display": "Enter a plate with at least one letter or number."})
        super().save(*args, **kwargs)

    @property
    def safe_display(self):
        return f"{self.get_vehicle_type_display()} · {self.plate_display} · {self.seat_capacity} seats"

    def __str__(self):
        return self.safe_display
