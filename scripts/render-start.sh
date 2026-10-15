#!/usr/bin/env bash
set -euo pipefail
python manage.py migrate --noinput
if [ "${SAFERIDE_SEED_SAMPLE_DATA:-false}" = "true" ]; then
  python manage.py seed_showcase
fi
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --timeout 120 --access-logfile -
