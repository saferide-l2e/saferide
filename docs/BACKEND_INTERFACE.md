# Backend interface — how the frontend and database connect

This document is the backend team's contract with the other teams. The backend
owns `apps/*/views.py`, `forms.py`, `services.py`, `urls.py`, `admin.py` and
permissions. It does **not** own the frontend (templates/static) or the database
schema (models/migrations/fixtures) — but it depends on both through the
interfaces described here.

## Backend → frontend

Every page view renders a template by name below. The frontend team provides the
files; the backend never hard-codes markup. Anonymous users are redirected to
`accounts:login` (302); a signed-in user without the required role/verification
gets **403**.

| URL | URL name | Method | Access | Template |
|---|---|---|---|---|
| `/` | `core:home` | GET | public | `home.html` |
| `/health/` | `core:health` | GET | public | — (JSON) |
| `/dashboard/` | `core:dashboard` | GET | signed in | `dashboard.html` |
| `/accounts/register/` | `accounts:register` | GET/POST | public | `accounts/register.html` |
| `/accounts/login/` | `accounts:login` | GET/POST | public | `accounts/login.html` |
| `/accounts/logout/` | `accounts:logout` | GET/POST | signed in | — (redirect) |
| `/accounts/profile/` | `accounts:profile` | GET | signed in | `accounts/profile.html` |
| `/verification/` | `verification:status` | GET | signed in | `accounts/verification.html` |
| `/verification/submit/` | `verification:submit` | POST | signed in | — (redirect) |
| `/driver/vehicles/` | `vehicles:list` | GET | driver | `driver/vehicles.html` |
| `/driver/vehicles/new/` | `vehicles:create` | GET/POST | driver | `driver/vehicle_form.html` |
| `/driver/vehicles/profile/` | `vehicles:profile` | GET/POST | driver | `driver/profile.html` |
| `/routes/` | `routes:list` | GET | public | `passenger/routes.html` |
| `/departures/search/` | `departures:search` | GET | passenger | `passenger/search.html` |
| `/departures/<uuid>/` | `departures:detail` | GET | passenger | `passenger/departure_detail.html` |
| `/departures/driver/` | `departures:dashboard` | GET | driver | `driver/dashboard.html` |
| `/departures/driver/new/` | `departures:create` | GET/POST | driver | `driver/departure_form.html` |
| `/departures/driver/<uuid>/manage/` | `departures:manage` | GET | driver (owner) | `driver/departure_manage.html` |
| `/departures/driver/<uuid>/transition/` | `departures:transition` | POST | driver (owner) | — (redirect) |
| `/departures/driver/<uuid>/check-in/` | `departures:check_in` | POST | driver (owner) | — (redirect) |
| `/bookings/` | `bookings:index` | GET | passenger | `booking/my_bookings.html` |
| `/bookings/<uuid>/` | `bookings:detail` | GET | passenger (owner) | `booking/detail.html` |
| `/bookings/departures/<uuid>/reserve/` | `bookings:reserve` | POST | passenger | — (redirect) |
| `/bookings/<uuid>/cancel/` | `bookings:cancel` | POST | passenger (owner) | — (redirect) |
| `/bookings/departures/<uuid>/waitlist/` | `bookings:join_waitlist` | POST | passenger | — (redirect) |
| `/bookings/waitlist/<uuid>/accept/` | `bookings:accept_offer` | POST | passenger (owner) | — (redirect) |
| `/bookings/<uuid>/confirm-arrival/` | `bookings:confirm_arrival` | POST | passenger (owner) | — (redirect) |
| `/safety/reviews/<booking_uuid>/` | `safety:review` | GET/POST | passenger (owner) | `safety/review_form.html` |
| `/safety/reports/` | `safety:report` | GET/POST | signed in | `safety/incident_form.html` |
| `/safety/reports/<booking_uuid>/` | `safety:report_booking` | GET/POST | participant | `safety/incident_form.html` |
| `/safety/route-updates/` | `safety:route_updates` | GET | public | `safety/route_updates.html` |
| `/safety/route-updates/new/` | `safety:route_update_new` | GET/POST | verified | `safety/route_update_form.html` |

Notes:
- All POST forms must include `{% csrf_token %}`.
- Messages from actions appear via Django's messages framework.
- Key context: `departure.available` (seats left) for search/detail/manage;
  `profile` for driver pages; `boarding_code` is stored in the session at
  reserve/accept time (the plaintext code is never stored in the database).

### JSON endpoints (poll these instead of trusting a browser timer)
| URL | URL name | Access | Shape |
|---|---|---|---|
| `/bookings/<uuid>/status/` | `bookings:status` | owner | `{status, status_display, expires_at, seconds_remaining, checked_in_at}` |
| `/departures/<uuid>/availability/` | `departures:availability` | passenger | `{status, status_display, available, capacity}` |

The 600-second hold and 120-second offer are computed from server UTC. The
client countdown is presentational only.

## Backend → database

Services depend on these models (owned by the database team). They must keep the
fields and constraints below, or the service contract breaks:

- `accounts.User` — UUID pk, unique email, `role`, `is_active`; custom `AUTH_USER_MODEL`.
- `verification.Verification` — one-to-one with user, `status`.
- `vehicles.DriverProfile` / `vehicles.Vehicle` — `Vehicle.capacity > 0`, unique `plate_normalized`, `approval_status`.
- `routes.Route` — origin/destination/boarding/destination points, `is_active`.
- `departures.Departure` — `route`, `driver`, `vehicle`, `scheduled_departure_at`, `snapshot_capacity`, `walk_in_count >= 0`, `status`.
- `bookings.Booking` / `WaitlistEntry` / `BoardingCredential` — partial unique indexes for active bookings and active waitlist entries; `BoardingCredential.booking` one-to-one with a salted `code_hash`.
- `safety.Review` (stars 1–5, one per booking), `IncidentReport`, `RouteUpdate`.
- `audit.AuditEvent` — append-only.

Capacity is an **aggregate invariant enforced in locked service code**, not by a
row CHECK. Callers must go through `apps/bookings/services.py`:

`reserve`, `cancel`, `join_waitlist`, `accept_offer`, `check_in`,
`confirm_arrival`, `reconcile`.

Departure lifecycle transitions live in `apps/departures/services.py`. Every
operation locks the departure row with `select_for_update`, reconciles first,
and commits its change together with its audit event.

Local development: `python manage.py migrate` then `python manage.py seed_demo`.
`python manage.py reconcile_departures` expires stale holds/offers.
