"""FE-08: booking hold is a rendering layer, not the inventory authority."""

from datetime import UTC, datetime, timedelta

from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class HoldFrontendTests(SimpleTestCase):
    server_now = datetime(2026, 10, 15, 10, 0, tzinfo=UTC)

    def booking(self, **changes):
        initial = {
            "status": "HELD",
            "reference": "BOOKING-TEST-001",
            "route_label": "Jibowu → Mile 2",
            "plate_display": "SRD-204",
            "boarding_point": "Jibowu Park",
            "expires_at": self.server_now + timedelta(seconds=600),
            "boarding_code": "482913",
        }
        initial.update(changes)
        return initial

    def render(self, data):
        request = RequestFactory().get("/bookings/my-hold/")
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(
            "booking/hold.html", data, request=request
        )

    def test_held_booking_uses_server_expiry_and_clock(self):
        html = self.render({
            "booking": self.booking(),
            "server_now": self.server_now,
            "status_url": "/bookings/my-hold/status/",
        })
        self.assertIn('data-booking-status="HELD"', html)
        self.assertIn('data-server-now="2026-10-15T10:00:00', html)
        self.assertIn('data-expires-at="2026-10-15T10:10:00', html)
        self.assertIn("482913", html)
        self.assertIn("Time remaining to check in", html)
        self.assertIn('data-status-url="/bookings/my-hold/status/"', html)

    def test_cancel_is_post_and_csrf_guarded_only_when_provided(self):
        html = self.render({
            "booking": self.booking(),
            "server_now": self.server_now,
            "cancel_action": "/bookings/my-hold/cancel/",
        })
        self.assertIn('action="/bookings/my-hold/cancel/"', html)
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn("Cancel my reservation", html)

        cannot_cancel = self.render({"booking": self.booking()})
        self.assertNotIn('action="/bookings/my-hold/cancel/"', cannot_cancel)

    def test_expired_or_cancelled_booking_does_not_show_code(self):
        for status in ("EXPIRED", "CANCELLED", "BOARDED"):
            with self.subTest(status=status):
                html = self.render({
                    "booking": self.booking(status=status),
                    "server_now": self.server_now,
                    "cancel_action": "/bookings/my-hold/cancel/",
                })
                self.assertNotIn("482913", html)
                self.assertNotIn('method="post"', html)
                self.assertIn(status, html)

    def test_not_found_or_error_shows_clear_message(self):
        missing = self.render({"booking": None})
        self.assertIn("We couldn't find this reservation.", missing)
        failed = self.render({
            "booking": self.booking(),
            "error_message": "<script>Something went wrong</script>",
        })
        self.assertIn("Booking update unsuccessful.", failed)
        self.assertNotIn("<script>Something went wrong</script>", failed)
        self.assertIn("&lt;script&gt;", failed)
