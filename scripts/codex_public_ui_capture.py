#!/usr/bin/env python3
"""Read-only Chromium screenshots of the public SafeRide UI.

This never authenticates, submits a form, or changes the production database.
Usage:
  pip install playwright && python -m playwright install chromium
  python scripts/codex_public_ui_capture.py
  python scripts/codex_public_ui_capture.py --base-url http://127.0.0.1:8000 --out artifacts/codex-ui-after
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

PUBLIC_PAGES = {
    "home": "/",
    "how-it-works": "/how-it-works/",
    "for-drivers": "/for-drivers/",
    "safety-support": "/safety-support/",
    "find-a-ride": "/departures/search/?origin=Jibowu&destination=Mile+2",
    "sign-in": "/accounts/login/",
    "get-started": "/accounts/register/",
}
VIEWPORTS = ((320, 700), (390, 844), (768, 1024), (1024, 768), (1440, 900))
LIVE_HOST = "saferide-friday-web.onrender.com"


def approved_base(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if host == LIVE_HOST and parsed.scheme == "https":
        return value.rstrip("/")
    if host in {"127.0.0.1", "localhost"} and parsed.scheme == "http":
        return value.rstrip("/")
    raise SystemExit("Only https://saferide-friday-web.onrender.com or a localhost HTTP URL is permitted.")


def capture(page, base, name, path, width, height, out):
    page.set_viewport_size({"width": width, "height": height})
    row = {"name": name, "path": path, "viewport": [width, height]}
    errors = []
    def on_error(error):
        errors.append(str(error)[:220])
    page.on("pageerror", on_error)
    try:
        response = page.goto(base + path, wait_until="domcontentloaded", timeout=100000)
        page.wait_for_timeout(1200)
        page.screenshot(path=str(out / f"{name}-{width}.png"), full_page=True, timeout=30000)
        row["status"] = response.status if response else None
        row["title"] = page.title()
        row["overflow_px"] = page.evaluate(
            "() => Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-window.innerWidth"
        )
        row["map_state"] = (
            page.locator("[data-route-hero]").first.get_attribute("data-map-state")
            if page.locator("[data-route-hero]").count() else None
        )
        row["map_provider"] = (
            "Google" if page.locator(".gm-style").count()
            else ("MapLibre" if page.locator(".maplibregl-canvas").count() else "unknown")
        )
        row["screenshot"] = str(out / f"{name}-{width}.png")
        row["page_errors"] = errors
    except Exception as exc:
        row["error"] = type(exc).__name__ + ": " + str(exc).split("\n", 1)[0][:220]
    finally:
        page.remove_listener("pageerror", on_error)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://saferide-friday-web.onrender.com")
    parser.add_argument("--out", default="artifacts/codex-ui")
    args = parser.parse_args()
    base = approved_base(args.base_url)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "source": base,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "screens": [],
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900},
                                      reduced_motion="reduce", device_scale_factor=1)
        page = context.new_page()
        try:
            for w, h in VIEWPORTS:
                result["screens"].append(capture(page, base, "home", "/", w, h, out))
            for name, path in PUBLIC_PAGES.items():
                if name == "home":
                    continue
                for w, h in ((390, 844), (1440, 900)):
                    result["screens"].append(capture(page, base, name, path, w, h, out))
        finally:
            browser.close()
    report = out / "report.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    errors = sum(bool(r.get("error")) for r in result["screens"])
    print(f"Captured {len(result['screens'])-errors} screenshots; {errors} errors. Report: {report}")
    print("Open the screenshots in Codex to evaluate actual rendered UI.")


if __name__ == "__main__":
    main()
