"""FE-11: passenger and driver journeys show separate arrival confirmations."""
from datetime import UTC, datetime

from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class JourneyUITests(SimpleTestCase):
    def render(self, template, context):
        request = RequestFactory().get("/my/journey/")
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(template, context, request=request)

    def booking(self, **overrides):
        value = {"route_label": "Jibowu → Mile 2", "plate_display": "SRD-204",
                 "display_status": "Boarded", "booking_status": "BOARDED"}
        value.update(overrides)
        return value

    def test_driver_arrival_without_passenger_confirmation(self):
        arrival = datetime(2026, 10, 14, 16, 0, tzinfo=UTC)
        html = self.render("passenger/trip.html", {
            "trip": self.booking(driver_arrived_at=arrival),
            "can_confirm": True, "confirm_action": "/journeys/confirm/",
        })
        self.assertIn("Driver marked arrived", html)
        self.assertIn("Not yet confirmed by you", html)
        self.assertIn('action="/journeys/confirm/"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_no_early_or_wrong_user_arrival_action(self):
        arrival = datetime(2026, 10, 14, 16, 0, tzinfo=UTC)
        for trip, allowed in [
            (self.booking(), True),
            (self.booking(driver_arrived_at=arrival, booking_status="HELD"), True),
            (self.booking(driver_arrived_at=arrival), False),
        ]:
            with self.subTest(trip=trip, allowed=allowed):
                html = self.render("passenger/trip.html", {
                    "trip": trip, "can_confirm": allowed,
                    "confirm_action": "/journeys/confirm/",
                })
                self.assertNotIn('action="/journeys/confirm/"', html)

    def test_confirmation_and_history_remain_separate(self):
        arrived = datetime(2026, 10, 14, 16, 0, tzinfo=UTC)
        html = self.render("passenger/trip.html", {
            "trip": self.booking(driver_arrived_at=arrived,
                                 passenger_confirmed_at=arrived),
        })
        self.assertIn("You confirmed your arrival.", html)
        self.assertNotIn("Yes, I've arrived", html)
        history = self.render("passenger/history.html", {
            "trips": [{"route_label": "Jibowu → Mile 2",
                       "driver_arrived_at": arrived,
                       "passenger_confirmed_at": None}],
        })
        self.assertIn("your confirmation is still pending", history)

    def test_driver_history_has_no_public_passenger_roster(self):
        html = self.render("driver/history.html", {
            "departures": [{"route_label": "Jibowu → Mile 2",
                            "plate_display": "SRD-204",
                            "private_passenger_email": "secret@example.com"}],
        })
        self.assertNotIn("secret@example.com", html)
        self.assertIn("Jibowu", html)
