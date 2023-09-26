FROM python:3.10

# Set working directory
WORKDIR /app

# Copy project files into the Docker image
COPY . /app

# Install dependencies
RUN pip3 install --upgrade pip && apt update && install libmemcached-dev
RUN python3 -m venv --copies /opt/venv && \
    . /opt/venv/bin/activate && \
    pip3 install -r requirements.txt

RUN python3 manage.py migrate && \
    python3 manage.py curl_heroes && \
    python3 manage.py import_heroes && \
    python3 manage.py clear_cache

ENTRYPOINT [ "gunicorn config.wsgi:application" ]
