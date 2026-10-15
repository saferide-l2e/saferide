"""Read-only Chromium landing QA. Local only; synthetic clip tests media mechanics.

SAFERIDE_AXE_PATH optionally points to a locally installed axe.min.js.
The colour-bars fixture is NOT cinematic footage or visual motion evidence.
"""
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = os.getenv("SAFERIDE_BROWSER_BASE", "http://127.0.0.1:8000")
if not BASE.startswith(("http://127.0.0.1:", "http://localhost:")):
    raise SystemExit("This check only accepts an isolated local instance.")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()
from django.template.loader import render_to_string  # noqa: E402

OUT = Path("artifacts/cinematic/final")
OUT.mkdir(parents=True, exist_ok=True)
report = {"screens": [], "accessibility": [], "pages": [], "errors": [], "media_fixture": {}}


def visit(page, path="/"):
    response = page.goto(BASE + path, wait_until="domcontentloaded")
    assert response.status == 200, (path, response.status)
    return response


def load_images(page):
    for image in page.locator('img[loading="lazy"]').all():
        image.scroll_into_view_if_needed()
        image.evaluate("image => image.decode()")
    page.evaluate("scrollTo(0,0)")
    page.wait_for_timeout(100)


def audit(page, path, theme, width):
    axe = os.getenv("SAFERIDE_AXE_PATH")
    if not axe:
        return
    page.add_script_tag(path=axe)
    failures = page.evaluate("""async () => (await axe.run(document, {
        runOnly:{type:'tag', values:['wcag2a','wcag2aa','wcag21aa']}
    })).violations.map(v=>({id:v.id, impact:v.impact, targets:v.nodes.map(n=>n.target)}))""")
    report["accessibility"].append({"path": path, "theme": theme, "width": width, "violations": failures})


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.getenv("SAFERIDE_CHROMIUM_PATH"), headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.on("pageerror", lambda error: report["errors"].append(str(error)))
    page.add_init_script("""window.layoutShiftScore=0;
      new PerformanceObserver(list=>list.getEntries().forEach(e=>{if(!e.hadRecentInput)window.layoutShiftScore+=e.value})).observe({type:'layout-shift',buffered:true});""")
    missing = []
    page.on("response", lambda response: missing.append(response.url) if response.status >= 400 and response.url.startswith(BASE + "/static/") else None)
    try:
        for width in [320, 360, 390, 430, 768, 1024, 1440, 1920]:
            page.set_viewport_size({"width": width, "height": 900})
            visit(page)
            load_images(page)
            expect(page.locator("#hero-title")).to_be_visible()
            assert page.locator("video").count() == 0
            state = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth-innerWidth,
              cls:window.layoutShiftScore,poster:document.querySelector('.cinematic-hero__poster').currentSrc,
              brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),
              lcp:performance.getEntriesByType('paint').map(e=>({name:e.name,ms:e.startTime}))})""")
            assert state["overflow"] <= 1, state
            assert not state["brokenImages"], state
            assert ("mobile.webp" in state["poster"]) == (width <= 700)
            assert state["cls"] < .1, state
            if width in [320, 390, 768, 1024, 1440]:
                page.screenshot(path=str(OUT / f"home-{width}.png"), full_page=True, animations="disabled", timeout=60000)
                page.screenshot(path=str(OUT / f"hero-{width}.png"))
            report["screens"].append({"width": width, **state})
            if width <= 430:
                menu = page.locator("[data-nav-toggle]")
                menu.click()
                expect(page.get_by_role("navigation", name="Main navigation")).to_be_visible()
                page.keyboard.press("Escape")
                expect(menu).to_have_attribute("aria-expanded", "false")
                expect(menu).to_be_focused()
        for theme in ["light", "dark"]:
            page.evaluate("theme=>{localStorage.setItem('saferide-color-theme',theme)}", theme)
            for width in [390, 1440]:
                page.set_viewport_size({"width": width, "height": 900})
                for path in ["/", "/how-it-works/", "/for-drivers/", "/safety-support/", "/accounts/login/", "/accounts/register/", "/departures/search/"]:
                    visit(page, path)
                    load_images(page)
                    expect(page.locator("html")).to_have_attribute("data-theme", theme)
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    audit(page, path, theme, width)
                    if width == 390 and (path != "/" or theme == "dark"):
                        name = path.strip("/").replace("/", "-") or "home"
                        page.screenshot(path=str(OUT / f"{name}-{theme}-{width}.png"), full_page=True, animations="disabled", timeout=60000)
                    report["pages"].append({"path": path, "theme": theme, "width": width})
        # Persistence and keyboard operation of the actual header control.
        page.locator("[data-theme-toggle]").focus()
        page.keyboard.press("Enter")
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        page.reload(wait_until="domcontentloaded")
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        visit(page)
        # Every homepage internal CTA resolves through Django, including login redirects.
        links = page.locator('main a[href^="/"]').evaluate_all("links=>[...new Set(links.map(a=>a.getAttribute('href')))]")
        for link in links:
            response = context.request.get(BASE + link)
            assert response.status == 200, (link, response.status)
        report["working_homepage_links"] = links
        page.locator("#site-from").fill("Yaba")
        page.locator("#site-to").fill("Ikeja")
        report["stage"] = "JavaScript-enabled route search submission"
        page.get_by_role("button", name="Find buses").click()
        assert "origin=Yaba" in page.url and "destination=Ikeja" in page.url
        report["search_query_preserved"] = True
        visit(page)
        for origin, destination in [("Jibowu", "Mile 2"), ("Lekki Phase 1", "Jibowu"), ("Yaba", "Ikeja"), ("Agege", "Oshodi"), ("Surulere", "CMS"), ("Maryland", "Victoria Island")]:
            page.locator("[data-map-origin]").select_option(origin)
            page.locator("[data-map-destination]").select_option(destination)
            expect(page.locator("[data-origin-label]")).to_have_text(origin)
            expect(page.locator("[data-destination-label]")).to_have_text(destination)
            expect(page.locator("#site-from")).to_have_value(origin)
            expect(page.locator("#site-to")).to_have_value(destination)
            assert destination in page.locator("[data-map-directions]").get_attribute("href").replace("%20", " ")
        report["map_selection_and_search_sync"] = "6 pairs, rapid changes; labels and external directions"
        # No-JavaScript remains a useful website, with native search and navigation.
        nojs = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
        plain = nojs.new_page()
        visit(plain)
        expect(plain.locator("#hero-title")).to_be_visible()
        expect(plain.get_by_role("navigation", name="Main navigation")).to_be_visible()
        plain.locator("#site-from").fill("Yaba")
        plain.locator("#site-to").fill("Ikeja")
        report["stage"] = "No-JavaScript route search submission"
        plain.get_by_role("button", name="Find buses").click()
        assert "origin=Yaba" in plain.url
        nojs.close()
        report["no_javascript"] = "Navigation, poster and GET search work"
        # Controlled, silent colour-bars video; tests component lifecycle, not art quality.
        fixture = Path("tests/fixtures/cinematic-test-pattern.mp4").read_bytes()
        webm_fixture = Path("tests/fixtures/cinematic-test-pattern.webm").read_bytes()
        fixture_hero = render_to_string("components/cinematic_hero.html", {"cinematic_video": {
            "desktop_webm": "/qa-fixture.webm", "mobile_webm": "/qa-fixture.webm",
            "desktop_mp4": "/qa-fixture.mp4", "mobile_mp4": "/qa-fixture.mp4",
        }})
        for mode in ["normal", "desktop", "reduced", "save-data", "failure", "autoplay-blocked"]:
            media_context = browser.new_context(viewport={"width": 1440 if mode == "desktop" else 390, "height": 844}, reduced_motion="reduce" if mode == "reduced" else "no-preference")
            media_page = media_context.new_page()
            requests = []
            report["stage"] = f"Native media lifecycle: {mode}"
            if mode == "save-data":
                media_page.add_init_script("Object.defineProperty(navigator,'connection',{value:{saveData:true,effectiveType:'4g',addEventListener(){}}})")
            if mode == "autoplay-blocked":
                media_page.add_init_script("HTMLMediaElement.prototype.play=()=>Promise.reject(new DOMException('Blocked by test','NotAllowedError'))")
            def media_response(route, request, *, requests=requests, mode=mode):
                requests.append(route.request.url)
                is_webm = request.url.endswith(".webm")
                route.fulfill(status=503 if mode == "failure" else 200, content_type="video/webm" if is_webm else "video/mp4", body=b"" if mode == "failure" else webm_fixture if is_webm else fixture)
            media_page.route("**/qa-fixture.*", media_response)
            def inject(route):
                response = route.fetch()
                html = re.sub(r'<section class="cinematic-hero".*?</section>', lambda match: fixture_hero, response.text(), count=1, flags=re.DOTALL)
                route.fulfill(response=response, body=html)
            media_page.route(re.compile(re.escape(BASE) + r"/$"), inject)
            visit(media_page)
            video = media_page.locator("video")
            support = video.evaluate("v=>({webm:v.canPlayType('video/webm; codecs=vp8'),h264:v.canPlayType('video/mp4; codecs=avc1.42E01E')})")
            if os.getenv("GITHUB_ACTIONS") and mode == "normal":
                print(f"::notice title=Native video codec support::{json.dumps(support)}", flush=True)
            if mode in ("normal", "desktop"):
                media_page.wait_for_function("document.querySelector('video').currentTime>.1")
                media_page.wait_for_timeout(1400)
                assert video.evaluate("v=>!v.paused && !v.ended && v.currentTime<v.duration")
                assert video.evaluate("v=>v.muted && v.loop && v.playsInline")
                report["stage"] = f"{mode} media pause/resume control"
                media_page.get_by_role("button", name="Pause scene").click()
                frozen = video.evaluate("v=>v.currentTime")
                media_page.wait_for_timeout(250)
                assert video.evaluate("v=>v.paused && Math.abs(v.currentTime-" + str(frozen) + ")<.05")
                media_page.get_by_role("button", name="Play scene").click()
                media_page.wait_for_function("!document.querySelector('video').paused")
                report["stage"] = f"{mode} media offscreen pause"
                media_page.evaluate("scrollTo(0,document.body.scrollHeight)")
                media_page.wait_for_function("document.querySelector('video').paused")
                media_page.evaluate("scrollTo(0,0)")
                media_page.wait_for_function("!document.querySelector('video').paused")
                media_page.emulate_media(reduced_motion="reduce")
                media_page.wait_for_function("document.querySelector('video').paused && !document.querySelector('video source')")
            else:
                media_page.wait_for_timeout(500)
                assert video.evaluate("v=>v.paused")
                assert not media_page.locator("[data-cinematic-hero]").evaluate("e=>e.classList.contains('is-playing')")
                if mode in ["reduced", "save-data"]:
                    assert not requests
            report["media_fixture"][mode] = {"passed": True, "media_requests": len(requests), "fixture_only": True, "webm_supported": video.evaluate("v=>v.canPlayType('video/webm; codecs=vp8')"), "h264_supported": video.evaluate("v=>v.canPlayType('video/mp4; codecs=avc1.42E01E')")}
            media_context.close()
        assert not missing, missing
        assert not report["errors"], report["errors"]
        violations = [v for result in report["accessibility"] for v in result["violations"]]
        assert not violations, violations
    except Exception as exc:
        report["failure"] = f"{report.get('stage', 'Landing checks')}: {type(exc).__name__}: {exc}"
        # GitHub annotations remain readable through the API when artifact/log
        # downloads are unavailable in a restricted development environment.
        annotation = report["failure"].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Cinematic landing QA::{annotation}", flush=True)
        raise
    finally:
        (OUT / "result.json").write_text(json.dumps(report, indent=2))
        browser.close()
print(json.dumps({"screens": len(report["screens"]), "pages": len(report["pages"]), "axe_audits": len(report["accessibility"]), "fixture_modes": report["media_fixture"], "errors": report["errors"]}, indent=2))
