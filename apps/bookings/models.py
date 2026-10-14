import uuid
from typing import ClassVar

from django.db import models
from django.db.models import Q

from apps.accounts.models import User
from apps.departures.models import Departure


class Booking(models.Model):
    class Status(models.TextChoices):
        HELD = "HELD", "Held"
        BOARDED = "BOARDED", "Boarded"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"
        DISPUTED = "DISPUTED", "Disputed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    departure = models.ForeignKey(
        Departure,
        on_delete=models.PROTECT,
        related_name="bookings",
        db_index=False,
    )
    passenger = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.HELD,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    checked_in_at = models.DateTimeField(null=True, blank=True)
    driver_arrived_at = models.DateTimeField(null=True, blank=True)
    passenger_confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["departure", "passenger"],
                condition=Q(status__in=["HELD", "BOARDED"]),
                name="booking_one_active_seat",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "HELD",
                        "BOARDED",
                        "COMPLETED",
                        "CANCELLED",
                        "EXPIRED",
                        "DISPUTED",
                    ]
                ),
                name="booking_status_valid",
            ),
        ]
        indexes: ClassVar[list] = [
            models.Index(
                fields=["departure", "status", "expires_at"],
                name="booking_dep_status_exp_idx",
            ),
        ]

    def __str__(self):
        return f"Booking {self.pk} ({self.status})"


class BoardingCredential(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.PROTECT,
        related_name="boarding_credential",
    )
    code_digest = models.CharField(max_length=128, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Boarding credential for booking {self.booking_id}"
