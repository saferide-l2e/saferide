"""Append-only audit trail of important actions.

Metadata must be redacted: never store passwords, KYC documents, one-time codes
or contact details here.
"""

import uuid

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import models


class AuditEvent(models.Model):
    """DB-07 Audit Event tracking database table.

    Enforces append-only constraints and strict staff-only visibility rules.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
        help_text="The staff member or system actor executing the change.",
    )
    action = models.CharField(max_length=64)
    object_type = models.CharField(max_length=64, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action}"

    def save(self, *args, **kwargs):
        # Enforce append-only constraint: cannot update existing rows
        if not self._state.adding:
            raise PermissionDenied("Audit entries are append-only and cannot be altered or modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Enforce permanent records constraint: cannot delete audit entries
        raise PermissionDenied("Audit logs are permanent records and cannot be deleted.")
