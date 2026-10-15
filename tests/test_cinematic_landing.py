"""Landing integration: real navigation, honest discovery and optional assets."""
from unittest.mock import patch

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("name", ["home", "how_it_works", "for_drivers", "safety_support"])
def test_public_pages_are_connected(client, name):
    response = client.get(reverse(f"core:{name}"))
    assert response.status_code == 200
    html = response.content.decode()
    for destination in ("how_it_works", "for_drivers", "safety_support"):
        assert f'href="{reverse(f"core:{destination}")}"' in html
    assert "data-theme-toggle" in html


def test_without_footage_home_is_complete_static_experience(client):
    with patch("apps.core.views.finders.find", return_value=None):
        html = client.get(reverse("core:home")).content.decode()
    assert "saferide-lagos-poster.webp" in html
    assert "saferide-lagos-mobile.webp" in html
    assert "<video" not in html
    assert html.index('id="hero-title"') < html.index('id="quick-ride"') < html.index('id="hero-route-map"')
    assert 'method="get" action="/departures/search/"' in html
    assert 'name="origin"' in html and 'name="destination"' in html
    assert "Journey suggestions, not a statement of bus availability." in html
    assert "/reserve/" not in html


def test_footage_requires_complete_encode_set(client):
    def missing_mobile_mp4(path):
        return None if path.endswith("mobile.mp4") else path
    with patch("apps.core.views.finders.find", side_effect=missing_mobile_mp4):
        assert b"<video" not in client.get(reverse("core:home")).content
    with patch("apps.core.views.finders.find", side_effect=lambda path: path):
        html = client.get(reverse("core:home")).content.decode()
    assert '<video class="cinematic-hero__video" muted loop playsinline preload="none"' in html
    assert "data-mobile-webm" in html and "data-desktop-mp4" in html
    assert '<source src="/static/media/saferide-lagos-desktop' not in html


def test_support_does_not_claim_official_identity_screening(client):
    html = client.get(reverse("core:safety_support")).content.decode()
    assert "does not perform official identity" in html
    assert "does not provide emergency response" in html
    assert reverse("verification:status") in html
    assert reverse("safety:report") in html
