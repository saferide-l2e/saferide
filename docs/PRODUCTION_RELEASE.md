# SafeRide production release

SafeRide runs Django templates and the existing Django services against PostgreSQL.
The Vercel target is `saferide.vercel.app`; the Render service is
`saferide-friday-web.onrender.com` (`srv-db8b7mhsrm7s73e216bg`).

## Configuration

Deploy the consolidated `main` branch. Keep `SAFERIDE_VISUAL_PREVIEW` unset:
the historical gallery is an opt-in local development tool, not the application.

Configure each host through its secure environment settings:

- `DJANGO_SECRET_KEY`: a strong, stable secret. Use the same value on instances
  serving the same application and sessions; never commit it.
- `DATABASE_URL`: the existing PostgreSQL database. Render can use its internal
  URL; Vercel needs the externally reachable TLS connection URL, with
  `sslmode=require`. Never use the live database for tests.
- `DEBUG=false`.
- `ALLOWED_HOSTS`: the exact hostnames serving the app.
- `CSRF_TRUSTED_ORIGINS`: the exact HTTPS origins serving forms.
- `GOOGLE_MAPS_BROWSER_KEY`: the supplied browser key, entered in host settings,
  never in Git. Google must allow the site referrer and enable Maps JavaScript
  API and Routes API with billing where required. Check both deployed hostnames.
- Keep sample seeding disabled by default. `seed_demo --reset-safe-demo` is a
  local development command; it does not implement real identity verification.

Render build: `bash scripts/render-build.sh`.
Render start: `bash scripts/render-start.sh`.
Health check: `/health/`.

For Vercel, select the Django framework and repository root, using
`config.wsgi:application`. Both `pyproject.toml` and `requirements.txt` include
the runtime dependencies, including WhiteNoise. Collect static files during the
build with `python manage.py collectstatic --noinput`. Do not replace Django
with a static export or enable the historical visual-preview environment.
Apply migrations once through the controlled Render release before directing
Vercel traffic to the same schema; do not run migrations inside requests.

## Release checks

1. Run `ruff check .`, `python manage.py check`,
   `python manage.py makemigrations --check --dry-run`, and `pytest -q`
   against isolated local PostgreSQL.
2. Inspect the real pages in Chromium at 320, 390, 768, 1024 and 1440 pixels.
   Check the mobile menu, keyboard navigation, registration and verification.
3. Verify production-mode static serving and `/health/` locally.
4. After deployment, check both public hosts, static assets, CSRF-protected
   sign-in, fictional verification submission, staff review, and booking flows.
   A green build or health endpoint alone does not establish these work.
5. Check Google Maps in the actual browser and its console. Confirm a real
   Jibowu–Mile 2 driving route; the animated danfo is an illustration, not GPS.

Deployment API access requires `RENDER_API_KEY` for `api.render.com` and
`VERCEL_TOKEN` for `api.vercel.com`, with permission for the existing projects.
Enter credentials in secure environment settings, not chat or repository files.
Network policy must also allow the two deployed hosts and the relevant APIs.
