"""FE-13 lightweight semantic/asset tests; not a substitute for browser audit."""
from pathlib import Path

from django.conf import settings
from django.template.loader import get_template
from django.test import SimpleTestCase
from django.urls import reverse


class AccessibilityFoundationTests(SimpleTestCase):
    def test_home_has_named_navigation_and_skip_link(self):
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertIn('href="#main-content"', html)
        self.assertIn('id="main-content"', html)
        self.assertIn('aria-label="Main navigation"', html)
        self.assertIn('aria-expanded="false"', html)

    def test_feature_templates_load_on_combined_branch(self):
        for name in (
            "accounts/register.html", "accounts/login.html",
            "accounts/verification.html", "passenger/search.html",
            "passenger/results.html", "passenger/bus_detail.html",
            "booking/hold.html", "booking/waitlist.html", "booking/offer.html",
            "driver/roster.html", "driver/check_in.html",
            "driver/vehicle_form.html", "driver/vehicle_list.html",
            "driver/dashboard.html", "driver/publish_departure.html",
            "driver/departure_detail.html", "passenger/trip.html",
            "passenger/history.html", "driver/history.html",
            "safety/review.html", "safety/report.html",
            "safety/route_feed.html", "safety/route_update_form.html",
        ):
            with self.subTest(template=name):
                self.assertIsNotNone(get_template(name))

    def test_shared_form_errors_announced_with_role(self):
        source = (Path(settings.BASE_DIR) / "templates/ui/field_errors.html").read_text()
        self.assertIn('role="alert"', source)
        self.assertIn('id="{{ field.auto_id }}_errors"', source)

    def test_shared_accessibility_and_reduced_motion_present(self):
        base = (Path(settings.BASE_DIR) / "static/css/base.css").read_text()
        menu = (Path(settings.BASE_DIR) / "static/js/navigation.js").read_text()
        self.assertIn("prefers-reduced-motion:reduce", base)
        self.assertIn("forced-colors:active", base)
        self.assertIn(":focus-visible", base)
        self.assertIn('event.key === "Escape"', menu)
        self.assertIn('aria-expanded', menu)
        self.assertIn('html:not(.has-js)', base)
