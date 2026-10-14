# SafeRide FE-06 — passenger route search and bus listings

Design reference: https://www.figma.com/design/ztF1QqN7Npu55gnJwZVrG7

## Frontend delivered

- Responsive search page and results page in templates/passenger/.
- Shared GET origin/destination form in templates/includes/route_search_form.html.
- Illustrated route map with explicit notice that it is not live GPS.
- Cards for available and full buses, driver status and approval badge when provided by backend.
- Empty results, eligibility and error states, and unobtrusive synthetic-data disclosure.
- CSS in static/css/search.css and rendering/escaping smoke tests.

## Required BE-04 server context

BE-04 issue #16 specifies GET /buses/?origin=Jibowu&destination=Mile+2. The backend must normalise input and enforce eligibility and visibility. Suggested URL routing: a landing/search view can render passenger/search.html, while an authenticated results view renders passenger/results.html.

Both templates use the following context keys:

- origin and destination (request search field values).
- search_url, optional: browser GET action. Defaults to the current path.
- error_message, optional user-visible backend validation message.
- eligibility_message, optional server-provided user-state message.
- has_searched, boolean, distinguishes blank query from no matching buses.
- buses, iterable of **safe public dictionaries** in earliest-scheduled-first order.

Each bus dictionary should provide:

- route_label, scheduled_departure_at (timezone-aware Python datetime), boarding_point.
- vehicle_type_display, plate_display (appropriate public display), driver_name (public alias only).
- driver_approved boolean, is_full boolean, available_seats integer from server-side inventory.
- detail_url and waitlist_url, optional **trusted, reverse-resolved local URLs** from Django. Never take them directly from user query parameters.

Only list approved drivers/vehicles, BOARDING_OPEN future departures and non-suspended accounts. The server, NOT the frontend, computes capacity. The cards intentionally do not store expiry or allocate seats.

## Integration and QA

BE-04 is not merged yet. The templates are currently render-tested but are **not reachable as live /buses/ routes** until BE-04 provides the URL, query service and Django view.

Backend integration checks still required: origin/destination normalization, unapproved/past/cancelled departure exclusion, seat counts, sold-out waitlist, 403 for forbidden users and tests against PostgreSQL. Frontend manual checks required: 360px, 200% zoom, low-bandwidth, keyboard, loading and empty states.

Do not mark FE-06 complete until the actual backend view and integration tests work.