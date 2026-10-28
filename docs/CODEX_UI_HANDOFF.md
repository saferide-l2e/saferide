# SafeRide — Codex UI + Browser Handover
**Updated:** 28 October 2026 · **Purpose:** Continue investor-grade UI work with visual browser evidence, safely.

> **Codex: open the real website in Chromium before writing code.** The live UI and current code are newer than the October 15 handover. This document replaces the older branch instructions. This is a real Django product; do not treat it as the 25-screen preview gallery or swap its stack for React.

## 1. Start here — authoritative status

| Item | Exact location / status |
|---|---|
| GitHub repository | https://github.com/saferide-l2e/saferide |
| **Current baseline** | `main`, commit `0255ced56595` (16 October 2026) |
| **Safe Codex working branch** | `codex/ui-browser-review-2026-10-28`, created from current `main` |
| Live website, **read-only UI reference** | https://saferide-friday-web.onrender.com/ |
| Render web service | https://dashboard.render.com/web/srv-db8b7mhsrm7s73e216bg |
| Render deploy branch | `deploy/render-demo-2026-10-16`, currently at the **same SHA as main** |
| Render deployment last verified | **LIVE**, deployed commit `0255ced56595` (Render API, checked 28 October) |
| Existing UI handover (historical) | `docs/CODEX_UI_HANDOFF.md` at older revisions |
| Current feature/workflow specification | `docs/WORKFLOWS.md` (39 URL routes + admin; prepared 16 October) |
| Original teammate Figma | https://www.figma.com/design/hOvnMbooxS9EW7t2mjxYmU/SafeRide-L2E?node-id=0-1 |
| SafeRide alternate design space | https://www.figma.com/design/ztF1QqN7Npu55gnJwZVrG7 |
| CI baseline | GitHub Actions on `main` (last completed run succeeded at that SHA) |

**What changed since the previous handover:** the actual homepage now uses a cinematic Lagos poster and a separate interactive map/route preview **below** the opening search/storytelling section; the site includes light/dark mode, real-road mapping with Google Maps or MapLibre/OpenFreeMap + OSRM fallback, several public pages and Django passenger/driver workflows. The current map code explicitly removed the previously discussed moving-bus animation. Do not assume a 3D danfo currently moves on the map: **inspect before changing**. The earlier notes that said `main` lacks UI merges are obsolete. A prior UI branch `codex/ui-visual-polish-handoff` exists but is **older** than `main`: do not branch from it.

**Deployment caution:** Render's free web service may sleep when idle. The site was confirmed LIVE by the Render API, **not independently re-inspected in a graphical browser in this handover**. Verify browser status rather than assuming the full site functions. The free PostgreSQL database was set to expire 14 November 2026: check its status before relying on it; do not use live data for automated tests.

## 2. Product and design intent

SafeRide is a professional Lagos transport **web application** (Django 5.2, HTML5, CSS3, vanilla JavaScript, PostgreSQL, Django Admin). It should be credible enough to pitch to a serious investor, but never imply operational features that are not implemented.

**Public navigation:** Find a Ride · How It Works · For Drivers · Safety & Support · Sign In · Get Started.

**Signed-in passenger:** search/results → driver/bus detail → server-backed 10-minute seat hold → FIFO waitlist/120-second offer if full → private single-use boarding code → trip/arrival → history, rating, private reports.

**Signed-in driver:** account/profile → vehicle approval → publish departure → assigned roster → code check-in → depart → driver arrival. Staff/automatic eligibility workflows have changed from the old October 15 description; consult `docs/WORKFLOWS.md` and `docs/FIVE_SECOND_APPROVALS.md` before editing any approval copy.

**Visual direction:** premium, memorable Lagos transport brand: deep green/forest, lime accents, warm editorial photography/illustration, generous whitespace, clear action hierarchy, useful motion and accessibility. Responsively designed at 320, 390, 768, 1024, 1440px and 200% zoom. Retain original teammate contributions and do **not** overwrite her Figma source.

**Truthfulness:** The cinematic Lagos assets are original *generated composite illustrations*, not actual operating-user photography. An optional cinematic video infrastructure exists but a finished scene has **not** been confirmed. The map displays real streets and route geometry, **not GPS tracking of a real bus**. The team operates fictional/pilot data, and automatic account/vehicle approval is application-state automation, not government KYC, background checks or vehicle inspection. Payment, insurance, emergency dispatch and actual fleet telemetry must not be invented or represented as live.

## 3. How Codex must OPEN the UI in a browser

### A. Git checkout
```bash
git clone https://github.com/saferide-l2e/saferide.git
cd saferide
git fetch origin
git switch codex/ui-browser-review-2026-10-28
git pull --ff-only
cat AGENTS.md
```

If you use **Codex's own browser/computer-use environment**, navigate to the URL below, open developer console, inspect responsive layouts and capture screenshots. If there is no built-in browser, use **Playwright/Chromium**, not just HTML fetching or curl. The user specifically wants Codex to **see the rendered UI**.

### B. Automatic PUBLIC-site screenshot runner (no login, no writes)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install playwright
python -m playwright install chromium
python scripts/codex_public_ui_capture.py --base-url https://saferide-friday-web.onrender.com
```

This opens an actual headless Chromium browser, captures screenshots at **320/390/768/1024/1440** for home and **390/1440** for other public pages, checks horizontal overflow and records public page status. Outputs:
- `artifacts/codex-ui/*.png` (browser screenshots)
- `artifacts/codex-ui/report.json` (screen dimensions/status/UI errors)

**Safety:** This runner is intentionally GET-only; it **does not log in, submit forms, reserve seats or modify Render PostgreSQL**. It only accepts the SafeRide Render host or localhost to prevent accidental crawls of unrelated sites. The map's external network requests may be blocked in some Chromium environments; record the specific failure. Do not claim you saw the map unless the screenshot supports it.

If using a remote Codex container without GUI, headless Chromium/Playwright still counts as browser inspection. Open the generated screenshots in Codex's image viewer. **If Codex cannot open Chromium or images, report that rather than claiming visual validation.**

### C. Local UI-edit preview (NOT the real Render DB)
Install local dependencies and point to a separate PostgreSQL instance:
```bash
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env locally: unique DJANGO_SECRET_KEY, DEBUG=true,
# and a LOCAL PostgreSQL DATABASE_URL; never reuse production credentials.
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/` **in the same browser context where you run Django**, and run:
```bash
python scripts/codex_public_ui_capture.py --base-url http://127.0.0.1:8000 --out artifacts/codex-ui-after
```

No local PostgreSQL? Start with the **read-only remote browser inspection**, then set up an isolated development DB before running full passenger or driver E2E checks. Do not point local tests at Render's production database.

### D. Existing specialised browser tests
```bash
# Local-only browser test that exercises real user workflows with a local DB:
python scripts/browser_release_check.py

# Optional map-focused Chromium tests (needs Node + Playwright + Chromium):
node --test tests/js/*.test.cjs
node scripts/browser_map_check.cjs
node scripts/browser_map_check.cjs --keyless
```

`scripts/browser_release_check.py` refuses remote hosts by design. `scripts/browser_map_check.cjs` expects the Node package `playwright` and often `/usr/bin/chromium`; install these or configure `SAFERIDE_CHROMIUM_PATH` if necessary. Do not run its state-changing local workflow checks against Render.

## 4. Public pages to inspect first

| Public page | URL | What to check |
|---|---|---|
| Home | https://saferide-friday-web.onrender.com/ | cinematic poster, headline, CTA, mobile crop, search, map, driver feature, footer |
| How It Works | /how-it-works/ | story hierarchy, steps, calls to action |
| For Drivers | /for-drivers/ | driver value proposition and signup |
| Safety & Support | /safety-support/ | readable safety disclosures, clear contact/report entry |
| Find a Ride | /departures/search/?origin=Jibowu&destination=Mile+2 | real departures vs sample suggestions, contrast and filters |
| Login | /accounts/login/ | authentic form and errors, dark/light |
| Register | /accounts/register/ | passenger/driver roles, mobile keyboard, field errors |

The exact current page/action inventory is in `docs/WORKFLOWS.md`, including 39 web routes. Log in only with separately approved **fictional** test credentials; obtain them securely, not via screenshots, GitHub or prompts. Never screenshot private boarding codes or personal documents.

## 5. UI code map — files that matter now

**Structure**
- `templates/base.html` — shared header/nav, theme, footer, authentication state.
- `templates/home.html` — homepage layout, includes, sections, metadata.
- `templates/components/cinematic_hero.html` — large media hero/overlay/actions.
- `templates/components/ride_search.html` — actual origin/destination GET search.
- `templates/components/route_preview.html` — selectable public stop map below hero.
- `templates/components/journey_steps.html`, `journey_art.html` — product story visuals.
- `templates/components/*`, `templates/passenger/*`, `templates/driver/*`, `templates/accounts/*`, `templates/booking/*`, `templates/safety/*` — full UI.
- `apps/core/views.py` and `apps/*/views.py` — Django view → template contexts. Avoid changing backend services for cosmetic work.
- `apps/bookings/services.py`, `apps/departures/services.py` — server-authoritative booking, queue, check-in and lifecycle (don't rewrite for UI).

**Style and interactive assets**
- `static/css/cinematic_hero.css`; `static/js/cinematic_hero.js` — responsive media and optional video.
- `static/css/lagos_experience.css`; `static/js/lagos_experience.js`; `static/js/theme_init.js` — responsive public design and theme.
- `static/css/site_public.css`; `static/css/site_route.css` — public layout and route visuals.
- `static/js/hero_route.js` — currently real-road route preview; no claimed live vehicle motion.
- `static/media/saferide-lagos-poster.webp`, `saferide-lagos-mobile.webp`, `saferide-lagos-driver.webp` — original generated Lagos imagery.

**Design and test evidence**
- `docs/CINEMATIC_LANDING_HANDOFF.md`, `docs/LAGOS_EXPERIENCE_HANDOFF.md`, `docs/LAGOS_MAP_HERO.md`.
- `docs/evidence/cinematic/` and `docs/evidence/danfo/` contain historical viewport and map screenshots/videos; check provenance and whether they match current release.
- `tests/test_cinematic_landing.py`, `tests/test_lagos_experience.py`, `tests/test_lagos_map_hero.py`, `tests/js/*.test.cjs`.
- `docs/WORKFLOWS.md` — latest authoritative product paths and state transitions.

## 6. First UI tasks and acceptance conditions

1. **Baseline browser audit.** Screenshot the actual homepage at 320, 390, 768, 1024 and 1440; all public landing pages at 390 and 1440. Record exactly which map provider loaded, whether road routing succeeded, and the site revision.
2. **Hero and visual polish.** Fix any cropped content, weak type scale, awkward spacing, overly tall mobile sections, slow image loading or missing responsive alignment. Don't revert the cinematic homepage to a developer gallery.
3. **Real images/motion.** Use original or properly licensed visuals (never scrape random protected photos). Distinguish generated artwork from live documentary photography. Only add motion that serves a purpose, with pause and reduced-motion support.
4. **Real-route map QA.** Test stop selection, route geometry, labeling, provider fallback, keyboard, attribution, native Google logo/terms, directions and connection to route search. **Don't animate a danfo through imaginary streets**; any vehicle motion is purely illustrative, not GPS. The current route code may deliberately have no motion, so agree on the new desired behaviour before adding it.
5. **Real frontend states.** Check search empty/results, error states, booking CTA eligibility, login/register, account/vehicle status on real Django routes, and driver vs passenger navigation. No fake successful booking on click.
6. **Accessibility/performance.** Responsive 320–1440, zoom 200%, keyboard, touch targets, contrast in both themes, reduced motion, JavaScript error and failed-network cases.

**Deliverables for Codex:** before/after screenshots, specific browser-observed bugs, code edits limited to UI where possible, test output and an ordinary PR from the Codex branch to `main` for review. **Do not merge or deploy without the team reviewing.** Render follows `deploy/render-demo-2026-10-16`, so a PR into `main` does **not** automatically update the live site.

## 7. Security and access rules

- A Google Maps browser API key was exposed earlier in chat. **Rotate that key and restrict the new key by allowed HTTP referrers and Maps APIs**. Never paste an API key in the repo, README, screenshots, test logs or prompts. The browser key is deliberately public in page source, so referrer/API restrictions and quotas matter.
- Never copy or log `DATABASE_URL`, `DJANGO_SECRET_KEY`, Render passwords, private boarding codes or personal data.
- If you cannot see the live site because of Render free-tier sleep, sign-in, network restrictions or missing Chromium, state the blocker precisely and take the safe local-browser route.
- Do not change protected Django service logic, ownership checks, 600s holds, 120s FIFO offers, or privacy controls for a visual redesign.
- Keep collaborator attribution and original Figma file untouched.
- Do not claim payment, insurance, verified driver identities, emergency dispatch or fleet GPS exists.

## 8. Ready-to-paste Codex task

> Continue SafeRide UI from the current repo branch `codex/ui-browser-review-2026-10-28`. Read `AGENTS.md`, `docs/CODEX_UI_HANDOFF.md`, and `docs/WORKFLOWS.md`. First **open https://saferide-friday-web.onrender.com/ in a real Chromium browser**, not only source HTML, or run `python scripts/codex_public_ui_capture.py` and inspect the PNGs. Capture real screenshots of home at widths 320, 390, 768, 1024 and 1440, plus the public pages at 390/1440. Verify the map, search, console errors, theme and responsive layouts. This is the current cinematic Lagos homepage—not the old 25-page gallery. Write a screenshot-based UI defect list, then implement the highest-impact visual fixes on this branch using Django templates, CSS and vanilla JS. Preview changes locally using a separate PostgreSQL DB; no live DB writes, secrets, auto-deploy or direct `main` merges. Run Ruff/Django/PostgreSQL tests, share before/after screenshots and open a PR for team review. Do not claim a graphical inspection unless images were actually captured and examined.

## 9. How to report progress

Provide: (a) actual Render response, screenshot filenames and dimensions; (b) browser-visible UI issues ranked by severity; (c) what code files changed; (d) before/after screenshots for each significant change; (e) tested viewports and test commands/results; (f) what remains unverified; (g) PR URL. Any browser limitations must be stated explicitly.
