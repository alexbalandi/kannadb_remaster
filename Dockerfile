# Use the official Python 3.10 image as a parent image
FROM python:3.10

# Set environment variables for Poetry
ENV POETRY_VERSION=1.5.0 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

# Set working directory
WORKDIR /app

# Copy project files into the Docker image
COPY ./pyproject.toml /app/pyproject.toml

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends libmemcached-dev

# Install pip, Poetry, and project dependencies
RUN pip3 install --upgrade pip \
    && pip3 install "poetry==$POETRY_VERSION" \
    && poetry install --no-dev
    
COPY . /app
# Run migrations and other project setup commands
RUN python3 manage.py migrate && \
    python3 manage.py curl_heroes && \
    python3 manage.py import_heroes && \
    python3 manage.py clear_cache

# Command to run the application using Gunicorn
ENTRYPOINT [ "gunicorn", "config.wsgi:application" ]
