#!/bin/bash
#python3 manage.py makemigrations
python3 manage.py migrate
if [[ "$SKIP_DB_UPDATE" != "True" ]]; then
    python3 manage.py curl_heroes
    python3 manage.py import_heroes
    python3 manage.py clear_cache
fi
python manage.py createcachetable
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --log-level $GUNICORN_LOG_LEVEL --workers $WORKERS --timeout $TIMEOUT
