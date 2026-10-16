# SafeRide — Learn2Earn MVP

## Current product workflows

[Complete page and workflow map](docs/WORKFLOWS.md) — current routes, passenger/driver/staff journeys, five-second approvals, state transitions and known gaps. Baseline: 16 October 2026. Older foundation/release notes below are historical.

## New to SafeRide? Start here! 👋

**[Group meeting script and screenshot checklist](docs/TEAM_MEETING_GUIDE.md)**

- **[EVERYONE: simple team guide](docs/TEAM_HUB.md)** — find your job and learn how to contribute.
- **[Frontend tasks](docs/TEAM_FRONTEND.md)** · **[Backend tasks](docs/TEAM_BACKEND.md)** · **[Database tasks](docs/TEAM_DATABASE.md)**
- **[Team lead: finish the progress board setup](docs/PROJECT_BOARD_GUIDE.md)** — the board and teams exist; check member access and assignment.
- **[2-minute meeting talk](docs/PRESENT_TO_TEAM.md)** — easy words for the whole group.
- **[All 45 GitHub Issues](https://github.com/saferide-l2e/saferide/issues)** — full instructions, checks and tests.

**Today:** Read your team's task, ask to be assigned one issue, work on a new branch, and request review. **Do not push directly to main.**

---

**Friday demo: 16 October 2026** · **Status: foundation only; features are NOT implemented.**

SafeRide is a privacy-conscious, bilateral-verification public bus discovery and seat reservation prototype. A verified passenger searches Jibowu → Mile 2, examines a participating driver/vehicle profile, holds one seat for **10 minutes**, boards with a single-use code, completes the trip and can leave a review or private safety report. Drivers and passengers both require **simulated admin-approved eligibility** for the demo; no real identity/background screening occurs.

## Stack
Single **Django 5.2 LTS** app, Django templates, HTML/CSS/JavaScript, PostgreSQL, Django Admin, pytest/pytest-django, GitHub Actions. No React/FastAPI or payment provider for Friday.

## Getting started (Ubuntu/Linux)
1. Install Python 3.11+ and PostgreSQL. Create a local database/user, or use a container.
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `cp .env.example .env` and change local credentials.
5. `python manage.py check` (initial skeleton works); models/migrations arrive through database issues.
6. After the database team merges its initial migrations: `python manage.py migrate`
7. `python manage.py runserver` then open http://127.0.0.1:8000/
8. `pytest` after installing dependencies and preparing PostgreSQL test database.

## Backend (apps/)
The backend implements the MVP scope in `docs/MVP_SCOPE.md` and the model contract in `docs/DATA_MODEL.md` across eight apps: `accounts`, `verification`, `vehicles`, `routes`, `departures`, `bookings`, `safety` and `audit`.

```bash
python manage.py migrate            # apply schema
python manage.py seed_demo         # fictional demo users, route, vehicle, departure
python manage.py reconcile_departures   # expire stale holds/offers (run on a schedule)
python manage.py runserver
```

Seeded demo accounts (password `saferide-demo-123`): `admin@example.test` (staff), `passenger@example.test`, `driver@example.test`.

Business rules live in service functions, not views:
- `apps/bookings/services.py` — `reserve`, `cancel`, `join_waitlist`, `accept_offer`, `check_in`, `confirm_arrival`, `reconcile`. Holds last exactly 600s; offers 120s; capacity is enforced under `select_for_update` on the departure row.
- `apps/departures/services.py` — publish and lifecycle transitions (a trip cannot start while valid holds exist).
- `apps/verification`, `apps/vehicles`, `apps/safety` — status transitions and moderation, all audited via `apps/audit/services.py`.

Every inventory change and its audit event commit together. Unverified/suspended users cannot book or publish, and cross-user access returns 403/404. Tests include PostgreSQL-only concurrency coverage (`tests/test_concurrency.py`); it is skipped on SQLite, which does not support row locks.

**Team interfaces:** see [`docs/BACKEND_INTERFACE.md`](docs/BACKEND_INTERFACE.md) for the URL → view → template contract the frontend team builds against, the JSON polling endpoints, and the models the services depend on. The backend renders template *names*; the frontend team owns the files in `templates/` and `static/`.

## Teams
- **Frontend**: `templates/`, `static/`, usability and accessibility.
- **Backend**: `apps/` business services/views, permissions and transactional logic.
- **Database**: `apps/*/models.py`, migrations, PostgreSQL constraints and seed fixtures. Coordinate model edits with backend.
- Integration/review/testing are **shared duties**.

**Start here:** [MVP scope](docs/MVP_SCOPE.md) · [architecture](docs/ARCHITECTURE.md) · [database contract](docs/DATA_MODEL.md) · [working together](CONTRIBUTING.md) · [Friday demo](docs/DEMO_SCRIPT.md).

**Safety boundary:** All accounts, registration numbers, KYC statuses, routes and reports used in the demo must be **synthetic**. Identity approval does not guarantee safety. Never upload real driver licences, ID photos, addresses or phone numbers to issues, fixtures or Git.
