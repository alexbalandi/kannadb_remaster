FROM ubuntu:22.04

# Set up non-interactive apt installation
ENV DEBIAN_FRONTEND=noninteractive

# Update and install software-properties-common, deadsnakes/ppa, and python3.10
RUN apt-get update -y && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get update -y && \
    apt-get install -y python3.10

# Install dependencies
RUN python -m venv --copies /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install -r requirements.txt

RUN python manage.py migrate && \
    python manage.py curl_heroes && \
    python manage.py import_heroes && \
    python manage.py clear_cache

ENTRYPOINT [ "gunicorn config.wsgi:application" ]
