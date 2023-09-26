FROM python:3.10

# Set working directory
WORKDIR /app

# Copy project files into the Docker image
COPY . /app

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
