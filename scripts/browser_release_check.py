"""Chromium UI journey checks on a LOCAL, isolated CI PostgreSQL database only.

Produces screenshots and JSON evidence; intentionally never targets production.
"""
import json
import os
import re
import uuid
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get("SAFERIDE_BROWSER_BASE", "http://127.0.0.1:8000")
if not BASE.startswith(("http://127.0.0.1:", "http://localhost:")):
    raise SystemExit("Browser QA refuses to touch a remote/production host.")

OUT = Path("artifacts/browser")
OUT.mkdir(parents=True, exist_ok=True)
viewports = [(320, 700), (390, 844), (768, 1024), (1024, 768), (1440, 900)]
evidence = {"base": BASE, "screens": [], "journeys": [], "page_errors": []}


def visit(page, path):
    response = page.goto(BASE + path, wait_until="domcontentloaded", timeout=30000)
    assert response is not None and response.status < 400, (path, response.status if response else None)
    return response


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True, executable_path=os.getenv("SAFERIDE_CHROMIUM_PATH"))
    page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    page.on("pageerror", lambda exc: evidence["page_errors"].append(str(exc)[:300]))
    try:
        for width, height in viewports:
            page.set_viewport_size({"width": width, "height": height})
            visit(page, "/")
            page.wait_for_timeout(850)
            page.screenshot(path=str(OUT / f"home-{width}.png"), full_page=True)
            overflow = page.evaluate(
                "() => Math.max(document.body.scrollWidth,document.documentElement.scrollWidth) - window.innerWidth"
            )
            map_state = page.locator("[data-route-hero]").get_attribute("data-map-state")
            evidence["screens"].append({
                "width": width,
                "height": height,
                "horizontal_overflow_px": overflow,
                "map_state": map_state,
            })
            assert overflow <= 5, f"{width}px viewport overflows horizontally by {overflow}px"
            expect(page.locator("h1#hero-title")).to_be_visible()
            if width <= 390:
                toggle = page.locator("[data-nav-toggle]")
                expect(toggle).to_be_visible()
                toggle.click()
                assert toggle.get_attribute("aria-expanded") == "true"
                expect(page.locator('a[href="/accounts/register/"]').first).to_be_visible()
                toggle.click()

        page.set_viewport_size({"width": 1440, "height": 900})
        visit(page, "/")
        page.locator("[data-map-destination]").select_option(label="Ikeja")
        expect(page.locator("[data-destination-label]")).to_have_text("Ikeja")
        expect(page.locator("#site-to")).to_have_value("Ikeja")
        page.screenshot(path=str(OUT / "lagos-map-ikeja-selected.png"), full_page=True)
        page.locator("[data-theme-toggle]").click()
        assert page.locator("html").get_attribute("data-theme") == "dark"
        page.reload(wait_until="domcontentloaded")
        assert page.locator("html").get_attribute("data-theme") == "dark"
        page.locator("[data-theme-toggle]").click()
        assert page.locator("[data-map-motion]").count() == 0
        assert page.locator("[data-map-provider]").count() == 0
        evidence["journeys"].append("Lagos stops update route and search; no broken theme or animation controls")

        visit(page, "/departures/search/?origin=Agege&destination=Lekki%20Phase%201")
        expect(page.get_by_role("heading", name="No matching departures")).to_be_visible()
        assert page.locator(".demo-bus-card").count() == 0
        page.screenshot(path=str(OUT / "unpublished-route-empty.png"), full_page=True)
        evidence["journeys"].append("Unpublished routes show an honest empty state without fictional buses")

        visit(page, "/accounts/register/?role=DRIVER")
        assert page.locator('input[name="role"][value="DRIVER"]').is_checked()
        evidence["journeys"].append("Driver signup CTA preselects driver")

        visit(page, "/accounts/register/")
        page.locator('input[name="display_name"]').fill("Browser QA Passenger")
        page.locator('input[name="email"]').fill(f"browser-qa-{uuid.uuid4().hex[:12]}@example.test")
        page.locator('input[name="role"][value="PASSENGER"]').check()
        page.locator('input[name="password1"]').fill("BrowserStrongPassword!2026")
        page.locator('input[name="password2"]').fill("BrowserStrongPassword!2026")
        page.get_by_role("button", name=re.compile("Create account")).click()
        page.wait_for_url("**/verification/", timeout=20000)
        expect(page.locator('form#verification-declaration')).to_be_visible()
        page.screenshot(path=str(OUT / "verification-before.png"), full_page=True)
        page.locator('input[name="fictional_data"]').check()
        page.locator('input[name="simulated_review"]').check()
        page.get_by_role("button", name=re.compile("Submit for staff review")).click()
        expect(page.get_by_text("Profile submitted")).to_be_visible()
        page.screenshot(path=str(OUT / "verification-pending.png"), full_page=True)
        evidence["journeys"].append("Browser registration -> fictional declaration -> pending staff review")

        page.locator(".nav-logout-form button").click()
        visit(page, "/accounts/login/")
        page.locator('input[name="email"]').fill(os.getenv("SAFERIDE_BROWSER_PASSENGER_EMAIL", "passenger@example.test"))
        page.locator('input[name="password"]').fill(os.getenv("SAFERIDE_BROWSER_PASSENGER_PASSWORD", "saferide-demo-123"))
        page.get_by_role("button", name=re.compile("Sign in")).click()
        page.wait_for_url("**/dashboard/", timeout=20000)
        visit(page, "/departures/search/?origin=Jibowu&destination=Mile%202")
        expect(page.get_by_role("link", name=re.compile("View bus")).first).to_be_visible()
        candidates = page.get_by_role("link", name=re.compile("View bus")).evaluate_all(
            "links => links.map(link => link.getAttribute('href'))"
        )
        for candidate in candidates:
            visit(page, candidate)
            if page.get_by_role("button", name=re.compile("Reserve one seat")).count():
                break
        else:
            raise AssertionError("Seed an available isolated local departure for the browser passenger")
        page.screenshot(path=str(OUT / "published-driver-details.png"), full_page=True)
        match = re.search(r"/departures/([0-9a-f-]{36})/", page.url)
        assert match, page.url
        departure_id = match.group(1)
        page.get_by_role("button", name=re.compile("Reserve one seat")).click()
        page.wait_for_url(re.compile(r"/bookings/[0-9a-f-]{36}/"), timeout=20000)
        code = page.locator("[data-boarding-code] strong").inner_text()
        assert len(code) == 6 and code.isdigit()
        page.screenshot(path=str(OUT / "passenger-reservation.png"), full_page=True, mask=[page.locator("[data-boarding-code]")])
        evidence["journeys"].append("Verified passenger login -> route search -> seat hold -> private code")

        page.locator(".nav-logout-form button").click()
        visit(page, "/accounts/login/")
        page.locator('input[name="email"]').fill("driver@example.test")
        page.locator('input[name="password"]').fill("saferide-demo-123")
        page.get_by_role("button", name=re.compile("Sign in")).click()
        page.wait_for_url("**/dashboard/", timeout=20000)
        visit(page, f"/departures/driver/{departure_id}/manage/")
        expect(page.get_by_text("Private passenger roster")).to_be_visible()
        page.locator('input[name="code"]').fill(code)
        page.get_by_role("button", name=re.compile("Check in")).click()
        expect(page.get_by_text("Passenger boarded.")).to_be_visible()
        page.screenshot(path=str(OUT / "driver-checkin.png"), full_page=True)
        evidence["journeys"].append("Approved driver sees roster -> checks in boarding code")
    except Exception as exc:
        evidence["failure"] = f"{type(exc).__name__}: {exc}"
        page.screenshot(path=str(OUT / "failure.png"), full_page=True, mask=[page.locator("[data-boarding-code]")])
        raise
    finally:
        (OUT / "qa-result.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        browser.close()
