"""Simulated demo verification status (KYC placeholder).

This is NOT real identity verification. No documents, licence numbers, addresses
or phone numbers are ever stored. Only a status transition record is kept.
"""

import uuid

from django.conf import settings
from django.db import models


class VerificationStatus(models.TextChoices):
    NOT_SUBMITTED = "NOT_SUBMITTED", "Not submitted"
    PENDING = "PENDING", "Pending review"
    VERIFIED = "VERIFIED", "Verified (demo)"
    REJECTED = "REJECTED", "Rejected"
    SUSPENDED = "SUSPENDED", "Suspended"


class Verification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification"
    )
    status = models.CharField(
        max_length=16, choices=VerificationStatus.choices, default=VerificationStatus.NOT_SUBMITTED
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verification_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=280, blank=True)

    class Meta:
        ordering = ["-submitted_at", "user__display_name"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.user} — {self.get_status_display()}"
