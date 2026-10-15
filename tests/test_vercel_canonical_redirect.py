"""Regression coverage for the temporary single-backend Vercel demo topology."""
import pytest
from django.test import override_settings

from apps.accounts.models import User

pytestmark = pytest.mark.django_db
VERCEL = "saferide-eight.vercel.app"
CANONICAL = "https://saferide-friday-web.onrender.com"


@override_settings(ALLOWED_HOSTS=[VERCEL, "saferide-friday-web.onrender.com", "testserver"])
def test_vercel_home_and_signup_are_redirected_before_db_pages(client, monkeypatch):
    monkeypatch.delenv("SAFERIDE_VERCEL_CANONICAL_REDIRECT", raising=False)
    for path in ("/", "/accounts/register/", "/accounts/login/",
                 "/verification/", "/departures/search/"):
        response = client.get(path, HTTP_HOST=VERCEL)
        assert response.status_code == 307
        assert response["Location"] == CANONICAL + path
        assert response["Cache-Control"] == "no-store"
    driver = client.get("/accounts/register/?role=DRIVER", HTTP_HOST=VERCEL)
    assert driver.status_code == 307
    assert driver["Location"] == CANONICAL + "/accounts/register/?role=DRIVER"


@override_settings(ALLOWED_HOSTS=[VERCEL, "saferide-friday-web.onrender.com", "testserver"])
def test_stale_post_does_not_repeat_credentials_across_hosts(client, monkeypatch):
    monkeypatch.delenv("SAFERIDE_VERCEL_CANONICAL_REDIRECT", raising=False)
    email = "must-not-create@example.test"
    response = client.post("/accounts/register/", {
        "display_name": "Test",
        "email": email,
        "role": "PASSENGER",
        "password1": "NotTransferredPassword!2026",
        "password2": "NotTransferredPassword!2026",
    }, HTTP_HOST=VERCEL)
    assert response.status_code == 303
    assert response["Location"] == CANONICAL + "/accounts/register/"
    assert not User.objects.filter(email=email).exists()


@override_settings(ALLOWED_HOSTS=[VERCEL, "saferide-friday-web.onrender.com", "testserver"])
def test_render_stays_canonical_and_switch_is_reversible(client, monkeypatch):
    original = client.get("/accounts/register/", HTTP_HOST="saferide-friday-web.onrender.com")
    assert original.status_code == 200
    monkeypatch.setenv("SAFERIDE_VERCEL_CANONICAL_REDIRECT", "false")
    restored = client.get("/accounts/register/", HTTP_HOST=VERCEL)
    assert restored.status_code == 200
