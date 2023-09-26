#!/bin/bash
python3 manage.py makemigrations
python3 manage.py migrate
if [[ "$SKIP_DB_UPDATE" != "True" ]]; then
    python3 manage.py curl_heroes
    python3 manage.py import_heroes
    python3 manage.py clear_cache
fi
python manage.py collectstatic
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --log-level debug
