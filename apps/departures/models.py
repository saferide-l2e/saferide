"""Scheduled departures and their lifecycle.

A departure snapshots the vehicle capacity so later edits to the vehicle cannot
retroactively change how many seats were promised on an already-published trip.
"""

import uuid

from django.conf import settings
from django.db import models


class DepartureStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    BOARDING_OPEN = "BOARDING_OPEN", "Boarding open"
    BOARDING_CLOSED = "BOARDING_CLOSED", "Boarding closed"
    EN_ROUTE = "EN_ROUTE", "En route"
    ARRIVED = "ARRIVED", "Arrived"
    CANCELLED = "CANCELLED", "Cancelled"


# Allowed forward transitions for the driver lifecycle.
ALLOWED_TRANSITIONS = {
    DepartureStatus.DRAFT: {DepartureStatus.BOARDING_OPEN, DepartureStatus.CANCELLED},
    DepartureStatus.BOARDING_OPEN: {DepartureStatus.BOARDING_CLOSED, DepartureStatus.CANCELLED},
    DepartureStatus.BOARDING_CLOSED: {DepartureStatus.EN_ROUTE, DepartureStatus.CANCELLED},
    DepartureStatus.EN_ROUTE: {DepartureStatus.ARRIVED, DepartureStatus.CANCELLED},
    DepartureStatus.ARRIVED: set(),
    DepartureStatus.CANCELLED: set(),
}

ACTIVE_STATUSES = (
    DepartureStatus.BOARDING_OPEN,
    DepartureStatus.BOARDING_CLOSED,
    DepartureStatus.EN_ROUTE,
)


class Departure(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(
        "routes.Route", on_delete=models.PROTECT, related_name="departures"
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="departures"
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle", on_delete=models.PROTECT, related_name="departures"
    )
    scheduled_departure_at = models.DateTimeField()
    snapshot_capacity = models.PositiveSmallIntegerField()
    walk_in_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16, choices=DepartureStatus.choices, default=DepartureStatus.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_departure_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(snapshot_capacity__gt=0), name="departure_capacity_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(walk_in_count__gte=0), name="departure_walkins_non_negative"
            ),
        ]
        indexes = [
            models.Index(
                fields=["route", "status", "scheduled_departure_at"],
                name="departure_route_status_idx",
            ),
            models.Index(fields=["driver", "status"]),
        ]

    def __str__(self):
        return f"{self.route} @ {self.scheduled_departure_at:%Y-%m-%d %H:%M} UTC"

    @property
    def is_active(self):
        return self.status in ACTIVE_STATUSES

    def can_transition_to(self, new_status):
        return new_status in ALLOWED_TRANSITIONS.get(self.status, set())
