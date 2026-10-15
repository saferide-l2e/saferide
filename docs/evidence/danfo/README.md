# Chromium evidence — danfo motion and route card

All captures use the actual local Django app, real map tiles and returned road
geometry. They are not the offline fixture mode. Required map attribution remains
visible. No keys, boarding codes or production database records are included.

- [Desktop](google-1440.png), [1024px](google-1024.png), [tablet](google-768.png),
  [390px phone](google-390.png), [320px phone](google-320.png).
- [Keyless map on a phone](keyless-390.png); [dark mode](dark.png).
- [Chromium/CDP motion recording](danfo-motion.mp4): 56 native screencast frames
  over approximately 7.5 seconds, encoded with their captured timing.
- [Google results](google-qa.json) and [MapLibre results](maplibre-qa.json).

Both engines passed the six specified stop pairs, pause/resume, rapid changes,
reduced motion, error fallback, attribution and no-horizontal-overflow checks.
Actual rAF samples measured a mean heading difference of 2.64° (Google, 493
frames) and 3.16° (MapLibre, 574 frames); peak errors at short sharp bends are
reported in the JSON, not omitted. Maximum marker drift from the projected
polyline was 0.025px and 0.000084px respectively. Neither run had an uncaught
JavaScript exception. These measurements describe the captured runs, not all
possible cameras, routes or network conditions.

Local validation: 188 pytest tests and 82 subtests; five JavaScript tests; Ruff;
Django check; no pending model migrations. The isolated browser regression also
passed registration, pending verification, published-departure browsing,
reservation and driver boarding-code check-in. Normal searches no longer invent
fictional buses when a route has no published departures.

`node scripts/browser_map_check.cjs` reproduces the Google check when a browser
key is configured; `--keyless` exercises MapLibre/OSRM. `node
scripts/record_map_motion.cjs` makes a native Chromium recording. The optional
`--fixture-basemap` test is explicitly separate and not used for these captures.
