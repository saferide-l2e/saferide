"""FE-03: verification pages render only safe simulated status information."""
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class Declaration(forms.Form):
    fictional_declaration = forms.BooleanField(
        label="I confirm this is a fictional declaration"
    )
    privacy_consent = forms.BooleanField(label="I understand the privacy notice")


class VerificationUITests(SimpleTestCase):
    def render(self, path, context):
        request = RequestFactory().get("/account/verification/")
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(path, context, request=request)

    def test_statuses_do_not_offer_self_approval(self):
        messages = {
            "NOT_SUBMITTED": "Not submitted",
            "PENDING": "Awaiting review",
            "VERIFIED": "Simulated approval complete",
            "REJECTED": "Review not approved",
            "SUSPENDED": "Account restricted",
        }
        for status, text in messages.items():
            with self.subTest(status=status):
                html = self.render("accounts/verification.html", {"status": status})
                self.assertIn(text, html)
                self.assertNotIn("Mark me verified", html)
                self.assertIn("simulated", html.lower())

    def test_declaration_is_post_only_and_uses_csrf(self):
        html = self.render("accounts/verification.html", {
            "status": "NOT_SUBMITTED",
            "can_submit": True,
            "submit_action": "/verification/submit/",
            "form": Declaration(),
        })
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('action="/verification/submit/"', html)

    def test_no_unapproved_user_can_submit_when_link_is_present(self):
        html = self.render("accounts/verification.html", {
            "status": "SUSPENDED",
            "can_submit": False,
            "submit_action": "/verification/submit/",
        })
        self.assertNotIn('action="/verification/submit/"', html)

    def test_public_profiles_reveal_no_hidden_fields(self):
        profile = {
            "public_display_name": "Amina O.",
            "is_approved": True,
            "initials": "AO",
            "email": "do-not-display@example.com",
            "phone": "08011112222",
            "licence_scan": "SECRET-LICENCE",
            "complaint": "SECRET-COMPLAINT",
        }
        for path in ("passenger/profile.html", "driver/profile.html"):
            with self.subTest(path=path):
                html = self.render(path, {"profile": profile})
                self.assertIn("Amina O.", html)
                self.assertIn("Simulated profile approved", html)
                for forbidden in ("do-not-display@example.com", "08011112222",
                                  "SECRET-LICENCE", "SECRET-COMPLAINT"):
                    self.assertNotIn(forbidden, html)
