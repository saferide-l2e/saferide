"""FE-10: driver-side boarding UI tests without unmerged BE-08 views."""

from datetime import UTC, datetime

from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class DriverBoardingFrontendTests(SimpleTestCase):
    def render(self, path, context):
        request = RequestFactory().get("/driver/boarding/")
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(path, context, request=request)

    def test_private_roster_uses_minimal_public_fields(self):
        passenger = {
            "short_reference": "SR-4872",
            "public_display_name": "Tomi A.",
            "initials": "TA",
            "status": "HELD",
            "verified": True,
            "expires_at": datetime(2026, 10, 15, 11, 30, tzinfo=UTC),
            "email": "secret.email@example.com",
            "phone": "08012345678",
            "licence_scan": "PRIVATE-SCAN",
        }
        html = self.render("driver/roster.html", {
            "departure": {"route_label": "Jibowu → Mile 2"},
            "roster": [passenger],
            "boarded_count": 0,
            "held_count": 1,
            "capacity": 12,
        })
        self.assertIn("Tomi A.", html)
        self.assertIn("SR-4872", html)
        self.assertIn("Profile approved", html)
        self.assertIn("HELD", html)
        self.assertNotIn("secret.email@example.com", html)
        self.assertNotIn("08012345678", html)
        self.assertNotIn("PRIVATE-SCAN", html)

    def test_eligible_code_submission_is_csrf_protected(self):
        html = self.render("driver/check_in.html", {
            "departure": {
                "route_label": "Jibowu → Mile 2",
                "vehicle_plate": "SRD-204",
            },
            "can_check_in": True,
            "checkin_action": "/driver/check-in/",
        })
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('name="boarding_code"', html)
        self.assertIn('pattern="[0-9]{6}"', html)
        self.assertIn('action="/driver/check-in/"', html)

    def test_no_permission_means_no_boarding_form(self):
        html = self.render("driver/check_in.html", {
            "can_check_in": False,
            "checkin_action": "/driver/check-in/",
            "action_message": "Not assigned to this vehicle.",
        })
        self.assertNotIn('action="/driver/check-in/"', html)
        self.assertIn("Not assigned to this vehicle.", html)

    def test_error_is_escaped_and_roster_empty_state_exists(self):
        html = self.render("driver/check_in.html", {
            "error_message": "<script>unsafe</script>",
        })
        self.assertNotIn("<script>unsafe</script>", html)
        self.assertIn("&lt;script&gt;", html)
        empty = self.render("driver/roster.html", {"roster": []})
        self.assertIn("No passengers listed yet.", empty)

    def test_departure_close_is_csrf_post_only_if_allowed(self):
        html = self.render("driver/roster.html", {
            "can_advance": True,
            "advance_action": "/driver/close-boarding/",
        })
        self.assertIn('action="/driver/close-boarding/"', html)
        self.assertIn('method="post"', html)
        no_access = self.render("driver/roster.html", {
            "can_advance": False,
            "advance_action": "/driver/close-boarding/",
        })
        self.assertNotIn('action="/driver/close-boarding/"', no_access)
