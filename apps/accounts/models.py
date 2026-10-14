"""Custom user model. Roles are PASSENGER/DRIVER; administrators are staff users.

Email is the login identifier. Public records use UUID primary keys and all
datetimes are UTC-aware (USE_TZ = True). No identity documents are ever stored
here — only synthetic demo accounts are allowed.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    PASSENGER = "PASSENGER", "Passenger"
    DRIVER = "DRIVER", "Driver"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.PASSENGER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.PASSENGER)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=80)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.PASSENGER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        ordering = ["display_name", "email"]

    def __str__(self):
        return self.display_name or self.email

    @property
    def is_passenger(self):
        return self.role == Role.PASSENGER

    @property
    def is_driver(self):
        return self.role == Role.DRIVER

    @property
    def verification_status(self):
        """Current demo verification status, or NOT_SUBMITTED when no row exists."""
        from apps.verification.models import VerificationStatus

        verification = getattr(self, "verification", None)
        return verification.status if verification else VerificationStatus.NOT_SUBMITTED

    @property
    def is_verified(self):
        from apps.verification.models import VerificationStatus

        return self.is_active and self.verification_status == VerificationStatus.VERIFIED

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email).lower()
