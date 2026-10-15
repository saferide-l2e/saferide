"""Customer copy and registration grouping without changing eligibility rules."""
import re
from html.parser import HTMLParser

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class CustomerText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        self.text.extend(value for name, value in attrs if value and name in {
            "aria-label", "placeholder", "alt", "title",
        })

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)


def assert_customer_copy(response):
    assert response.status_code == 200
    parser = CustomerText()
    parser.feed(response.content.decode())
    assert not re.search(r"\b(demo|fictional)\b", " ".join(parser.text), re.IGNORECASE)


@pytest.mark.parametrize("url", [
    "/", "/accounts/register/", "/accounts/login/", "/how-it-works/",
    "/for-drivers/", "/safety-support/",
    "/departures/search/?origin=Yaba&destination=Ikeja&preview=1",
    "/departures/sample-ride/?origin=Yaba&destination=Ikeja&option=1",
])
def test_customer_copy_avoids_development_terms(client, url):
    assert_customer_copy(client.get(url))


def test_account_form_preserves_review_requirements_with_clear_labels(client, unverified_passenger):
    client.force_login(unverified_passenger)
    response = client.get(reverse("verification:status"))
    assert_customer_copy(response)
    assert response.context["form"].fields["fictional_data"].required
    assert response.context["form"].fields["simulated_review"].required
    assert b"does not include government identity" in response.content


def test_signup_groups_account_choices_and_preserves_driver_preselection(client):
    response = client.get(reverse("accounts:register"), {"role": "DRIVER"})
    assert_customer_copy(response)
    assert b"<legend>How will you use SafeRide?</legend>" in response.content
    assert response.context["form"]["role"].value() == "DRIVER"
    assert list(response.context["form"].fields["role"].choices) == [
        ("PASSENGER", "Passenger"), ("DRIVER", "Driver"),
    ]
