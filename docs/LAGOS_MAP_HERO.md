# SafeRide Lagos Route Hero

The new hero is a split grid on desktop (copy left; map right, from 980 CSS pixels). Tablets and phones stack the copy above a full-width map. Motion respects reduced-motion preferences and includes a Pause/Play control.

## Actual geography

Jibowu Bus Stop, Ikorodu Road, Lagos: approximately 6.52104, 3.36779 (public WorldPlaces location). Mile 2 Lagos interchange vicinity: approximately 6.45998, 3.31175 (Mapcarta/OpenStreetMap). These identify real geographic areas, not verified bus operator boarding bays.

## Available immediately

Without a Google key the homepage renders real OpenFreeMap vector street tiles with MapLibre GL JS (https://tiles.openfreemap.org/styles/liberty), and requests road geometry from the public OSRM sample routing server. This avoids direct use of OpenStreetMap Foundation's donation-funded raster tile servers, which returned 403 Access blocked in browser tests. OpenFreeMap explicitly permits keyless public/commercial use; attribution is shown automatically by MapLibre. The 3D yellow danfo illustration is generated for SafeRide and animates on the returned geometry. The path is never a made-up decorative curve. If routing is unavailable, the street map remains with real stop markers and a Google Maps directions link; animation stays disabled.

OpenFreeMap's public vector tile service and OSRM's public demo routing endpoint are both best-effort; OpenFreeMap does not offer an SLA. For sustained production traffic, arrange a reliable hosted map and routing service. Neither provider supplies real live danfo GPS.

## Enable interactive Google Maps

Google Maps JavaScript API now supports the Routes library and Route.computeRoutes with a path field. New Google Cloud projects may not be able to enable legacy Directions API.

1. In Google Cloud Console enable Maps JavaScript API and Routes API (check billing/pricing or eligible prototyping demo key).
2. Create an HTTP referrer-restricted browser key limited to the site's hostname https://saferide-friday-web.onrender.com/* and only the Maps APIs used. Set usage quota/budget alerts.
3. In Render Web Service, set GOOGLE_MAPS_BROWSER_KEY in Environment, then Save and deploy. Do not paste keys into ChatGPT or commit them.
4. Refresh homepage: the map will show the actual Google driving route and animate the same 3D bus marker on that polyline. If Google's key or route fails, the independent OpenFreeMap/OSRM fallback remains available. The street map can display even if the demo routing server is down; it will then show stop markers and a directions link, without invented road geometry.

Google routes and interactive maps can have usage costs. A public browser key is visible to browsers by design and must have HTTP referrer/API restrictions.

## Verification

Automated template checks live at tests/test_lagos_map_hero.py; CI runs Ruff, Django checks and PostgreSQL pytest. Manually verify Google when configured; fallback when absent; OSRM outage handling; 320, 390, 768, 1024 and 1440px widths; keyboard and reduced-motion settings. Animated yellow bus indicates visual trip illustration, not actual location tracking.

No changes to team's main branch, booking services or Render database.
