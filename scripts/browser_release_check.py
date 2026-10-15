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

        # Search eligibility notice uses theme text tokens, including its link.
        visit(page, "/departures/search/?origin=Jibowu&destination=Mile%202")
        notice = page.locator(".eligibility-note")
        expect(notice).to_be_visible()
        for theme in ("light", "dark"):
            page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
            for selector in (".eligibility-note", ".eligibility-note a"):
                contrast = page.locator(selector).evaluate("""element => {
                    const luminance = colour => colour.match(/[\\d.]+/g).slice(0, 3)
                        .map(Number).map(v => v / 255)
                        .map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
                        .reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
                    const a = luminance(getComputedStyle(element).color);
                    const b = luminance(getComputedStyle(element.closest('.eligibility-note')).backgroundColor);
                    return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
                }""")
                assert contrast >= 4.5, f"{theme} {selector} contrast: {contrast}"
            for width, height in viewports:
                page.set_viewport_size({"width": width, "height": height})
                notice.scroll_into_view_if_needed()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(OUT / f"search-notice-{theme}-{width}.png"))
        page.evaluate("document.documentElement.dataset.theme = 'light'")

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
        role_group = page.get_by_role("group", name="How will you use SafeRide?")
        for width, height in viewports:
            page.set_viewport_size({"width": width, "height": height})
            role_group.scroll_into_view_if_needed()
            for radio in role_group.get_by_role("radio").all():
                bounds = radio.bounding_box()
                assert bounds and 16 <= bounds["width"] <= 24 and 16 <= bounds["height"] <= 24
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            # Empty fields can escape an automated text-contrast audit. Verify
            # actual input foreground/background colours, including dark mode.
            for theme in ("light", "dark"):
                page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
                contrast = page.locator('[name="display_name"]').evaluate("""input => {
                    const style = getComputedStyle(input);
                    const luminance = colour => colour.match(/[\\d.]+/g).slice(0, 3)
                        .map(Number).map(v => v / 255)
                        .map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
                        .reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
                    const a = luminance(style.color), b = luminance(style.backgroundColor);
                    return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
                }""")
                assert contrast >= 4.5, (width, theme, contrast)
            page.evaluate("document.documentElement.dataset.theme = 'light'")
            page.screenshot(path=str(OUT / f"signup-role-{width}.png"))
        role_group.get_by_role("radio", name=re.compile("Passenger")).focus()
        page.keyboard.press("ArrowRight")
        assert role_group.get_by_role("radio", name=re.compile("Driver")).is_checked()
        page.set_viewport_size({"width": 1440, "height": 900})
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

        visit(page, "/driver/vehicles/new/")
        expect(page.get_by_role("button", name=re.compile("Submit for review"))).to_be_visible()
        page.locator('[name="plate_display"]').fill("QA-" + uuid.uuid4().hex[:8].upper())
        page.locator('[name="vehicle_type"]').fill("Toyota Hiace")
        page.locator('[name="capacity"]').fill("10")
        page.get_by_role("button", name=re.compile("Submit for review")).click()
        page.wait_for_url("**/driver/vehicles/")
        expect(page.get_by_text("Vehicle submitted. An administrator must approve it.")).to_be_visible()
        evidence["journeys"].append("Approved driver submits vehicle for staff review")

        page.locator(".nav-logout-form button").click()
        visit(page, "/accounts/register/?role=DRIVER")
        page.locator('[name="display_name"]').fill("Vehicle Onboarding QA")
        page.locator('[name="email"]').fill(f"vehicle-qa-{uuid.uuid4().hex[:12]}@example.test")
        page.locator('[name="password1"]').fill("BrowserStrongPassword!2026")
        page.locator('[name="password2"]').fill("BrowserStrongPassword!2026")
        page.get_by_role("button", name=re.compile("Create account")).click()
        page.wait_for_url("**/verification/")
        visit(page, "/driver/vehicles/new/")
        expect(page.get_by_role("heading", name="Account approval required")).to_be_visible()
        assert page.locator('[name="plate_display"]').count() == 0
        token = page.locator('[name="csrfmiddlewaretoken"]').first.input_value()
        response = page.request.post(BASE + "/driver/vehicles/new/", form={
            "csrfmiddlewaretoken": token, "plate_display": "QA-BLOCKED",
            "vehicle_type": "Toyota Hiace", "capacity": "10",
        })
        assert response.status == 200
        assert "Account approval required" in response.text()
        for theme in ("light", "dark"):
            page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
            for width, height in viewports:
                page.set_viewport_size({"width": width, "height": height})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(OUT / f"vehicle-approval-{theme}-{width}.png"))
        page.get_by_role("link", name=re.compile("Review account status")).click()
        page.wait_for_url("**/verification/")
        expect(page.locator("#verification-declaration")).to_be_visible()
        evidence["journeys"].append("Unapproved driver gets account review guidance, including stale form POST")
    except Exception as exc:
        evidence["failure"] = f"{type(exc).__name__}: {exc}"
        page.screenshot(path=str(OUT / "failure.png"), full_page=True, mask=[page.locator("[data-boarding-code]")])
        raise
    finally:
        (OUT / "qa-result.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        browser.close()
