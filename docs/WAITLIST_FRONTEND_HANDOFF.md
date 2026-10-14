# SafeRide FE-09 — FIFO waitlist and two-minute seat-offer UI

## Frontend implementation

- Mobile-first templates in templates/booking/waitlist.html and templates/booking/offer.html.
- Reusable queue display, server-provided position and number-ahead, copy explaining positions may change.
- Offer countdown uses exactly 120 seconds only as **display**; offer_expires_at and server_now come from the backend.
- Accept, decline, join and leave actions are POST forms with csrf_token. Multiple accidental browser submissions are guarded, but actual idempotency and capacity enforcement remain the backend's responsibility.
- Optional same-origin status polling every 15 seconds, session credentials and disabled browser cache.
- Pending/offered/expired/cancelled states, text-based guidance, network warnings, synthetic-data disclosure and no automatic offer acceptance.
- Template tests for server time display, valid actions, expired offers, CSRF, escaping and queue position.

## BE-07 and BE-14 handshake

The backend owns FIFO order by (joined_at, id), a unique active waitlist entry per passenger/departure, capacity allocation, 120-second offers and 600-second new holds. These templates must never derive a queue spot from browser data.

Waitlist template context:
- entry with status WAITING/OFFERED/ACCEPTED/EXPIRED/CANCELLED/INELIGIBLE, position (positive integer), people_ahead (nonnegative integer), route_label.
- can_join, join_action (trusted POST URL), leave_action (trusted POST URL), offer_url (trusted GET URL), queue_url, status_url (optional GET), search_url, route_label, action_message, info_message, error_message, verification_url.

Offer template context:
- offer with status, route_label, expires_at (UTC-aware datetime), server_now (UTC-aware datetime).
- accept_action and decline_action (server-generated POST URLs only while OFFERED), queue_url, error_message, status_url.

Optional same-origin polling endpoint returns JSON fields status, queue_position (positive integer for WAITING), server_now ISO-8601 UTC and offer_expires_at ISO-8601 UTC. Only its server results determine status. Never put personal identity data or private driver details in polling JSON.

## Still required before closure

BE-07 and BE-14 views/services are not merged. Real join, promotion, acceptance, timer reconciliation and inventory are not active here. Test with PostgreSQL simultaneous release/accept/decline, 120-second boundary, duplicate joins, expiry and user role checks after backend integration. Manual browser 360px, keyboard-only, 200% zoom, network interruption and team review are also outstanding.