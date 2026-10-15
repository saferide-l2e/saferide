from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from apps.audit.admin import AuditEventAdmin
from apps.audit.models import AuditEvent
from apps.audit.services import record_audit_event

User = get_user_model()


class AuditSecurityEnforcementTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(email="staff@saferide.test", password="password123", is_staff=True)
        self.regular_user = User.objects.create_user(
            email="passenger@saferide.test", password="password123", is_staff=False
        )

    def test_event_metadata_scrub(self):
        """Verify that forbidden sensitive records are automatically scrubbed out."""
        raw_data = {
            "booking_reference": "BK-9942",
            "password": "supersecretpassword",
            "licence_number": "AG-45124-XYZ",
            "complaint_narrative": "Detailed user description about route layout problems.",
        }

        event = record_audit_event(
            actor=self.staff_user,
            action="VERIFICATION_APPROVAL",
            object_type="Booking",
            object_id="12345",
            raw_metadata=raw_data,
        )

        # Assert clean public variables remain untouched
        self.assertEqual(event.metadata["booking_reference"], "BK-9942")

        # Assert structural safety targets are cleanly blacked out
        self.assertEqual(event.metadata["password"], "[REDACTED]")
        self.assertEqual(event.metadata["licence_number"], "[REDACTED]")
        self.assertEqual(event.metadata["complaint_narrative"], "[REDACTED]")

    def test_audit_records_are_append_only(self):
        """Verify that editing or deleting log objects is strictly rejected."""
        event = record_audit_event(actor=self.staff_user, action="CHECK_IN", object_type="Passenger", object_id="77")

        # Attempt to change action field and save update
        event.action = "MALICIOUS_TAMPERING"
        with self.assertRaises(PermissionDenied):
            event.save()

        # Attempt to remove transaction footprint history
        with self.assertRaises(PermissionDenied):
            event.delete()

    def test_non_staff_admin_access_denied(self):
        """Verify that regular non-staff users cannot view audit logs in admin."""
        factory = RequestFactory()
        admin_instance = AuditEventAdmin(AuditEvent, None)

        # Regular passenger request
        req = factory.get("/admin/audit/auditevent/")
        req.user = self.regular_user
        self.assertFalse(admin_instance.has_module_permission(req))
        self.assertFalse(admin_instance.has_view_permission(req))

        # Staff user request
        req_staff = factory.get("/admin/audit/auditevent/")
        req_staff.user = self.staff_user
        self.assertTrue(admin_instance.has_module_permission(req_staff))
        self.assertTrue(admin_instance.has_view_permission(req_staff))

        # Immutability in admin interface
        self.assertFalse(admin_instance.has_add_permission(req_staff))
        self.assertFalse(admin_instance.has_change_permission(req_staff))
        self.assertFalse(admin_instance.has_delete_permission(req_staff))
