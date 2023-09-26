#!/bin/bash
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py curl_heroes
python3 manage.py import_heroes
python3 manage.py clear_cache
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
