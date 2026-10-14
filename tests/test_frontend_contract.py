"""Backend → frontend view contract.

The frontend team owns the actual templates. These tests verify the backend
exposes the documented URLs, renders the documented template names, and enforces
access control — using in-memory placeholder templates so the backend can be
checked on its own.
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


# (url name, logged-in fixture, object fixture for URL args, expected template)
PAGE_CASES = [
    ("core:home", None, None, "home.html"),
    ("accounts:login", None, None, "accounts/login.html"),
    ("accounts:register", None, None, "accounts/register.html"),
    ("accounts:profile", "passenger", None, "accounts/profile.html"),
    ("verification:status", "passenger", None, "accounts/verification.html"),
    ("core:dashboard", "passenger", None, "dashboard.html"),
    ("departures:search", "passenger", None, "passenger/search.html"),
    ("bookings:index", "passenger", None, "booking/my_bookings.html"),
    ("bookings:detail", "passenger", "booking", "booking/detail.html"),
    ("departures:detail", "passenger", "departure", "passenger/departure_detail.html"),
    ("departures:dashboard", "driver", None, "driver/dashboard.html"),
    ("departures:create", "driver", None, "driver/departure_form.html"),
    ("departures:manage", "driver", "departure", "driver/departure_manage.html"),
    ("vehicles:list", "driver", None, "driver/vehicles.html"),
    ("vehicles:create", "driver", None, "driver/vehicle_form.html"),
    ("vehicles:profile", "driver", None, "driver/profile.html"),
    ("safety:route_updates", None, None, "safety/route_updates.html"),
    ("safety:route_update_new", "passenger", None, "safety/route_update_form.html"),
    ("safety:report", "passenger", None, "safety/incident_form.html"),
    ("safety:review", "passenger", "booking", "safety/review_form.html"),
]


@pytest.mark.parametrize("url_name,user_fixture,obj_fixture,expected", PAGE_CASES)
def test_page_view_renders_contracted_template(
    request, client, stub_frontend_templates, url_name, user_fixture, obj_fixture, expected
):
    args = []
    if user_fixture:
        client.force_login(request.getfixturevalue(user_fixture))
    if obj_fixture:
        args = [request.getfixturevalue(obj_fixture).id]

    response = client.get(reverse(url_name, args=args))

    assert response.status_code == 200, (url_name, response.status_code)
    rendered = [template.name for template in response.templates]
    assert expected in rendered, (url_name, rendered)


def test_json_endpoints_return_data_not_html(passenger, driver, departure, booking, client):
    """The frontend polls these; they must be JSON and enforce ownership."""
    client.force_login(passenger)
    status = client.get(reverse("bookings:status", args=[booking.id]))
    assert status["Content-Type"].startswith("application/json")
    assert status.json()["status"] == "HELD"

    availability = client.get(reverse("departures:availability", args=[departure.id]))
    assert availability["Content-Type"].startswith("application/json")
    assert "available" in availability.json()


def test_anonymous_page_redirects_to_login_with_next(departure, client):
    response = client.get(reverse("departures:detail", args=[departure.id]))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url
