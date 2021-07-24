release: python manage.py migrate && python manage.py curl_heroes && python manage.py import_heroes && python manage.py clear_cache
web: gunicorn config.wsgi:application

