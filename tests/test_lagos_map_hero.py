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
        "Road preview for planning your journey.",
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
    assert "View directions" in html
    assert "unpkg.com/maplibre-gl@5.6.0" in html
    from pathlib import Path

    from django.conf import settings

    route_js = (Path(settings.BASE_DIR) / "static/js/hero_route.js").read_text()
    assert "tiles.openfreemap.org/styles/liberty" in route_js
    assert "tile.openstreetmap.org" not in route_js


def test_no_map_scripts_on_login_page(client):
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
    assert b'id="hero-route-map"' not in response.content
    assert b"hero_route.js" not in response.content


def test_danfo_render_has_verified_asset_digest():
    """Guard against a mangled binary upload of the 3D illustration."""
    import hashlib
    from pathlib import Path

    from django.conf import settings

    asset = (Path(settings.BASE_DIR) / "static/img/danfo-3d.webp").read_bytes()
    assert asset[:4] == b"RIFF"
    assert asset[8:12] == b"WEBP"
    git_blob = b"blob " + str(len(asset)).encode() + b"\x00" + asset
    assert hashlib.sha1(git_blob).hexdigest() == "1620a13eaaa66e9b4ebab52da9d08779031a880a"


def test_route_card_is_product_focused_and_has_search_metadata(client):
    html = client.get(reverse("core:home")).content.decode()
    assert "YOUR LAGOS ROUTE" in html
    assert "data-map-provider" not in html
    assert "danfo_motion.js" not in html
    assert "data-map-motion" not in html
    assert "data-map-provider" not in html
    assert 'rel="canonical"' in html
    assert 'property="og:title"' in html
    assert 'application/ld+json' in html
