import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Role
from apps.vehicles.models import ApprovalStatus, Vehicle
from apps.verification.models import VerificationStatus

pytestmark = pytest.mark.django_db
DATA = {"plate_display": "LAG-917QA", "vehicle_type": "Toyota Hiace", "capacity": 10}


@pytest.mark.parametrize("status", list(VerificationStatus))
def test_vehicle_form_matches_account_eligibility(client, make_user, status):
    user = make_user("vehicle-review@example.test", "Driver QA", Role.DRIVER, verified=False)
    user.verification.status = status
    user.verification.save()
    client.force_login(user)
    response = client.get(reverse("vehicles:create"))
    assert response.status_code == 200
    approved = status == VerificationStatus.VERIFIED
    assert response.context["can_register"] is approved
    assert (b'name="plate_display"' in response.content) is approved
    if not approved:
        assert b"Account approval required" in response.content
        assert reverse("verification:status").encode() in response.content
        response = client.post(reverse("vehicles:create"), DATA)
        assert response.status_code == 200
        assert b"Account approval required" in response.content
        assert not Vehicle.objects.exists()
    else:
        response = client.post(reverse("vehicles:create"), DATA)
        assert response.status_code == 302
        vehicle = Vehicle.objects.get()
        assert vehicle.driver.user_id == user.pk
        assert vehicle.approval_status == ApprovalStatus.PENDING


def test_vehicle_submission_still_rejects_passengers(client, passenger):
    client.force_login(passenger)
    assert client.post(reverse("vehicles:create"), DATA).status_code == 403
    assert not Vehicle.objects.exists()


def test_vehicle_submission_requires_csrf(driver):
    client = Client(enforce_csrf_checks=True)
    client.force_login(driver)
    assert client.post(reverse("vehicles:create"), DATA).status_code == 403
    assert not Vehicle.objects.exists()
