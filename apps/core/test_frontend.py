"""Basic Django template and navigation smoke checks for FE-01."""

from django.template.loader import get_template
from django.test import SimpleTestCase
from django.urls import reverse


class FrontendShellTests(SimpleTestCase):
    def test_homepage_shows_routes_driver_and_safety_sections(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        for label in ('id="how-it-works"', 'id="for-drivers"', 'id="site-safety-title"'):
            with self.subTest(section=label):
                self.assertContains(response, label)
        self.assertContains(response, "Move smarter.")
        self.assertContains(response, "Jibowu")

    def test_accessible_navigation_and_truthful_route_label(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, 'href="#main-content"')
        self.assertContains(response, 'aria-label="Main navigation"')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, "Not live vehicle tracking")
        self.assertContains(response, "no live GPS")
        self.assertContains(response, 'data-site-header')
        self.assertContains(response, 'data-nav-toggle')

    def test_shared_components_are_available(self):
        for name in (
            "ui/action_link.html",
            "ui/status_badge.html",
            "ui/feature_card.html",
            "ui/notice.html",
            "ui/field_errors.html",
            "ui/demo_notice.html",
        ):
            with self.subTest(template=name):
                self.assertIsNotNone(get_template(name))

    def test_health_check_still_works(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
