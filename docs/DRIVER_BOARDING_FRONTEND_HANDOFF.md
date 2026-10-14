# SafeRide FE-10 — driver's private roster and boarding code check-in

## Built

- templates/driver/roster.html shows only booking short reference, public name/initials, limited verification status, HELD/BOARDED state and expiry time. No phone, email, KYC documents, raw boarding code or stored code digest.
- templates/driver/check_in.html has one six-digit code input, validation messages, POST with csrf_token and status feedback.
- Optional server-gated POST to close boarding; explicit privacy explanation.
- static/css/driver_boarding.css is responsive, keyboard reachable and uses no external fonts.
- static/js/roster.js optionally polls an authorised same-origin count endpoint every 15 seconds; the frontend never marks someone boarded itself.
- apps/core/test_driver_boarding_templates.py tests minimum safe context, no-access state, CSRF, escaping and permitted POST links.

## Backend handshake: BE-08, BE-09, FE-10

Back end must enforce current driver identity, vehicle ownership, departure assignment, boarding-open status, valid active held seat, and a never-used short boarding code via PostgreSQL row locks. Code digest and private passenger details must never be sent to roster template or logs.

Roster context:
- departure with route_label, scheduled_departure_at; roster is list of objects/dicts with short_reference, public_display_name, initials, status, verified, expires_at.
- boarded_count, held_count, capacity; all computed by server after reconciliation.
- can_check_in, checkin_url (GET), can_advance, advance_action (POST).
- status_url (optional, same-origin GET) returning only boarded_count and held_count integers. The backend must check driver permissions on every GET.
- error_message for rejected or forbidden views.

Check-in context:
- departure route_label and vehicle_plate;
- can_check_in boolean from authoritative server permission; checkin_action trusted local POST URL generated with Django reverse;
- error_message for used/invalid/expired/wrong-bus code and success_message after real database commit;
- roster_url (trusted GET) and action_message.

No permission is granted merely because HTML hides a form. The backend must reject unrelated driver roster access and code replay. Check-in POST must be idempotent/replay-protected and have CSRF enforcement.

## Unfinished

BE-08/09 remain unmerged. UI rendering is testable but live boarding won't work until those views are wired. Manual 360px, 200%-zoom, keyboard/screen-reader review and full role/expiry/replay tests against PostgreSQL remain mandatory before FE-10 can be closed.