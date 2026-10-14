"""Seat holds, the FIFO waitlist and single-use boarding credentials.

Capacity is an aggregate invariant enforced in locked service code, not by a
row CHECK. Partial unique indexes prevent a person holding or awaiting the same
departure twice at the same time.
"""

import uuid

from django.conf import settings
from django.db import models


class BookingStatus(models.TextChoices):
    HELD = "HELD", "Held"
    BOARDED = "BOARDED", "Boarded"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    EXPIRED = "EXPIRED", "Expired"
    DISPUTED = "DISPUTED", "Disputed"


class WaitlistStatus(models.TextChoices):
    WAITING = "WAITING", "Waiting"
    OFFERED = "OFFERED", "Offered"
    ACCEPTED = "ACCEPTED", "Accepted"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"
    INELIGIBLE = "INELIGIBLE", "Ineligible"


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    departure = models.ForeignKey(
        "departures.Departure", on_delete=models.PROTECT, related_name="bookings"
    )
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings"
    )
    status = models.CharField(
        max_length=16, choices=BookingStatus.choices, default=BookingStatus.HELD
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    driver_arrived_at = models.DateTimeField(null=True, blank=True)
    passenger_confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["departure", "passenger"],
                condition=models.Q(status__in=[BookingStatus.HELD, BookingStatus.BOARDED]),
                name="booking_unique_active_per_passenger",
            ),
        ]
        indexes = [
            models.Index(
                fields=["departure", "status", "expires_at"],
                name="booking_departure_status_idx",
            ),
            models.Index(fields=["passenger", "status"]),
        ]

    def __str__(self):
        return f"{self.passenger} · {self.get_status_display()} · {self.departure_id}"

    @property
    def is_hold_valid(self):
        from django.utils import timezone

        return (
            self.status == BookingStatus.HELD
            and self.expires_at is not None
            and self.expires_at > timezone.now()
        )


class WaitlistEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    departure = models.ForeignKey(
        "departures.Departure", on_delete=models.PROTECT, related_name="waitlist_entries"
    )
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="waitlist_entries"
    )
    status = models.CharField(
        max_length=16, choices=WaitlistStatus.choices, default=WaitlistStatus.WAITING
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    offered_at = models.DateTimeField(null=True, blank=True)
    offer_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["joined_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["departure", "passenger"],
                condition=models.Q(status__in=[WaitlistStatus.WAITING, WaitlistStatus.OFFERED]),
                name="waitlist_unique_active_per_passenger",
            ),
        ]
        indexes = [
            models.Index(
                fields=["departure", "status", "joined_at", "id"],
                name="waitlist_fifo_idx",
            ),
        ]

    def __str__(self):
        return f"{self.passenger} · {self.get_status_display()} · {self.departure_id}"

    @property
    def is_offer_valid(self):
        from django.utils import timezone

        return (
            self.status == WaitlistStatus.OFFERED
            and self.offer_expires_at is not None
            and self.offer_expires_at > timezone.now()
        )


class BoardingCredential(models.Model):
    """Salted single-use boarding code. The plaintext code is never stored."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="boarding_credential"
    )
    code_hash = models.CharField(max_length=128)
    issued_at = models.DateTimeField(auto_now_add=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Credential for {self.booking_id}"

    @property
    def is_usable(self):
        return self.consumed_at is None and self.revoked_at is None
