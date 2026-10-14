"""FE-06 route-search frontend rendering, independent of unmerged BE-04 views."""

from datetime import UTC, datetime

from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class RouteFrontendTests(SimpleTestCase):
    def render(self, name, context=None):
        request = RequestFactory().get("/buses/")
        request.user = AnonymousUser()
        return render_to_string(name, context or {}, request=request)

    def test_search_form_uses_get_and_names_backend_expects(self):
        html = self.render("passenger/search.html", {"origin": "Jibowu"})
        self.assertIn('method="get"', html)
        self.assertIn('name="origin"', html)
        self.assertIn('name="destination"', html)
        self.assertIn("Jibowu", html)
        self.assertIn("Mile 2", html)
        self.assertIn("not live", html.lower())

    def test_results_are_rendered_from_server_context(self):
        result = {
            "route_label": "Jibowu → Mile 2",
            "scheduled_departure_at": datetime(2026, 10, 15, 11, 30, tzinfo=UTC),
            "boarding_point": "Jibowu Park",
            "vehicle_type_display": "Minibus",
            "plate_display": "SRD-204",
            "driver_name": "Amina O.",
            "driver_approved": True,
            "available_seats": 5,
            "is_full": False,
            "detail_url": "/buses/example-uuid/",
        }
        html = self.render("passenger/results.html", {
            "origin": "Jibowu", "destination": "Mile 2",
            "buses": [result], "has_searched": True,
        })
        self.assertIn("SRD-204", html)
        self.assertIn("5 available", html)
        self.assertIn('href="/buses/example-uuid/"', html)
        self.assertIn("Amina O.", html)

    def test_full_bus_and_empty_results_show_clear_states(self):
        bus = {
            "route_label": "Jibowu → Mile 2",
            "is_full": True,
            "available_seats": 0,
        }
        html = self.render("passenger/results.html", {
            "buses": [bus], "has_searched": True,
        })
        self.assertIn("All seats taken", html)
        self.assertIn("Full", html)
        empty = self.render("passenger/results.html", {
            "buses": [], "has_searched": True,
        })
        self.assertIn("No matching departures", empty)

    def test_private_or_malicious_text_is_html_escaped(self):
        html = self.render("passenger/results.html", {
            "buses": [{
                "route_label": "Jibowu → Mile 2",
                "driver_name": "<script>alert(1)</script>",
                "plate_display": "SRD-204",
                "is_full": False,
                "available_seats": 1,
            }],
            "has_searched": True,
        })
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)
