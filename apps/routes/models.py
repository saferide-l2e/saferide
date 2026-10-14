"""Bus routes searchable by passengers.

Demo routes are synthetic. The pilot route is Jibowu -> Mile 2.
"""

import uuid

from django.db import models


class Route(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origin_name = models.CharField(max_length=80)
    destination_name = models.CharField(max_length=80)
    boarding_point = models.CharField(max_length=120)
    destination_point = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["origin_name", "destination_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["origin_name", "destination_name", "boarding_point"],
                name="route_unique_origin_destination_boarding",
            )
        ]
        indexes = [models.Index(fields=["origin_name", "destination_name"])]

    def __str__(self):
        return f"{self.origin_name} → {self.destination_name}"

    @property
    def label(self):
        return f"{self.origin_name} → {self.destination_name}"
