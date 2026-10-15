# Cinematic Lagos landing handoff

## Concept and delivery status

**Lagos moves. Move with it.** A warm lagoon-and-bridge composition introduces
SafeRide, followed immediately by working route search. Original yellow danfo
artwork, restrained motion, off-white editorial sections, emerald surfaces and
lime actions replace the former map-led opening. Mobile uses a separate portrait
crop above compact copy; the search follows without an oversized headline screen.

**Delivered: original static cinematic artwork and a video-ready implementation.**
No finished cinematic video was supplied or produced. The artwork is a generated,
fictional Lagos-inspired composite, not a photograph of an operating departure or
a claim that depicted people use SafeRide. Realistic boarding animation and a
seamless production loop remain outstanding. Do not describe the media test clip
as cinematic footage, moving danfos, or evidence of realistic passenger movement.

## Original asset inventory and provenance

- `static/media/saferide-lagos-poster.webp`: 1920×1080, 349,790 bytes.
- `static/media/saferide-lagos-mobile.webp`: 800×790, 111,302 bytes.
- `static/media/saferide-lagos-driver.webp`: 900×900, 134,018 bytes.
- Artwork generated for this task using OpenAI's image generation tool on
  15 October 2026. Prompt specified Lagos lagoon/bridge, authentic yellow
  minibuses, a boarding stop, Nigerian commuters, warm daylight and coherent
  perspective, with no logos, text or third-party reference footage. The three
  WebPs are optimized crops/encodes of that single original composition.
- `components/journey_art.html` and `journey_steps.html`: original inline SVGs
  authored in this change. No third-party artwork or stock footage incorporated.
- `tests/fixtures/cinematic-test-pattern.mp4` and `.webm`: original FFmpeg `testsrc2`,
  320×180, 24fps, 1.2 seconds, silent H.264/VP8. Test-only colour bars and shapes;
  never linked by production templates or copied into production static assets.
- Existing mapping libraries, data and mandatory attribution retain their own
  licences. No provider watermark, Terms link or required attribution was hidden.

## Components and behaviour

- `templates/components/cinematic_hero.html`: accessible HTML headline/actions,
  responsive picture, optional native video and an explicit playback control.
- `ride_search.html`: GET submission to the existing Django search endpoint with
  origin/destination parameters, datalist stop suggestions and popular journeys.
- `journey_steps.html`, `journey_art.html`: original lightweight SVG illustrations.
- `route_preview.html`: existing selectable real-road map, moved below the hero.
  Provider scripts/routing load near the viewport or after stop interaction.
  Keyless MapLibre CSS loads with its adapter instead of blocking the homepage.
- `cinematic_hero.js`: chooses mobile/desktop encodes on first playback, pauses
  offscreen/in hidden tabs, supports manual pause/resume, suppresses source
  requests for reduced motion/saveData/2G, and retains the poster on media errors
  or autoplay rejection. Preference changes remove sources to stop downloading.
- `theme_init.js`: applies persisted/system theme before CSS paint and establishes
  the JS navigation state before first paint. `lagos_experience.js` provides the
  accessible toggle, cross-tab/system updates and search-stop synchronization.
- `lagos_experience.css`: shared public layout and theme surfaces for public,
  account, passenger and driver pages. Fixed brand panels remain dark green;
  text and surface tokens change independently in dark mode.
- `cinematic_hero.css`: stable responsive media frame and restrained entrance.
- New connected Django pages: `/how-it-works/`, `/for-drivers/`,
  `/safety-support/`. All use real registration, profile, search, trips, dashboard
  and reporting URLs. No new authentication or booking rules.

The homepage shows **journey suggestions**, not fictional operational buses.
They navigate to real published-departure search. There are no invented seats,
fares, ratings, driver identities, telemetry or assurances of official screening.

## Final footage specification / rendering storyboard

Supply all four reviewed assets in `static/media/`:

| File | Encode / target |
| --- | --- |
| `saferide-lagos-desktop.webm` | VP9, 1920×1080, 24/30fps, no audio, ≤5 MB |
| `saferide-lagos-desktop.mp4` | H.264, yuv420p, same dimensions/timing, faststart, ≤6 MB |
| `saferide-lagos-mobile.webm` | VP9, 720×900, 24/30fps, no audio, ≤2 MB |
| `saferide-lagos-mobile.mp4` | H.264, yuv420p, same framing/timing, faststart, ≤3 MB |

Use a 10–12-second loop with a locked or gently moving camera. Frames 0–4s:
bridge traffic, grounded wheel contact and perspective-correct speed. Frames
4–8s: focus on a parked danfo, conductor and one or two people boarding through
the open door; natural steps and unobstructed anatomy. Frames 8–12s: restore the
initial bridge/city composition with matching traffic positions, light and camera
for a seamless loop. Render both compositions deliberately, not by blindly
cropping away the boarding scene. Preserve left-side desktop copy space.

`core.views.home` enables video only when **all four source files exist**.
Django static URLs go through the established collectstatic/WhiteNoise pipeline.
No deployment secret or environment variable change is necessary. Review the
actual footage for human anatomy, road alignment and loop quality before adding
it. Re-run the media and visual tests with real footage; the current production
poster-mode test assertion must then be updated deliberately.

## Accessibility and performance

Real HTML text and buttons, keyboard-operable navigation with Escape/focus return,
a skip link, visible focus, native labelled search, meaningful poster alternative
text and native FAQ disclosures. Video is silent, decorative and never required
to search. Reduced motion suppresses entrance/hover transitions and video source
loading. No-JavaScript navigation, poster, search and public pages remain useful.

Desktop poster is ~342 KiB; mobile poster is ~109 KiB. Responsive preload avoids
requesting the desktop poster on phones. Driver imagery is lazy loaded. No hero
video request occurs until reviewed footage exists and playback policy permits.
No new external font or animation framework. Browser timings are local laboratory
observations, not a field Core Web Vitals or typical-Android performance claim.

## Validation and release

See the evidence inventory and final validation results added below. Browser media
lifecycle checks use only the explicitly labelled test pattern. They establish
play/pause/resume, visibility, preferences and failure handling, **not** cinematic
boarding quality or a seamless final scene. Production deployment and SHA must be
verified separately after PR review; passing local tests is not deployment.

### Verified results (15 October 2026)

- Ruff, Django system check, migrations dry-run: passed; no schema changes.
- Full isolated PostgreSQL suite: **195 passed, 82 subtests passed** (clean run,
  185.57 seconds). Follow-up map/landing integration: **13 passed**.
- Native JavaScript motion regression suite: **5 passed**.
- Chromium landing checks: eight widths (320/360/390/430/768/1024/1440/1920),
  no overflow or broken images; ten homepage internal CTA destinations resolve;
  GET search preserves selected stops; six rapid map selection pairs synchronize
  labels, search fields and external directions. No uncaught page exceptions.
- **28 axe-core WCAG A/AA audits** across seven public/account/search pages,
  phone/desktop and light/dark: zero reported violations. This supplements,
  rather than replaces, keyboard and visual inspection.
- Additional **22 authenticated passenger/driver page/theme audits**: zero
  reported violations, failed page responses or horizontal overflow. Includes
  dashboards, account/profile, trips, reports, route updates, vehicles and
  departure creation.
- Existing real Chromium regression: driver-role signup, registration → profile
  submission → pending review, approved passenger → published search → seat hold
  → private code, assigned driver → roster → check-in. All passed against local
  PostgreSQL only. Boarding-code screenshots remain masked.
- Native colour-bars clip: play/pause/resume, offscreen pause/resume, reduced
  motion, saveData, source failure and autoplay rejection passed. Reduced motion
  and saveData initiated **zero** media requests. No production footage tested.
- Measured local layout shift maximum **0.0021** across eight widths. Local first
  contentful paints ranged **196–1428 ms**, without network/device throttling;
  these are not field LCP or Android performance measurements.
- Header menu tested across tablet → desktop → phone; breakpoint reset and
  Escape/focus return work. No-JavaScript phone navigation and GET search pass.

### Evidence and changed files

Source-controlled evidence: [`docs/evidence/cinematic/`](evidence/cinematic/).
Includes five hero viewport captures, full desktop and dark-phone screenshots,
new public-page screenshots, landing JSON, authenticated theme JSON and masked
workflow results. Images were encoded as WebP from actual Chromium captures.

Source changes: `apps/core/views.py`, `apps/core/urls.py`, `templates/home.html`,
`templates/base.html`, `templates/components/`, `templates/public/`,
`static/media/`, `static/css/cinematic_hero.css`,
`static/css/lagos_experience.css`, `static/css/auth.css`, `static/js/cinematic_hero.js`,
`static/js/theme_init.js`, `static/js/lagos_experience.js`,
`static/js/navigation.js`, `static/js/hero_route.js`,
`scripts/browser_cinematic_check.py`, `scripts/browser_release_check.py`,
`.github/workflows/browser_release_audit.yml`, landing/map template tests and the
explicit test-pattern fixture. Authentication, inventory, booking services,
authorization and database migrations are unchanged.

Run locally with isolated PostgreSQL:

```sh
ruff check .
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q
node --test tests/js/*.test.cjs
SAFERIDE_CHROMIUM_PATH=/usr/bin/chromium python scripts/browser_release_check.py
SAFERIDE_CHROMIUM_PATH=/usr/bin/chromium python scripts/browser_cinematic_check.py
```

For axe audits, set `SAFERIDE_AXE_PATH` to an installed `axe.min.js`. The browser
release audit runs both Python checks and uploads their screenshots/results.
Use fresh eligible **local** fixtures for repeated booking runs; do not reset
production accounts or reservations to make a test pass.

### Deployment status / limitations

Work starts from latest fetched main **f15bab59a9a29d3fe8755e8f6538c669af0ba347**.
The live Render `/static/release.json` independently reported that same SHA during
this task. Changes are on `feat/cinematic-lagos-landing`. No new service/database,
production records or deployment secrets were changed.

PR review and checks are release gates. Do not describe this feature as deployed
until the existing Render deployment pipeline has served the reviewed commit and
its `/static/release.json` matches. No Render API credential was ready in the
managed environment at the start of this task. Live post-deployment playback and
performance are not established by local screenshots.

Outstanding: legitimate finished desktop/mobile cinematic footage; artistic
review of actual boarding movement and loop seam; production release and live
verification after review. Absolute absence of bugs cannot be guaranteed by
these tests.

### GitHub review and runs

- PR: https://github.com/saferide-l2e/saferide/pull/80
- Initial Django run: https://github.com/saferide-l2e/saferide/actions/runs/38796937041
- Initial Chromium run: https://github.com/saferide-l2e/saferide/actions/runs/38796936912

Run links are evidence locations, not a statement that a still-running check has
passed. The PR's checks show the latest commit and any follow-up runs.

### Additional road-preview validation

Read-only Chromium checked all six requested stop pairs with live OSRM road
geometry (171–515 vertices, not artificial straight lines), fitted MapLibre maps
and required attribution. Blocking both providers retained the external link and
did not invent a distance. The default configured adapter also used the working
MapLibre fallback during this check; this is **not** evidence of successful Google
Routes responses. See `route-results.json` and `route-keyless.webp` in evidence.

The first GitHub Django run passed. The first Chromium run failed; remote logs
were blocked by the environment's network policy. Two exact GitHub log/artifact
hosts were added to the saved environment configuration draft; applying that
draft requires publishing the environment settings. Failure annotations were
added to the browser script so subsequent CI failures can be diagnosed through
the already accessible GitHub API. See the PR for final check results.

### Production-settings smoke

A separate local Gunicorn process with DEBUG=false, isolated local PostgreSQL and
the normal trusted-proxy HTTPS header served the homepage, three public pages and
sign-in successfully. Collected WhiteNoise static assets and theme persistence
worked, with zero missing static responses or page exceptions. The existing
storage is CompressedStaticFilesStorage (unhashed names), not manifest storage;
that established deployment configuration is preserved. See production-smoke.json.

Follow-up runs for the route-fallback/diagnostics commit:
https://github.com/saferide-l2e/saferide/actions/runs/38797737103 (Django),
https://github.com/saferide-l2e/saferide/actions/runs/38797737062 (Chromium).

### Interface recording and scrolling

`docs/evidence/cinematic/interface-walkthrough.mp4` records actual Chromium UI
interaction, using the real keyless MapLibre/OSRM preview (92 captured frames,
about 7.1 seconds). The poster remains static. This demonstrates section
navigation, route selection and colour themes, not cinematic vehicle movement.

The Chromium CI annotation identified a timeout clicking Find buses while the
control was moving. Smooth scrolling is now scoped to explicit hero section links
instead of all browser/form scrolling. Those links retain URL history and move
keyboard focus to the section. Without JavaScript the expanded header scrolls
with the document rather than covering search. Native search clicks with and
without JavaScript, keyboard section focus, and the full local landing/media
suite passed again after this correction. See the PR's latest CI for confirmation.

### Native media test compatibility

The native media check renders the actual Django hero component with controlled
test sources, rather than duplicating its markup. Silent WebM/VP8 and MP4/H.264
fixtures match the production source order, supporting Chromium builds with
different codec availability. Mobile and desktop playback controls, actual loop
progress, pause/resume, offscreen pause and preference/failure paths are tested.
The desktop playback control is outside the background media stacking context so
headline layout cannot intercept it. No test pattern is enabled on the website.
