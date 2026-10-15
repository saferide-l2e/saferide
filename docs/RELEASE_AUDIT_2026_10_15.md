# SafeRide release audit — 15 October 2026

## Current demo topology

- **Canonical application:** https://saferide-friday-web.onrender.com/
- **Vercel entry:** https://saferide-eight.vercel.app/
- **Temporary production Vercel behavior:** HTTP 307 GET redirect to the matching path on Render via the Django canonical-host middleware. Existing `vercel.json` is retained as best-effort config, but the public probe showed that its redirect was not applied on Vercel's Django framework runtime. This is a **single Django backend**, not two independently database-backed installations.
- **Why:** Vercel `DATABASE_URL` was not configured. Its registration page returned HTTP 500 while the static homepage rendered. Render PostgreSQL explicitly blocks external connections; do **not** open it to 0.0.0.0/0.
- **Authentication:** Sessions and CSRF remain same-origin on Render after the redirect. Do not mirror session secrets, transmit passwords in query strings, or use live production PostgreSQL in CI.
- **Longer term:** Provision Vercel-accessible, TLS-protected database access with narrowly scoped network rules, verify migrations and secrets, then remove the redirect and restore true independent Vercel Django runtime.

## Audit matrix and expected demo journeys

| Surface | Check | Safety rule |
| --- | --- | --- |
| Public | Landing page loads, functional CTA to sign up as driver, internal links reach 200/login redirect | No fictional GPS or official verification claims |
| Account | Register passenger and driver, validate input, login, POST-only logout | CSRF and isolated sessions |
| Verification | Fictional declaration visible for not-submitted/rejected; submit -> PENDING | Only staff can approve |
| Passenger | Search Jibowu–Mile 2; departure detail; 10-minute seat hold; private boarding code; cancellation; trip history | Never show another passenger's details |
| Driver | Vehicle request; approved vehicle; publish/manage departure; roster; boarding check-in; arrival | Only approved/eligible driver and vehicle |
| Safety | Private incident report; route updates stay moderated; review only completed trip | No public unreviewed allegations |
| Staff | Django Admin review verification/vehicles/reports | Actions audit-tracked; no self-approval |
| Map | OpenFreeMap fallback route with illustrated danfo; Google when securely configured | No real-time location representation |
| Accessibility | Keyboard, focus, viewport widths 320/390/768/1024/1440 and reduced motion | No hidden or unusable forms |

## Observed defects addressed by this branch

1. Vercel Django 500 on /accounts/register/ due to missing production database settings: temporary host-specific 307 redirect to Render is implemented in Django before auth/session/DB access. Stale POST submissions receive 303 and are NOT repeated across origins.
2. Verification panel lacked a visually prominent declaration in live screenshot: simplified template guard and added in-page action/link plus visible form styling.
3. Landing page repeats value strip, large benefits, safety, and final CTA: removed redundant strip and duplicate closing sections, reduced spacing.
4. Driver CTA incorrectly linked to its own current section: link to driver-prefilled account creation.
5. Logout view allowed GET with side effects: require POST with CSRF.
6. Added transaction-safe regression tests in `tests/test_release_smoke.py`, on isolated PostgreSQL in GitHub Actions.

## Not yet proven by this code change

- Real-browser UI screenshots, blocked third-party tile providers, full phone/tablet interactive checks, and production sign-up/booking after deploy.
- Vercel's final URL and 307 behavior (must observe actual response).
- Google Maps API key/billing and live route rendering.
- Payment, official ID screening, emergency dispatch, or live GPS (none exist).

## Release procedure

1. Review GitHub PR, ensure full Ruff/Django/Postgres test suite passes.
2. Merge to `main`, wait for Vercel production READY, check actual redirect and registration workflow.
3. Fast-forward the Render deployment branch, manually deploy if GitHub pushes do not auto-trigger. Watch build and migrations; preserve database.
4. Browser-test all required workflows with fictional test identities and report screenshots and exact HTTP outcomes. Never claim green CI alone proves production functionality.
