FROM python:3.10

# Set up non-interactive apt installation

# Install dependencies
RUN which python
RUN python -m venv --copies /opt/venv && \
    . /opt/venv/bin/activate && \
    pip3 install -r requirements.txt

RUN python manage.py migrate && \
    python manage.py curl_heroes && \
    python manage.py import_heroes && \
    python manage.py clear_cache

ENTRYPOINT [ "gunicorn config.wsgi:application" ]
