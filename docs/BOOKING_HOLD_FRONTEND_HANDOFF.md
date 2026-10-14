# SafeRide FE-08 — booking hold countdown, cancel and expiry UI

## Frontend implementation

- Responsive hold screen, boarding-pass code and one-time cancel POST form in templates/booking/hold.html.
- Styled time display in static/css/booking.css.
- Browser countdown in static/js/hold.js based on two authoritative server timestamps.
- Clock display uses performance.now monotonic elapsed time relative to server_now. Local device clock edits and refreshing cannot extend the server's original expiry.
- An optional GET status_url is polled every 15 seconds with same-origin credentials and no cache; responses can refresh server_now, expires_at and status. No polling when no endpoint is supplied.
- Only the server confirms whether a booking is HELD, BOARDED, EXPIRED or CANCELLED. The UI shows a cautious refresh reminder when the display reaches zero; it does not invent a server-side expiration.
- Online/offline warning, text status messages, no colour-only dependence, code hidden on browser-visible expiry.
- A cancellation button prevents accidental duplicate submission while a real POST is loading. The server still enforces permissions, idempotency and inventory reconciliation.
- Template rendering tests under apps/core/test_hold_template.py.

## BE-05, BE-06 and BE-14 integration contract

Render booking/hold.html with:

- booking: server-owned public booking object or dictionary with reference, status, route_label, boarding_point, plate_display, expires_at UTC-aware datetime, and optionally an ephemeral boarding_code when freshly issued. Do not persist the raw one-time code or expose it in status polling responses.
- server_now: current UTC-aware server datetime as close to the response time as possible.
- cancel_action: trusted reverse-resolved URL to POST a cancellation, only when eligible. Must require CSRF and object-level passenger permission.
- status_url: optional same-origin GET endpoint returning JSON with status (string), server_now (ISO-8601 datetime) and expires_at (ISO-8601 datetime); never reveal private passenger details.
- search_url: trusted public route search URL; error_message may contain readable 403, 409, invalid or expired states.

Backend invariants: 600 seconds from successful reserve commit, not client local time; 120-second separate offer windows; only server under PostgreSQL row locks decides inventory. Synchronous expiry reconciliation must ensure no late boarding. Cancel must update capacity and waitlist atomically.

## Incomplete until backend integration

This PR does not implement allocation, expiry reconciliation, status polling endpoint or cancellation service. Time displays are only visual guidance; pass a trusted status_url to enable real status checks. End-to-end testing against BE-05/06/14, 360px, keyboard navigation, fake/reversed device time, offline and cross-user security tests are still required before issue closure.
