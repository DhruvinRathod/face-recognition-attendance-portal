#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate --noinput
python manage.py create_demo_data \
  --username "${DEMO_USERNAME:-teacher}" \
  --password "${DEMO_PASSWORD:-RecruiterDemo2026!}"

exec gunicorn attendance_portal.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120
