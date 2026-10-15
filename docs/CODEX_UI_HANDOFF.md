# SafeRide — Codex UI/UX & Browser Handover
**Prepared:** 15 October 2026 · **Presentation:** Friday, 16 October 2026 · **Priority:** outstanding visual quality and trustworthy functioning flows.

> **Start here, Codex.** This document is the authoritative handover for continuing SafeRide's UI. Inspect the actual site with a **real browser and screenshots before editing**. Work safely on the handover feature branch; do not push directly to main or the auto-deployed Render branch. Do not invent successful bookings, driver screening or GPS tracking.

## 1. What SafeRide is

SafeRide is a Lagos-focused **responsive web application**, not a native app and not just a portfolio mockup. Passengers should be able to discover routes and buses, see their stops and permitted driver information, reserve seats with a 10-minute server-side hold, receive a private single-use boarding code, follow trip milestones and privately report safety concerns. Drivers register vehicles, publish eligible departures, manage their assigned passenger roster, check boarding codes and record arrival. Staff moderate identity submissions, vehicle approvals, reports and route updates. Some verification and transport data in the Friday presentation is fictional/pilot data; never present simulated checks as official identity or criminal-background checks.

**Design bar:** professional Lagos transport technology company with a credible investor-pitch experience: beautiful photography (properly licensed), excellent mobile/tablet/desktop layout, restrained elegant animation, delightful but purposeful interactions, fast perceived loading, accessibility and consistent design language. The user explicitly rejected an all-screens gallery as a homepage and rejected public menus named "Discover / Journey / Safety / Driver Space."

**Public nav:** **Find a Ride | How It Works | For Drivers | Safety & Support** plus **Sign In / Get Started**. After login, show **passenger** navigation (Find a Ride, My Trips, Route Updates, Account) or **driver** navigation (Dashboard, My Vehicles, Departures, Account). A 25-screen internal gallery existed in an earlier preview but must not be presented as the customer site.

## 2. Verified URLs, repository, branch order

| Purpose | Link/identifier |
|---|---|
| **Live site to inspect in browser** | https://saferide-friday-web.onrender.com/ |
| Render web dashboard | https://dashboard.render.com/web/srv-db8b7mhsrm7s73e216bg |
| Render PostgreSQL dashboard | https://dashboard.render.com/d/dpg-db8b5vgm7kps73doubrg-a |
| Private GitHub repo | https://github.com/saferide-l2e/saferide |
| **Codex working branch; START HERE** | **codex/ui-visual-polish-handoff** |
| Currently auto-deployed Render branch | deploy/render-demo-2026-10-16 |
| Full-stack FE+BE review | PR #67: https://github.com/saferide-l2e/saferide/pull/67 |
| Render deploy review | PR #69: https://github.com/saferide-l2e/saferide/pull/69 |
| Map + animated bus | PR #71: https://github.com/saferide-l2e/saferide/pull/71 — **MERGED into Render branch** |
| Original teammate Figma | https://www.figma.com/design/hOvnMbooxS9EW7t2mjxYmU/SafeRide-L2E?node-id=0-1 |

**As checked 15 October:** Render service is **LIVE**, running a Django web service with a connected free PostgreSQL database; latest observed Render deployment commit starts **04c49a8bf05c**. The map PR was merged into the Render branch; it was not merged to `main`. The map feature branch's CI passed: https://github.com/saferide-l2e/saferide/actions/runs/38739635917 . The code is integrated and CI-tested, but browser-validated Google route rendering, smooth animation and all transactional user journeys have **not** been established by that evidence.

The Render free database is temporary (planned expiry **14 November 2026**); keep only fictional sample information in the presentation database. Avoid destructive schema/data changes.

## 3. Safe branch workflow and browser access

### First thing to do
1. Connect Codex to `saferide-l2e/saferide` and select `codex/ui-visual-polish-handoff` (not `main`, not Render's auto-deployed branch). If working locally:
   ```bash
   git clone https://github.com/saferide-l2e/saferide.git
   cd saferide
   git fetch origin
   git switch codex/ui-visual-polish-handoff
   git pull --ff-only
   ```
2. Read `AGENTS.md` and this document, then `docs/LAGOS_MAP_HERO.md`, `docs/RENDER_SHOWCASE_DEPLOY.md`, `docs/TEAM_FRONTEND.md`, and the current templates/CSS/JS.
3. **OPEN https://saferide-friday-web.onrender.com/ in the browser** with a real rendering engine. Codex should use its browser/computer-use interface **if available**, otherwise use a local Playwright/Chromium browser and take screenshots. Browsing HTML/source alone does not show layout problems.
4. Before editing, capture at least five **baseline** screenshots: public homepage **1440×900 desktop**, **1024×768 laptop**, **768×1024 tablet**, **390×844 phone** and **320×700 small phone**. Also inspect sign-in, bus search/results, bus detail, booking, My Trips and driver dashboard. Report UI bugs with screenshots and console/network logs. Confirm if the public site currently shows Google Maps, OpenStreetMap, or an error/fallback.
5. Edit on the **Codex working branch only**. To inspect changes, run the local Django server and open its localhost URL **in the same browser environment**, or create a *separate* staging web service/preview. The existing public Render URL is your **baseline**, not an automatic live preview of unmerged Codex edits.
6. Submit PR back to `deploy/render-demo-2026-10-16` for review and safe deployment, not directly to `main`. Leave other contributors' work and Figma files intact.

### Run locally (if a local PostgreSQL development DB is available)
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Create a LOCAL .env using .env.example; supply a unique local DJANGO_SECRET_KEY,
# DEBUG=true and a local PostgreSQL DATABASE_URL. NEVER use live Render DB credentials
# in screenshots, prompts, commits, or untrusted environments.
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```
Then open **http://127.0.0.1:8000/** in Codex's browser and capture after-screenshots. **Do not point local experiments at the presentation's production PostgreSQL database.** If no local DB, use only the live public site for initial visual inspection and ask for an approved isolated staging setup before runtime testing.

Browser checks: viewport widths **320, 390, 768, 1024, 1440**; tab/Enter/Escape keyboard navigation; 200% zoom; reduced-motion mode; page horizontal scroll; forms and error focus states; map loading and error cases; image load and CLS; console/runtime errors; fonts, spacing, contrast and touch target size. Use Playwright screenshots where available. If Codex cannot access a browser, explicitly report that blocker rather than claiming the UI was inspected.

## 4. CURRENT homepage map work — inspect and improve it

The user showed that on desktop the original illustration sat **beneath the headline**. The fix in merged PR #71 introduces a side-by-side hero on wide screens and a real map route experience.

**Files to inspect first:**
- `templates/home.html` — hero headline, `data-route-hero`, live route map container, search form and homepage sections.
- `static/css/site_public.css` — global public site layouts and breakpoint declarations.
- `static/css/site_route.css` — new map card styling and **>=980px two-column override**. Check specificity/breakpoints carefully.
- `static/js/hero_route.js` — Google Maps JavaScript Routes API attempted first when a browser key is configured; otherwise Leaflet/OpenStreetMap and public OSRM road geometry. SVG/imaginary curve must **not** replace real road routing.
- `static/img/danfo-3d.webp` — original **3D-*styled* illustrated image** of a yellow Lagos danfo; this is not an interactive 3D mesh.
- `apps/core/views.py` — passes `GOOGLE_MAPS_BROWSER_KEY` into the homepage as browser-visible data, if configured.
- `tests/test_lagos_map_hero.py`, `docs/LAGOS_MAP_HERO.md` — existing map tests/implementation notes.

**Geography:** Jibowu public stop vicinity ~**6.52104, 3.36779** and Mile 2 interchange vicinity ~**6.45998, 3.31175** in Lagos. These are approximate stop coordinates, **not confirmed operator boarding bays**. Street map with real stops, a real **driving route polyline**, and a yellow 3D-styled danfo marker following it at a reasonable speed (currently ~22s simulated loop). This is an **animated illustration**, not live vehicle GPS. External **Open in Google Maps** link is required.

**Google key security:** The user pasted a Google Maps API key in chat. **DO NOT put that key in repository files, documentation, screenshots, issue comments or PR descriptions.** Treat it as exposed; recommend **rotating and locking it down** in Google Cloud Console. Use a new **HTTP referrer-restricted browser key** (only trusted SafeRide site URLs) and restrict enabled APIs/quota/billing. Configure it in Render as `GOOGLE_MAPS_BROWSER_KEY` after the restrictions are set. Browser API keys are visible to browser visitors by design; referer/API restrictions are essential. Do not assume the key is currently configured or that the Google route request is working until seen in the actual browser/network panel.

**Fallback:** With no configured Google key, the existing JS attempts Leaflet + OpenStreetMap tiles and public OSRM driving geometry. If routing fails, keep real map/stop markers and direct Google Maps directions; do not draw a convincing but false road path. Public OSM tiles and public OSRM sample routing are not guaranteed infrastructure for a high-traffic product.

**UI improvements requested:** desktop map beside copy at reasonable widths (avoid vertical stacking at desktop); a premium map card, strong colours, realistic geographic detail, smooth attractive moving yellow danfo along the **road line**, visibly real Jibowu/Mile 2 labels, accessible animation pause/reduce-motion and sensible 320px/mobile layout. A 3D-styled marker is acceptable for the next-day pitch, but don't claim true real-time 3D navigation.

## 5. Entire website redesign scope — in priority order

1. **Hero & homepage**: beautiful credible headline and CTA, photo/illustration quality, live map card to the right on desktop and stacked on mobile, working origin/destination search, strong rhythm/whitespace, subtle motion, appropriate real Lagos/public transport images with verified reuse rights, efficient loading.
2. **Public pages:** routes/results, bus detail with public driver approval indicators, How It Works, For Drivers, Safety & Support, login and registration. Public menus should be natural customer language. Preserve original Figma designer's valuable map, SOS visual ideas, images and safe profile ideas with credit; don't overwrite her original Figma file.
3. **Passenger account:** verification status, search/results, reserve one seat, **server-owned 600-second hold**, cancel/expire, FIFO waitlist with 120-second offer, private boarding code, trip milestones, review/private report.
4. **Driver account:** vehicle registration/review, departure creation, roster, one-time code check-in, transition boarding→en route→driver arrived. Driver and passenger arrival confirmation are separate.
5. **Staff and safety:** only staff can approve profiles, vehicles, route notices; incident reports remain private. Future SOS is a product direction; **do not pretend emergency dispatch exists**.
6. **Accessibility + polish:** 320–1440px responsive, zoom, usable touch controls, semantic forms/labels, accessible errors, reduced-motion, keyboard/screen reader, maps fallback, graceful empty/loading/error states and fast delivery on Nigerian mobile networks.

**Product stack stays fixed:** Django 5.2 LTS, Django templates + HTML/CSS/vanilla JS, PostgreSQL, Django Admin, pytest-django, GitHub Actions, Render web+PostgreSQL. Avoid adding React/Next.js or a new API/backend for this near-term deadline.

## 6. Verify functional pages, not just screenshots

Live site is a **real Django + Render PostgreSQL deployment** with fictional Friday sample users/bus departures. The app has integrated booking/driver service code, but don't assume every browser interaction is error-free merely because CI passed.

Inspect with safe sample accounts obtained through approved Render environment controls (never paste credentials into PR/screenshot):
- Public home → search **Jibowu → Mile 2** → bus results → bus detail.
- Approved passenger → reservation POST → held seat + private boarding code → My Trips. Use only sample data and keep code private.
- Driver → assigned vehicle/departure → assigned roster → code check-in.
- Waitlist and trip completion when available.
- Bad credentials/roles, unverified passenger, duplicate holds, expired offer, other driver's roster, CSRF, reports privacy, and moderated route notices.

**Never fabricate successful identity verification, live seat data, Google road coordinates or confirmed booking in UI.** Keep presentation copy polished and explain pilot/sample status unobtrusively but accurately.

## 7. Tools and validation commands

```bash
ruff check .
python manage.py check
pytest -q
# If working with Playwright in the Codex environment:
# browser screenshot for 1440/1024/768/390/320px; browser console/network checks
```
Tests need a local PostgreSQL test database. Don't run destructive tests on Render's live DB.

**Definition of done for each UI change:** visible in *actual browser* at desktop/tablet/mobile; screenshots and before→after notes; no JS console errors; no broken dynamic links; good fallbacks; keyboard/reduced-motion respected; CI green; reviewed PR to Render deployment branch. Nothing auto-merged to `main` without the team.

## 8. Exact Codex execution request

> Read `AGENTS.md` and `docs/CODEX_UI_HANDOFF.md`. You are working on SafeRide's Django website, on branch `codex/ui-visual-polish-handoff`. Use your browser tool or Playwright/Chromium to **open https://saferide-friday-web.onrender.com/** and capture screenshots of the actual homepage at 1440, 1024, 768, 390 and 320px widths. Explore Find a Ride, Sign In, My Trips and driver pages. Fix the visible desktop hero/map layout and refine the Jibowu→Mile 2 interactive road map with 3D-styled yellow danfo animation. Keep original backend services, server rules and secrets untouched. Work locally with a local/staging browser preview to inspect your edits. Verify map road geometry and Google/OSM fallback, reduced-motion, mobile UX, keyboard, and real page states. Run `ruff check .`, `python manage.py check` and `pytest -q` with a development PostgreSQL DB. Provide actual screenshots, a concise change summary and a PR targeting `deploy/render-demo-2026-10-16`. Never auto-deploy to the live presentation site or merge to `main` without review. If there is no browser access, tell me exactly what access is needed.

## 9. Additional facts and coordination

- GitHub issue board: https://github.com/orgs/saferide-l2e/projects/1/views/1
- Design source (teammate worked extensively on mobile and imagery): https://www.figma.com/design/hOvnMbooxS9EW7t2mjxYmU/SafeRide-L2E?node-id=0-1
- Branch `main` still does **not** contain all merged UI work. See full-stack integration PR #67 and Render setup PR #69.
- Render's free web service can sleep; a cold visit can take 50+ seconds. Do not confuse wake-up latency with a persistent build failure.
- Brand: **SafeRide — Every Journey Matters**. Colours already centre on rich dark green, mint and vibrant lime; raise design quality without changing identity or making everything neon.
- This document and `AGENTS.md` live on the Codex working branch so Codex can continue safely without modifying production unintentionally.

**Handover complete when:** Codex can open the live URL in a browser, compare responsive screenshots, make changes locally, demonstrate the modified UI in its own browser and submit a tested PR without leaking any keys or changing the production deployment unexpectedly.
