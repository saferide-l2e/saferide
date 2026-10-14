"""FE-12: moderation and privacy-safe passenger/community screens."""
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class ReviewForm(forms.Form):
    stars = forms.IntegerField(min_value=1, max_value=5)
    comment = forms.CharField(required=False, widget=forms.Textarea)


class ReportForm(forms.Form):
    category = forms.ChoiceField(choices=(("OTHER", "Other"),))
    description = forms.CharField(widget=forms.Textarea)


class SafetyTemplateTests(SimpleTestCase):
    def render(self, template, context):
        req = RequestFactory().get("/safety/")
        req.user = AnonymousUser()
        get_token(req)
        return render_to_string(template, context, request=req)

    def test_rating_only_on_completed_eligible_trip(self):
        ctx = {"form": ReviewForm(), "can_review": True,
               "trip_is_completed": True, "review_action": "/review/"}
        html = self.render("safety/review.html", ctx)
        self.assertIn('action="/review/"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        uncompleted = self.render("safety/review.html", {
            **ctx, "trip_is_completed": False,
        })
        self.assertNotIn('action="/review/"', uncompleted)
        reviewed = self.render("safety/review.html", {
            **ctx, "has_reviewed": True,
        })
        self.assertNotIn('action="/review/"', reviewed)

    def test_bad_star_rating_uses_server_validation(self):
        form = ReviewForm(data={"stars": 6})
        self.assertFalse(form.is_valid())
        html = self.render("safety/review.html", {
            "can_review": True, "trip_is_completed": True,
            "review_action": "/review/", "form": form,
        })
        self.assertIn("Ensure this value is less than or equal to 5.", html)

    def test_private_report_requires_permission_and_csrf(self):
        ctx = {"form": ReportForm(), "can_report": True,
               "report_action": "/private-report/"}
        html = self.render("safety/report.html", ctx)
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn("Reports are reviewed", html)
        disabled = self.render("safety/report.html", {
            **ctx, "can_report": False,
        })
        self.assertNotIn('action="/private-report/"', disabled)

    def test_public_feed_excludes_pending_and_escapes_text(self):
        html = self.render("safety/route_feed.html", {
            "updates": [
                {"status": "PENDING", "note": "PRIVATE-PENDING-TEXT"},
                {"status": "APPROVED", "type_label": "Traffic",
                 "route_label": "Jibowu → Mile 2",
                 "note": "<script>bad</script>"},
            ],
        })
        self.assertNotIn("PRIVATE-PENDING-TEXT", html)
        self.assertNotIn("<script>bad</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_route_submission_is_pending_and_requires_csrf(self):
        html = self.render("safety/route_update_form.html", {
            "form": ReportForm(), "can_submit": True,
            "form_action": "/routes/submit/",
        })
        self.assertIn('action="/routes/submit/"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        pending = self.render("safety/route_update_form.html", {"submitted": True})
        self.assertIn("remains pending", pending)
