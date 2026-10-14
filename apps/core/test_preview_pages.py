"""Preview-only page smoke tests. No DB or real booking operations."""
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.test import RequestFactory, SimpleTestCase

from apps.core.preview_views import PAGE_GROUPS, PAGES, app_home, gallery, page, public_page


class PreviewPagesTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request(self, path):
        request = self.factory.get(path)
        request.user = AnonymousUser()
        get_token(request)
        return request

    def test_gallery_displays_all_pages(self):
        response = gallery(self.request("/preview/screens/"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Every screen.", content)
        self.assertEqual(len(PAGES), 25)
        self.assertIn("noindex, nofollow", response["X-Robots-Tag"])

    def test_app_home_links_to_separate_sections(self):
        response = app_home(self.request("/preview/"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for target in ("/preview/search/", "/preview/trip/", "/preview/route-updates/",
                       "/preview/driver-dashboard/"):
            self.assertIn('href="' + target + '"', html)
        self.assertIn("Your journey", html)

    def test_route_search_get_navigates_to_results(self):
        response = page(self.request("/preview/search/"), "search")
        self.assertIn('action="/preview/results/"', response.content.decode())
        self.assertIn('method="get"', response.content.decode())

    def test_public_marketing_and_account_pages_work(self):
        for slug in ("how-it-works", "drive", "support", "my-trips"):
            with self.subTest(slug=slug):
                response = public_page(self.request("/preview/" + slug + "/"), slug)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertIn('href="/preview/', html)
                self.assertIn("<main ", html)
                self.assertIn('meta name="robots" content="noindex,nofollow"', html)

    def test_navigation_is_customer_facing(self):
        response = app_home(self.request("/preview/"))
        header = response.content.decode().split("</header>")[0]
        for label in ("Find a Ride", "How It Works", "For Drivers",
                      "Safety &amp; Support", "Sign In", "Get Started"):
            self.assertIn(label, header)
        for term in (">Discover</a>", ">Driver Space</a>", ">Journey</a>"):
            self.assertNotIn(term, header)

    def test_marketing_pages_reject_post(self):
        response = public_page(self.factory.post("/preview/drive/"), "drive")
        self.assertEqual(response.status_code, 405)

    def test_every_screen_is_renderable_with_safe_sample_data(self):
        for group, records in PAGE_GROUPS:
            for slug, title, _template in records:
                with self.subTest(group=group, slug=slug, title=title):
                    response = page(self.request(f"/preview/{slug}/"), slug)
                    self.assertEqual(response.status_code, 200)
                    html = response.content.decode()
                    self.assertIn("Design review", html)
                    self.assertIn("Sample content", html)
                    self.assertIn("<main ", html)
                    self.assertNotIn("SECRET-LICENCE", html)

    def test_preview_forms_are_get_only(self):
        from django.http import HttpResponseNotAllowed
        for view in (app_home, gallery, page, public_page):
            request = self.factory.post("/preview/")
            result = view(request, "login") if view is page else (
                view(request, "drive") if view is public_page else view(request)
            )
            self.assertIsInstance(result, HttpResponseNotAllowed)
