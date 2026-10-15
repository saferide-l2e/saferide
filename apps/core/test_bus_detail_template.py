"""FE-07: passenger-visible bus details without BE-04/BE-05 dependencies."""

from datetime import UTC, datetime

from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class BusDetailTemplateTests(SimpleTestCase):
    def render(self, context):
        request = RequestFactory().get("/buses/one-bus/")
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(
            "passenger/bus_detail.html", context, request=request
        )

    def bus(self, **overrides):
        data = {
            "route_label": "Jibowu → Mile 2",
            "scheduled_departure_at": datetime(2026, 10, 15, 11, 30, tzinfo=UTC),
            "boarding_point": "Jibowu Park",
            "destination_point": "Mile 2 terminal",
            "vehicle_type_display": "Minibus",
            "plate_display": "SRD-204",
            "driver_public_name": "Amina O.",
            "driver_initials": "AO",
            "driver_approved": True,
            "is_open": True,
            "is_full": False,
            "available_seats": 5,
        }
        data.update(overrides)
        return data

    def test_bus_details_show_only_public_profile_and_booking_terms(self):
        bus = self.bus(
            private_phone="08012345678",
            licence_image="secret-licence-photo.jpg",
            incident_allegations="PRIVATE-COMPLAINT",
        )
        html = self.render({"bus": bus})
        self.assertIn("Jibowu", html)
        self.assertIn("SRD-204", html)
        self.assertIn("Amina O.", html)
        self.assertIn("within 10 minutes", html)
        self.assertNotIn("08012345678", html)
        self.assertNotIn("secret-licence-photo.jpg", html)
        self.assertNotIn("PRIVATE-COMPLAINT", html)

    def test_reservation_is_a_csrf_protected_post_only_when_eligible(self):
        html = self.render({
            "bus": self.bus(),
            "can_reserve": True,
            "reserve_action": "/bookings/hold/",
        })
        self.assertIn('action="/bookings/hold/"', html)
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn("Reserve one seat", html)

        not_eligible = self.render({"bus": self.bus(), "can_reserve": False})
        self.assertNotIn('action="/bookings/hold/"', not_eligible)
        self.assertNotIn("type=\"submit\"", not_eligible)

    def test_full_bus_uses_waitlist_and_closed_bus_has_no_post(self):
        full = self.render({
            "bus": self.bus(is_full=True, available_seats=0),
            "can_join_waitlist": True,
            "waitlist_action": "/bookings/join-waitlist/",
        })
        self.assertIn('action="/bookings/join-waitlist/"', full)
        self.assertIn("Join waitlist", full)
        self.assertNotIn("Reserve one seat <", full)

        closed = self.render({
            "bus": self.bus(is_open=False),
            "can_reserve": True,
            "reserve_action": "/bookings/hold/",
        })
        self.assertNotIn('action="/bookings/hold/"', closed)
        self.assertIn("Bookings are closed", closed)

    def test_unavailable_bus_and_error_states(self):
        missing = self.render({"bus": None, "search_url": "/buses/"})
        self.assertIn("This bus isn't available.", missing)
        bad = self.render({
            "bus": self.bus(),
            "error_message": "<script>alert(1)</script>",
        })
        self.assertNotIn("<script>alert(1)</script>", bad)
        self.assertIn("&lt;script&gt;", bad)
