from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.verification.models import VerificationStatus

User = get_user_model()


class AccountsAndVerificationTests(TestCase):
    def test_user_creation_and_default_verification_status(self):
        user = User.objects.create_user(
            username="testuser",
            email="Test.User@SafeRide.com",
            password="SecurePassword123!",
            display_name="Test User",
            role=User.Role.PASSENGER,
        )

        # 1. Email is normalized to lowercase
        self.assertEqual(user.email, "test.user@saferide.com")
        
        # 2. Default user is not staff
        self.assertFalse(user.is_staff)
        
        # 3. Post-save signal automatically creates NOT_SUBMITTED verification status
        self.assertEqual(
            user.verification_status.status,
            VerificationStatus.Status.NOT_SUBMITTED,
        )

    def test_duplicate_case_insensitive_email_fails(self):
        User.objects.create_user(
            username="rider1",
            email="rider@saferide.com",
            password="Password123!",
            display_name="Rider One",
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="rider2",
                email="RIDER@SAFERIDE.COM",
                password="Password456!",
                display_name="Rider Two",
            )
