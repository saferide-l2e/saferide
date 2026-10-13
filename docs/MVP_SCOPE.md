# SafeRide Friday MVP — locked scope
**Date:** Friday 16 October 2026. **Platform:** one Django + PostgreSQL mobile-responsive web app, no React.

## Mandatory journey
1. Passenger/driver register, sign in/out, choose role; eligibility begins NOT_SUBMITTED.
2. Fictional passenger and driver demo verification: PENDING -> VERIFIED/REJECTED only by authorized staff. Vehicle also requires APPROVED state. Both sides see **limited** verified status, not documents.
3. Approved driver registers bus (plate display, type, positive seat capacity), picks a saved route, publishes a scheduled departure with boarding point and sufficient time for a 10-minute hold.
4. Verified passenger searches origin+destination (Jibowu -> Mile 2), sees only eligible open departures, seat counts and limited driver/vehicle details.
5. One verified passenger reserves one seat for exactly **600 seconds**; expiry computed on server UTC. Driver sees only minimal passenger booking roster. Passenger can cancel.
6. Capacity is transactional: `HELD not expired + BOARDED + outstanding OFFERED waitlist seats + walk_ins <= snapshot capacity`; no double-booking.
7. Sold-out verified passenger can join FIFO waitlist. Released seats offered to next eligible person for **120 seconds**; accepted offer turns into fresh 600-second hold; offer expiry advances queue.
8. Assigned driver validates short single-use boarding code before hold expires; booking becomes BOARDED. Driver cannot board someone else's reservation.
9. Driver advances departure BOARDING_OPEN -> BOARDING_CLOSED -> EN_ROUTE -> ARRIVED; passenger independently confirms arrival, and history shows both assertions.
10. Eligible completed passenger can review (one 1–5 star review per booking); involved passenger/driver can privately report misconduct with status pending admin review; never publish allegations automatically.
11. Verified users can submit route/traffic information as a PENDING report; admin approves/rejects; UI displays approved reports only, with timestamps and a demo-data badge.
12. Django Admin staff can review demo verification, approve vehicles, moderate safety/traffic reports, suspend accounts; audit changes.
13. All forms have clear errors; layouts work at ~360px width and keyboard-only; timers do not rely on color; empty states and low-bandwidth behaviour.
14. PostgreSQL transactions/constraints, role/object permissions, CSRF, password hashing, simulated data policy, seeded scenario, tests, CI and demo deployment.

## Out of scope
Real KYC/background registry integration, ID/document uploads, biometric verification, live GPS, automated emergency dispatch, payments, AI TrustScore, public accusations/blacklists, SMS, live traffic partners, mobile native apps.

## Invariants and error rules
- Reservation duration exactly 600 seconds from successful database commit server timestamp. Reject if departure sooner than 600 sec or not BOARDING_OPEN.
- No active duplicate booking for passenger/departure and no overlapping active bookings across departures for MVP.
- At expiry instant (`now >= expires_at`), hold is invalid even if cron has not run. Reconcile synchronously **under row lock** for any inventory operation.
- Simultaneous last-seat requests: exactly one succeeds; loser receives a clear full-bus response.
- Boarding after expiration fails; no silent revival. A cancelled/expired hold remains immutable.
- Outstanding offer consumes one slot. Offer acceptance transfers slot rather than double-counting.
- Driver cannot depart early while valid outstanding holds exist; no seats promised inside the 600-second departure window.
- Unverified/suspended users cannot book, publish or access rosters. Cross-user and cross-driver accesses return 403/404.
- Never include secrets/KYC documents/phone numbers in logs, URLs, serializers, reviews, or public profiles.
- Driver arrival ≠ passenger confirmation; preserve independent timestamps and complaints.
