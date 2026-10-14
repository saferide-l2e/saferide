"""FE-05: driver departure publishing/transition templates — no backend state changes."""
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class DepartureForm(forms.Form):
    vehicle = forms.ChoiceField(choices=(("1", "Mini bus SRD-204"),))
    route = forms.ChoiceField(choices=(("1", "Jibowu → Mile 2"),))
    scheduled_departure_at = forms.DateTimeField()


class DriverDashboardUITests(SimpleTestCase):
    def render(self, path, context):
        request = RequestFactory().get("/driver/departures/")
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(path, context, request=request)

    def test_dashboard_empty_and_publish_gated(self):
        html = self.render("driver/dashboard.html", {"can_publish": False,
                                                     "publish_url": "/driver/publish/"})
        self.assertIn("No scheduled departures yet.", html)
        self.assertNotIn('href="/driver/publish/"', html)
        eligible = self.render("driver/dashboard.html", {"can_publish": True,
                                                        "publish_url": "/driver/publish/"})
        self.assertIn('href="/driver/publish/"', eligible)

    def test_publish_form_csrf_and_validation(self):
        form = DepartureForm(data={"vehicle": "1", "route": "1",
                                   "scheduled_departure_at": "invalid"})
        self.assertFalse(form.is_valid())
        html = self.render("driver/publish_departure.html", {
            "can_publish": True, "form_action": "/driver/publish/", "form": form,
        })
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn("Enter a valid date/time.", html)
        self.assertIn("Africa/Lagos", html)

    def test_each_transition_has_a_single_post_action(self):
        states = [
            ("BOARDING_OPEN", "close_action", "can_close", "Close boarding"),
            ("BOARDING_CLOSED", "start_action", "can_start", "Start trip"),
            ("EN_ROUTE", "arrive_action", "can_arrive", "Mark arrived"),
            ("DRAFT", "cancel_action", "can_cancel", "Cancel departure"),
        ]
        for status, action, permitted, label in states:
            with self.subTest(status=status):
                html = self.render("driver/departure_detail.html", {
                    "departure": {"status": status, "route_label": "Jibowu → Mile 2"},
                    permitted: True,
                    action: "/driver/transition/",
                })
                self.assertIn(label, html)
                self.assertIn('action="/driver/transition/"', html)
                self.assertIn('name="csrfmiddlewaretoken"', html)
                no_permission = self.render("driver/departure_detail.html", {
                    "departure": {"status": status, "route_label": "Jibowu → Mile 2"},
                    permitted: False,
                    action: "/driver/transition/",
                })
                self.assertNotIn('action="/driver/transition/"', no_permission)

    def test_private_driver_name_not_echoed(self):
        html = self.render("driver/dashboard.html", {"departures": [{
            "route_label": "<script>alert(1)</script>",
            "plate_display": "SRD-204", "capacity": 12, "status": "DRAFT",
        }]})
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)
