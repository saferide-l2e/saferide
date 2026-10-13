# Architecture & work boundaries
```text
Browser (Django templates + JavaScript)
  -> Django URL/view/form (session auth + CSRF + per-object permissions)
  -> Service functions (business rules + transaction.atomic/select_for_update)
  -> Django ORM and migrations (PostgreSQL)
  -> Django Admin moderation
```
PostgreSQL is the single source of truth. Countdown is visual only: client periodically polls server state (10–15s); only backend determines expiry. Management command reconciles expired holds/offers periodically; all reads that allocate inventory reconcile under lock.

## Module ownership (target; scaffold apps when tickets are taken)
`apps/accounts` registration/roles; `apps/verification` KYC-status transitions; `apps/vehicles` drivers/buses; `apps/routes` locations; `apps/departures` departure lifecycle; `apps/bookings` hold/waitlist/boarding; `apps/safety` reviews/reports/route updates; `apps/audit` events.
Database team owns model/migration contracts for those apps; backend team owns service/view logic; frontend team owns templates/static. Coordinate changes to `urls.py`, settings and cross-team model definitions.

## Booking service contract (required)
`reserve(passenger, departure, now_utc)`, `cancel(booking, actor, now_utc)`, `join_waitlist(passenger, departure)`, `accept_offer(entry, passenger, now_utc)`, `check_in(booking, driver, code, now_utc)`, `reconcile(departure, now_utc)`. Each operation must lock departure row, reconcile expiries/offers, enforce eligibility, unique active booking and capacity; updates + audit commit together. Never rely on browser timers or SQLite concurrency to guarantee correctness.
