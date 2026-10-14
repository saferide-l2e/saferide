import uuid
from typing import ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.routes.models import Route
from apps.vehicles.models import DriverProfile, Vehicle


class Departure(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        BOARDING_OPEN = "BOARDING_OPEN", "Boarding open"
        BOARDING_CLOSED = "BOARDING_CLOSED", "Boarding closed"
        EN_ROUTE = "EN_ROUTE", "En route"
        ARRIVED = "ARRIVED", "Arrived"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(
        Route,
        on_delete=models.PROTECT,
        related_name="departures",
        db_index=False,
    )
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.PROTECT,
        related_name="departures",
        db_index=False,
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="departures",
    )
    scheduled_departure_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    capacity_snapshot = models.PositiveIntegerField()
    walk_in_count = models.IntegerField(default=0)

    class Meta:
        constraints: ClassVar[list] = [
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "DRAFT",
                        "BOARDING_OPEN",
                        "BOARDING_CLOSED",
                        "EN_ROUTE",
                        "ARRIVED",
                        "CANCELLED",
                    ]
                ),
                name="departure_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(capacity_snapshot__gt=0),
                name="departure_capacity_positive",
            ),
            models.CheckConstraint(
                condition=Q(walk_in_count__gte=0),
                name="departure_walk_ins_nonnegative",
            ),
        ]
        indexes: ClassVar[list] = [
            models.Index(
                fields=["route", "status", "scheduled_departure_at"],
                name="departure_route_status_idx",
            ),
            models.Index(fields=["driver", "status"], name="departure_driver_status_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            old_capacity = type(self).objects.values_list(
                "capacity_snapshot", flat=True
            ).get(pk=self.pk)
            if self.capacity_snapshot != old_capacity:
                raise ValidationError("A departure capacity snapshot cannot be changed.")
        super().save(*args, **kwargs)

    @property
    def safe_display(self):
        return f"{self.route.display_label} · {self.scheduled_departure_at.isoformat()}"

    def __str__(self):
        return self.safe_display
