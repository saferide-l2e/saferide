import uuid
from typing import ClassVar

from django.db import models
from django.db.models import F, Q
from django.utils import timezone

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


class WaitlistEntryQuerySet(models.QuerySet):
    def fifo(self):
        return self.order_by("joined_at", "id")

    def allocated_offers(self, *, at=None):
        at = at or timezone.now()
        return self.filter(status="OFFERED", offer_expires_at__gt=at)

    def allocated_offer_count(self, *, at=None):
        return self.allocated_offers(at=at).count()


class WaitlistEntry(models.Model):
    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        OFFERED = "OFFERED", "Offer sent"
        ACCEPTED = "ACCEPTED", "Accepted"
        EXPIRED = "EXPIRED", "Expired"
        CANCELLED = "CANCELLED", "Cancelled"
        INELIGIBLE = "INELIGIBLE", "Ineligible"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    departure = models.ForeignKey(
        Departure,
        on_delete=models.PROTECT,
        related_name="waitlist_entries",
        db_index=False,
    )
    passenger = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="waitlist_entries",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
    )
    offered_at = models.DateTimeField(null=True, blank=True)
    offer_expires_at = models.DateTimeField(null=True, blank=True)
    accepted_booking = models.OneToOneField(
        Booking,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="accepted_waitlist_entry",
    )

    objects = WaitlistEntryQuerySet.as_manager()

    class Meta:
        ordering = ("joined_at", "id")
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["departure", "passenger"],
                condition=Q(status__in=["WAITING", "OFFERED"]),
                name="waitlist_one_active_entry",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "WAITING",
                        "OFFERED",
                        "ACCEPTED",
                        "EXPIRED",
                        "CANCELLED",
                        "INELIGIBLE",
                    ]
                ),
                name="waitlist_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(status="OFFERED")
                    | Q(
                        offered_at__isnull=False,
                        offer_expires_at__gt=F("offered_at"),
                    )
                ),
                name="waitlist_offer_timestamps_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="ACCEPTED", accepted_booking__isnull=False)
                    | (~Q(status="ACCEPTED") & Q(accepted_booking__isnull=True))
                ),
                name="waitlist_accepted_booking_valid",
            ),
        ]
        indexes: ClassVar[list] = [
            models.Index(
                fields=["departure", "status", "joined_at", "id"],
                name="waitlist_dep_status_fifo_idx",
            ),
        ]

    def __str__(self):
        return f"Waitlist entry {self.pk} ({self.status})"
