"""FE-09: no browser-generated queue spots or offers; template-only tests."""

from datetime import UTC, datetime, timedelta

from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class WaitlistTemplateTests(SimpleTestCase):
    server_now = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

    def render(self, name, context):
        request = RequestFactory().get("/bookings/waitlist/")
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(name, context, request=request)

    def test_waiting_position_is_from_the_server_context(self):
        html = self.render("booking/waitlist.html", {
            "entry": {
                "status": "WAITING",
                "position": 4,
                "people_ahead": 3,
                "route_label": "Jibowu → Mile 2",
            },
            "status_url": "/bookings/waitlist/status/",
        })
        self.assertIn("#4", html)
        self.assertIn("3 passengers ahead", html)
        self.assertIn("may change", html)
        self.assertIn('data-status-url="/bookings/waitlist/status/"', html)

    def test_join_and_leave_forms_use_csrf_post(self):
        join = self.render("booking/waitlist.html", {
            "can_join": True,
            "join_action": "/bookings/join/",
        })
        self.assertIn('action="/bookings/join/"', join)
        self.assertIn('name="csrfmiddlewaretoken"', join)
        self.assertIn('method="post"', join)

        leave = self.render("booking/waitlist.html", {
            "entry": {
                "status": "WAITING",
                "position": 1,
                "route_label": "Jibowu → Mile 2",
            },
            "leave_action": "/bookings/leave/",
        })
        self.assertIn('action="/bookings/leave/"', leave)
        self.assertIn("Leave waitlist", leave)

    def test_active_offer_has_exact_server_deadline_and_post_actions(self):
        html = self.render("booking/offer.html", {
            "offer": {
                "status": "OFFERED",
                "route_label": "Jibowu → Mile 2",
                "expires_at": self.server_now + timedelta(seconds=120),
            },
            "server_now": self.server_now,
            "accept_action": "/bookings/offer/accept/",
            "decline_action": "/bookings/offer/decline/",
        })
        self.assertIn('data-server-now="2026-10-15T12:00:00', html)
        self.assertIn('data-offer-expires="2026-10-15T12:02:00', html)
        self.assertIn("Accept this seat", html)
        self.assertIn("Decline offer", html)
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_expired_offer_has_no_post_action(self):
        html = self.render("booking/offer.html", {
            "offer": {"status": "EXPIRED", "route_label": "Jibowu → Mile 2"},
            "accept_action": "/bookings/offer/accept/",
        })
        self.assertNotIn('action="/bookings/offer/accept/"', html)
        self.assertIn("EXPIRED", html)

    def test_error_message_is_escaped(self):
        html = self.render("booking/waitlist.html", {
            "error_message": "<script>malicious</script>",
        })
        self.assertNotIn("<script>malicious</script>", html)
        self.assertIn("&lt;script&gt;", html)
