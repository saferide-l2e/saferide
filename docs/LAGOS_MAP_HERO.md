# Lagos route map and danfo motion

The homepage uses real driving geometry between curated Lagos public-stop areas.
These are approximate public locations, not confirmed operator boarding bays. The
bus is an illustration of the selected journey, not a live vehicle feed.

## Marker and motion

`static/img/danfo-top.svg` is an original overhead yellow danfo with its front
pointing right (+screen X). The former 72×52 perspective WebP remains unchanged,
but is no longer the map marker: it cannot convincingly represent every heading.

`static/js/danfo_motion.js` handles cumulative road distance, interpolation,
projected tangents, shortest-angle smoothing and animation state. It advances by
time, at approximately 30 CSS pixels per second using the local projection scale.
A small projected road neighbourhood smooths the heading around bends. Position
always remains on the returned polyline; no artificial curves or direct lines are
substituted. At arrival it stops; Replay explicitly starts another journey.

The library owns the outer marker's positioning transform. A separate inner image
owns visual rotation, centred on the road. Width is 40px on phones, 44px on tablets
and 48px on desktop; the SVG's aspect ratio is preserved.

`static/js/hero_route.js` provides two adapters:

- Google: a supported `OverlayView` DOM marker, without a required map ID. Screen
  direction uses `MapCanvasProjection.fromLatLngToDivPixel`. Wait for the async
  SDK callback and the overlay's first usable draw, not merely script load or map
  idle, before requesting libraries or starting the animation.
- MapLibre: a custom HTML marker with viewport pitch/rotation alignment. Direction
  uses `map.project`, which includes camera bearing and pitch.

Pause retains distance. Resume does not jump. Hidden-tab time is discarded.
Reduced motion prevents autoplay and pauses an active animation when enabled.
A ResizeObserver refits the route when the map card changes size, with room for
stops and required attribution. Camera changes refresh marker orientation.

Each selection owns an AbortController, map, markers and cleanup. Stale Google
responses are ignored; old OSRM requests and animation frames are cancelled.
Destroyed animations cannot refresh detached markers. Route failures clear the
old journey and leave an external directions link, without an invented distance.

## Product interface and attribution

The header is **YOUR LAGOS ROUTE**. SafeRide's additional provider badge and
provider-specific descriptions have been removed. **View directions** opens the
selected route externally. Native Google logos/Terms/copyright and MapLibre's
OpenFreeMap/OpenMapTiles/OpenStreetMap attribution remain intact and visible.

Google uses `GOOGLE_MAPS_BROWSER_KEY` from secure runtime configuration, Maps
JavaScript API and Routes API. Never commit keys or place them in screenshots.
Restrict browser keys to approved referrers and APIs. Keyless fallback uses
OpenFreeMap tiles and public OSRM routing; production traffic needs appropriately
provisioned services rather than an assumption of unlimited public capacity.

Network dependencies: maps.googleapis.com, maps.gstatic.com,
routes.googleapis.com, fonts.googleapis.com, fonts.gstatic.com, unpkg.com,
tiles.openfreemap.org and router.project-osrm.org.

## Validation

Run the isolated PostgreSQL checks in the repository, plus:

```sh
node --test tests/js/*.test.cjs
node scripts/browser_map_check.cjs
node scripts/browser_map_check.cjs --keyless
```

The Chromium check records five viewport sizes, required attribution, actual
marker frames and heading error, drift from the projected road, pause/resume,
five additional stop pairs, rapid selection, reduced motion, dark mode and
explicit routing-failure handling. It encodes successive Chromium captures as
`danfo-motion.mp4` with their measured timing using system FFmpeg. Set
`SAFERIDE_MAP_ARTIFACTS` to select the output directory.

`--fixture-basemap` is a separate, local-only offline-canvas test of the real
MapLibre engine and live OSRM geometry. Its evidence is explicitly labelled and
must never be described as successful street-map or live-site validation.

The read-only live check can use `SAFERIDE_MAP_BASE=https://saferide-friday-web.onrender.com`.
Use `scripts/browser_release_check.py` only with an isolated local database for
account, driver and booking regressions. Reservation screenshots mask the private
boarding code. Render builds expose only the Git SHA at `/static/release.json`,
so the deployed build can be compared with the tested release.
