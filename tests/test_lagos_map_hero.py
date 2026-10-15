"""Live-route homepage integration contracts; actual browser map QA remains required."""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_home_map_and_real_directions_link(client):
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    html = response.content.decode()
    for required in (
        'id="hero-route-map"',
        "data-route-hero",
        "Jibowu", "Mile 2",
        "maps/dir/?api=1",
        "Not live vehicle tracking",
        "img/danfo-3d.webp",
        "site_route.css",
        "hero_route.js",
        'method="get" action="/departures/search/"',
    ):
        assert required in html, required


def test_browser_key_injected_only_if_configured(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_BROWSER_KEY", "BROWSER_RESTRICTED_EXAMPLE")
    html = client.get(reverse("core:home")).content.decode()
    assert 'data-google-key="BROWSER_RESTRICTED_EXAMPLE"' in html


def test_without_google_key_map_has_fallback(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_MAPS_BROWSER_KEY", raising=False)
    html = client.get(reverse("core:home")).content.decode()
    assert 'data-google-key=""' in html
    assert "Open in Google Maps" in html
    assert "unpkg.com/leaflet" in html


def test_no_map_scripts_on_login_page(client):
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
    assert b'id="hero-route-map"' not in response.content
    assert b"hero_route.js" not in response.content
