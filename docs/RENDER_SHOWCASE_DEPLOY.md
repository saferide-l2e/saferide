# Render pitch environment — 16 October 2026

Render Web Service (Python, **Free**) and Render PostgreSQL (**Free**, short-lived) in the same region, deployment source `deploy/render-demo-2026-10-16`. The 13 frontend PRs are not being force-merged into main.

Web build command: `bash scripts/render-build.sh`
Web start command: `bash scripts/render-start.sh`
Health path: `/health/` (check in apps/core/urls.py)
Environment variables:
- `DATABASE_URL`: Render **internal** PostgreSQL connection URL, secret.
- `DJANGO_SECRET_KEY`: unique random secret (never commit).
- `DEBUG=false`
- `ALLOWED_HOSTS=saferide-l2e-pitch.onrender.com` (adapt to assigned hostname)
- `CSRF_TRUSTED_ORIGINS=https://saferide-l2e-pitch.onrender.com` (adapt)
- `SAFERIDE_SEED_SAMPLE_DATA=true` (fictional temporary accounts/routes only, can turn off).
- `SAFERIDE_SAMPLE_DRIVER_EMAIL`, `SAFERIDE_SAMPLE_DRIVER_PASSWORD`; `SAFERIDE_SAMPLE_PASSENGER_EMAIL`, `SAFERIDE_SAMPLE_PASSENGER_PASSWORD`. **Unique 12+ char secrets; do not publish to public webpages or GitHub**.
- `PYTHON_VERSION=3.12.8` to pin a compatible runtime (if needed).

The seed command creates *synthetic preapproved* pilot user profiles and a current route for the walkthrough. It never approves arbitrary registered users and doesn't reset prior staff decisions. The real signup role/verification workflow remains staff-gated.

**Caution**: Render Free PostgreSQL is temporary (typically expires after 30 days). Transfer or export data before expiry. Free web services can sleep and have cold-start delays, so visit the site well before the presentation. Avoid live personal documents and real travel safety claims. Back up all important data off the Render free DB.

QA for pitch: Django health, landing assets, demo-user authentication, database-backed route search, reservation, booking history, driver roster/check-in, cross-user permission checks, expiry/reclaim, proper CSRF and staff review.
