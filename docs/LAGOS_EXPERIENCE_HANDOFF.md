# Lagos Experience — engineering handoff

## Design scope

- New homepage retains the Django template stack. Responsive editorial hero with an original source-controlled SVG illustration (`static/img/lagos-park.svg`), a single high-priority route search, an interactive real-road map and three journey steps.
- The map offers curated Lagos public-stop coordinates, selectable pickup/drop-off, interactive updated route line, a responsive 40–48px overhead yellow danfo aligned to the projected road tangent. The actual route geometry comes from OSRM/Google when reachable, not invented. The reduced-motion preference prevents automatic animation.
- OpenFreeMap vector tiles are the keyless fallback; Google Maps Routes API is used only when a secured browser-restricted key is configured. Neither backend represents actual bus telemetry.
- Global light/dark switch stores only the preference locally in the browser. It does not affect Django sessions.
- `/departures/search/` normally shows only actual Django-published departures; deterministic illustrative options require DEBUG=true and an explicit preview=1 query; `/departures/sample-ride/` shows an optional full-screen fictional ride preview with indicative fares, travel time, safety link and directions, without database writes or fake checkout.
- Profile form stores the minimum user-provided display name, Lagos commuting area and preferred boarding stop; **do not accept real identity documents, ID numbers, driver's licences, date of birth or home addresses through this workflow**. Pending users can edit it, while eligibility remains staff-approved.
- The dashboard calculates 10 informational milestone points per COMPLETED booking; points have no monetary value or redemption functionality. The existing actual booking history remains the source of truth.

## Production constraints

**Do not claim that merchant payments, official identity screening, actual bus availability, insurance, real GPS tracking, dynamic fare quoting or live seat data for fictional suggestions are integrated.**

Secure payments require a verified merchant provider, provider webhooks with signature verification, transaction reconciliation and a reviewed data-retention policy. Until then, no credit card fields or direct payment links are enabled. 'Ride protection' currently links to the existing safety-report and route-update system, not an insurance product.

The existing Django/PostgreSQL app and permission boundaries remain authoritative. Passenger reservation/boarding must never refer to a synthetic ride option.

## QA checklist

1. CI Django/Postgres tests, lints and migration checks.
2. Chromium screenshots at 320, 390, 768, 1024 and 1440.
3. From the homepage change pickup/destination and verify matching stop label/search text/directions URL and the mapped route, or a friendly provider fallback.
4. Toggle dark/light mode and refresh; keyboard through form fields and mobile navigation.
5. Browse Agege → Lekki Phase 1, open a sample card, see prices and no payment or reserve action.
6. Submit a fictional account profile, edit while PENDING, confirm no self-approval and staff-only VERIFIED transition.
7. Verify published booking, hold, driver check-in, cancellation, ride history and rewards.
8. Deploy Render only after successful checks and a browser review; database migrations are additive. Never test against live data.

## Future work

Real operator onboarding, configurable route and fare catalog, provider-verified online checkout, opt-in protection coverage from a regulated provider, redeemable loyalty rules, real route geocoding for arbitrary places and verified live vehicle feeds. These require external integration and explicit product decisions.
