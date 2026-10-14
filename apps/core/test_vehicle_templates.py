"""FE-04: vehicle screens render backend-owned approval status only."""
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class VehicleForm(forms.Form):
    vehicle_type = forms.ChoiceField(choices=(("BUS", "Bus"), ("MINIBUS", "Minibus")))
    plate_display = forms.CharField()
    seat_capacity = forms.IntegerField(min_value=1)


class VehicleTemplateTests(SimpleTestCase):
    def render(self, path, context):
        request = RequestFactory().get("/driver/vehicles/")
        request.user = AnonymousUser()
        get_token(request)
        return render_to_string(path, context, request=request)

    def test_valid_django_form_posts_with_csrf(self):
        html = self.render("driver/vehicle_form.html", {
            "form": VehicleForm(), "can_register": True, "form_action": "/driver/vehicles/new/",
        })
        self.assertIn('method="post"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('name="seat_capacity"', html)

    def test_invalid_capacity_shows_backend_validation(self):
        form = VehicleForm(data={"vehicle_type": "BUS", "plate_display": "SRD-204", "seat_capacity": 0})
        self.assertFalse(form.is_valid())
        html = self.render("driver/vehicle_form.html", {
            "form": form, "can_register": True, "form_action": "/driver/vehicles/new/",
        })
        self.assertIn("Ensure this value is greater than or equal to 1.", html)

    def test_no_driver_eligibility_means_no_form(self):
        html = self.render("driver/vehicle_form.html", {
            "can_register": False, "form_action": "/driver/vehicles/new/",
        })
        self.assertNotIn('action="/driver/vehicles/new/"', html)

    def test_publish_only_approved(self):
        for status in ("PENDING", "APPROVED", "REJECTED", "SUSPENDED"):
            with self.subTest(status=status):
                html = self.render("driver/vehicle_list.html", {"vehicles": [{
                    "vehicle_type_display": "Minibus", "plate_display": "SRD-204",
                    "seat_capacity": 12, "approval_status": status,
                    "can_publish": True, "publish_url": "/driver/new-departure/",
                }]})
                if status == "APPROVED":
                    self.assertIn('href="/driver/new-departure/"', html)
                else:
                    self.assertNotIn('href="/driver/new-departure/"', html)

    def test_untrusted_plate_is_escaped(self):
        html = self.render("driver/vehicle_list.html", {"vehicles": [{
            "vehicle_type_display": "Minibus",
            "plate_display": "<script>bad</script>",
            "seat_capacity": 12, "approval_status": "PENDING",
        }]})
        self.assertNotIn("<script>bad</script>", html)
        self.assertIn("&lt;script&gt;", html)
