"""Passengers see actual approval state and approved public fields only."""
import pytest
from django.urls import reverse

from apps.vehicles.models import ApprovalStatus

pytestmark = pytest.mark.django_db


def test_passenger_sees_driver_and_vehicle_review_status(client, passenger, departure):
    profile = departure.driver.driver_profile
    profile.bio = "I drive the Jibowu corridor."
    profile.save()
    client.force_login(passenger)
    response = client.get(reverse("departures:detail", args=[departure.pk]))
    assert response.status_code == 200
    assert profile.approved_display_name.encode() in response.content
    assert b"I drive the Jibowu corridor." in response.content
    for label in (b"Account access", b"Driver profile access", b"Vehicle listing access"):
        assert label in response.content
    assert departure.driver.email.encode() not in response.content
    assert b"Access approvals are automatic" in response.content


def test_unapproved_driver_bio_is_not_published(client, passenger, departure):
    profile = departure.driver.driver_profile
    profile.bio = "UNAPPROVED-BIO"
    profile.licence_review_status = ApprovalStatus.PENDING
    profile.save()
    client.force_login(passenger)
    response = client.get(reverse("departures:detail", args=[departure.pk]))
    assert b"UNAPPROVED-BIO" not in response.content
    assert b"Not approved" in response.content
