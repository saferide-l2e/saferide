"""Exercise real verification forms, staff gating and request validation."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.verification.models import VerificationStatus
from apps.verification.services import approve

pytestmark = pytest.mark.django_db
DECLARATION = {"fictional_data": "on", "simulated_review": "on"}


def test_unverified_user_sees_and_submits_declaration(client, unverified_passenger, staff):
    client.force_login(unverified_passenger)
    page = client.get(reverse("verification:status"))
    assert page.status_code == 200
    assert b'name="fictional_data"' in page.content
    assert b'name="simulated_review"' in page.content
    result = client.post(reverse("verification:submit"), DECLARATION, follow=True)
    assert result.status_code == 200
    assert b"Your request is processing." in result.content
    verification = unverified_passenger.verification
    verification.refresh_from_db()
    assert verification.status == VerificationStatus.PENDING
    assert verification.reviewed_by is None
    assert verification.submitted_at is not None
    assert b"Submit for staff review" not in result.content

    approve(verification, staff)
    result = client.get(reverse("verification:status"))
    assert b"Your profile has been approved." in result.content


@pytest.mark.parametrize("data", [{}, {"fictional_data": "on"}, {"simulated_review": "on"}])
def test_missing_declarations_do_not_submit(client, unverified_passenger, data):
    client.force_login(unverified_passenger)
    result = client.post(reverse("verification:submit"), data)
    assert result.status_code == 400
    assert b"Please confirm both declarations" in result.content
    verification = unverified_passenger.verification
    verification.refresh_from_db()
    assert verification.status == VerificationStatus.NOT_SUBMITTED
    assert verification.submitted_at is None


@pytest.mark.parametrize("status", [VerificationStatus.VERIFIED, VerificationStatus.PENDING, VerificationStatus.SUSPENDED])
def test_ineligible_status_cannot_be_resubmitted(client, passenger, status):
    verification = passenger.verification
    verification.status = status
    verification.save()
    client.force_login(passenger)
    result = client.post(reverse("verification:submit"), DECLARATION, follow=True)
    assert result.status_code == 200
    assert b"Submit for staff review" not in result.content
    verification.refresh_from_db()
    assert verification.status == status


def test_rejected_user_can_resubmit(client, unverified_passenger):
    verification = unverified_passenger.verification
    verification.status = VerificationStatus.REJECTED
    verification.note = "Please review the declaration."
    verification.save()
    client.force_login(unverified_passenger)
    assert b"Please review the declaration." in client.get(reverse("verification:status")).content
    client.post(reverse("verification:submit"), DECLARATION)
    verification.refresh_from_db()
    assert verification.status == VerificationStatus.PENDING
    assert verification.note == ""


def test_submission_requires_login_csrf_and_post(unverified_passenger):
    client = Client(enforce_csrf_checks=True)
    assert client.get(reverse("verification:status")).status_code == 302
    client.force_login(unverified_passenger)
    assert client.get(reverse("verification:submit")).status_code == 405
    assert client.post(reverse("verification:submit"), DECLARATION).status_code == 403
