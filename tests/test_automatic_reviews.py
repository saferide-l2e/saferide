from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role
from apps.audit.models import AuditEvent
from apps.core.automatic_reviews import process_due_reviews
from apps.safety.models import IncidentReport, IncidentStatus, RouteUpdate, RouteUpdateStatus
from apps.vehicles.models import ApprovalStatus, DriverProfile, Vehicle
from apps.vehicles.services import register_vehicle
from apps.verification.models import Verification, VerificationStatus
from apps.verification.services import reject, submit

pytestmark = pytest.mark.django_db


def test_account_approval_boundary_and_audit(unverified_passenger):
    review = submit(unverified_passenger)
    due = review.submitted_at + timedelta(seconds=5)
    assert process_due_reviews(now=due - timedelta(microseconds=1))["accounts"] == 0
    assert process_due_reviews(now=due)["accounts"] == 1
    review.refresh_from_db()
    assert review.status == VerificationStatus.VERIFIED
    assert review.reviewed_by is None
    assert review.reviewed_at == due
    audit = AuditEvent.objects.get(action="verification.verified", object_id=str(review.pk))
    assert audit.actor is None and audit.metadata["automatic"] is True
    assert process_due_reviews(now=due)["accounts"] == 0
    assert AuditEvent.objects.filter(action="verification.verified").count() == 1


@pytest.mark.parametrize("status", [VerificationStatus.NOT_SUBMITTED, VerificationStatus.REJECTED, VerificationStatus.SUSPENDED])
def test_staff_decisions_and_unsubmitted_accounts_remain(status, unverified_passenger):
    Verification.objects.filter(user=unverified_passenger).update(status=status, submitted_at=timezone.now()-timedelta(days=1))
    assert process_due_reviews()["accounts"] == 0
    unverified_passenger.refresh_from_db()
    assert unverified_passenger.verification_status == status


def test_disabled_policy_and_inactive_account(settings, unverified_passenger):
    review = submit(unverified_passenger)
    now = review.submitted_at + timedelta(seconds=6)
    settings.SAFERIDE_AUTO_APPROVAL = False
    assert not any(process_due_reviews(now=now).values())
    settings.SAFERIDE_AUTO_APPROVAL = True
    unverified_passenger.is_active = False
    unverified_passenger.save()
    assert not any(process_due_reviews(now=now).values())


def test_rejection_before_due_is_not_overwritten(unverified_passenger, staff):
    review = submit(unverified_passenger)
    reject(review, staff, note="Staff decision")
    process_due_reviews(now=review.submitted_at+timedelta(seconds=6))
    review.refresh_from_db()
    assert review.status == VerificationStatus.REJECTED and review.reviewed_by == staff


def test_driver_profile_and_vehicle_each_observe_delay(make_user):
    driver = make_user("automatic-driver@example.test", "Driver QA", Role.DRIVER, verified=False)
    review = submit(driver)
    profile = DriverProfile.objects.get(user=driver)
    due = max(review.submitted_at, profile.created_at) + timedelta(seconds=5)
    result = process_due_reviews(now=due)
    assert result["accounts"] == result["drivers"] == 1
    driver.refresh_from_db()
    vehicle = register_vehicle(driver, plate_display="LAG-911QA", vehicle_type="Hiace", capacity=10)
    due = vehicle.created_at + timedelta(seconds=5)
    assert process_due_reviews(now=due-timedelta(microseconds=1))["vehicles"] == 0
    assert process_due_reviews(now=due)["vehicles"] == 1
    vehicle.refresh_from_db()
    assert vehicle.approval_status == ApprovalStatus.APPROVED


@pytest.mark.parametrize("status", [ApprovalStatus.REJECTED, ApprovalStatus.SUSPENDED])
def test_vehicle_and_driver_restrictions_stay_in_force(driver, status):
    vehicle = register_vehicle(driver, plate_display="LAG-912QA", vehicle_type="Hiace", capacity=10)
    Vehicle.objects.filter(pk=vehicle.pk).update(approval_status=status)
    DriverProfile.objects.filter(user=driver).update(licence_review_status=status)
    assert not any(process_due_reviews(now=timezone.now()+timedelta(seconds=10)).values())
    vehicle.refresh_from_db()
    assert vehicle.approval_status == status


def test_vehicle_does_not_approve_for_restricted_driver(driver):
    vehicle = register_vehicle(driver, plate_display="LAG-913QA", vehicle_type="Hiace", capacity=10)
    Verification.objects.filter(user=driver).update(status=VerificationStatus.SUSPENDED)
    process_due_reviews(now=timezone.now()+timedelta(seconds=10))
    vehicle.refresh_from_db()
    assert vehicle.approval_status == ApprovalStatus.PENDING


def test_route_publication_and_private_incident_are_separate(passenger, route):
    update = RouteUpdate.objects.create(route=route, reporter=passenger, type="TRAFFIC", note="Traffic observation", occurred_at=timezone.now())
    incident = IncidentReport.objects.create(reporter=passenger, category="OTHER", description="Private report")
    due = update.created_at + timedelta(seconds=5)
    assert process_due_reviews(now=due-timedelta(microseconds=1))["route_updates"] == 0
    assert process_due_reviews(now=due)["route_updates"] == 1
    update.refresh_from_db()
    incident.refresh_from_db()
    assert update.status == RouteUpdateStatus.APPROVED and update.reviewed_by is None
    assert incident.status == IncidentStatus.PENDING
    RouteUpdate.objects.filter(pk=update.pk).update(status=RouteUpdateStatus.REJECTED)
    assert process_due_reviews(now=due)["route_updates"] == 0


def test_existing_due_queue_processed_after_worker_restart(unverified_passenger):
    submit(unverified_passenger)
    Verification.objects.filter(user=unverified_passenger).update(submitted_at=timezone.now()-timedelta(seconds=30))
    call_command("process_reviews")
    unverified_passenger.refresh_from_db()
    assert unverified_passenger.is_verified


def test_progress_endpoint_private_and_read_only(client, unverified_passenger, other_passenger):
    url = reverse("core:review_progress")
    assert client.get(url).status_code == 302
    review = submit(unverified_passenger)
    Verification.objects.filter(pk=review.pk).update(submitted_at=timezone.now()-timedelta(seconds=30))
    client.force_login(unverified_passenger)
    response = client.get(url)
    assert response.status_code == 200
    assert "no-store" in response.headers["Cache-Control"]
    assert response.json()["version"].startswith("PENDING|")
    assert str(other_passenger.pk) not in response.content.decode()
    review.refresh_from_db()
    assert review.status == VerificationStatus.PENDING


@pytest.mark.django_db(transaction=True)
def test_parallel_workers_only_approve_and_audit_once(unverified_passenger):
    review = submit(unverified_passenger)
    due = review.submitted_at+timedelta(seconds=6)

    def run():
        close_old_connections()
        try:
            return process_due_reviews(now=due)["accounts"]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(lambda _: run(), range(2))) == 1
    assert AuditEvent.objects.filter(action="verification.verified", object_id=str(review.pk)).count() == 1
