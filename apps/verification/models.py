from typing import ClassVar

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class VerificationStatus(models.Model):
    class Status(models.TextChoices):
        NOT_SUBMITTED = "NOT_SUBMITTED", "Not Submitted"
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_status",
        primary_key=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_SUBMITTED,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews_conducted",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.status}"


# Automatic trigger: Whenever a new User is created, create their default verification record
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_verification_status(sender, instance, created, **kwargs):
    if created:
        VerificationStatus.objects.create(user=instance)
