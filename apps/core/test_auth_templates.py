"""FE-02: form rendering tests without unmerged authentication views or URLs."""

from django import forms
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class SignupForm(forms.Form):
    role = forms.ChoiceField(choices=(("PASSENGER", "Passenger"), ("DRIVER", "Driver")))
    display_name = forms.CharField()
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    privacy_acknowledged = forms.BooleanField(
        label="I understand the privacy notice"
    )


class SigninForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class AuthenticationTemplateTests(SimpleTestCase):
    def render_form(self, path, form, url):
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(path, {"form": form}, request=request)

    def test_signup_renders_roles_fields_and_csrf(self):
        html = self.render_form("accounts/register.html", SignupForm(), "/register/")
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('type="password"', html)
        self.assertIn('type="checkbox"', html)
        self.assertIn('name="role"', html)
        self.assertIn("Passenger", html)
        self.assertIn("Driver", html)

    def test_signup_renders_errors_without_echoing_password(self):
        form = SignupForm(
            data={
                "role": "PASSENGER",
                "display_name": "Tomi",
                "email": "not-an-email",
                "password1": "supersecret-example-value",
                "password2": "",
            }
        )
        self.assertFalse(form.is_valid())
        html = self.render_form("accounts/register.html", form, "/register/")
        self.assertIn("Enter a valid email address.", html)
        self.assertIn("form-field--error", html)
        self.assertNotIn('value="supersecret-example-value"', html)

    def test_login_has_password_and_post_based_form(self):
        html = self.render_form("accounts/login.html", SigninForm(), "/login/")
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('name="email"', html)
        self.assertIn('type="password"', html)
        self.assertIn("Sign in securely", html)
