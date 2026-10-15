#!/usr/bin/env bash
set -euo pipefail
python manage.py migrate --noinput
if [ "${SAFERIDE_SEED_SAMPLE_DATA:-false}" = "true" ]; then
  python manage.py seed_showcase
fi
# Keep the database-backed timer alive even when nobody has the page open.
# If either child exits, terminate its sibling so Render restarts the service.
python manage.py process_reviews --watch &
review_pid=$!
gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --timeout 120 --access-logfile - &
web_pid=$!
cleanup() {
  trap - EXIT TERM INT
  kill "$web_pid" "$review_pid" 2>/dev/null || true
  wait "$web_pid" "$review_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 0' TERM INT
wait -n "$web_pid" "$review_pid"
exit 1
