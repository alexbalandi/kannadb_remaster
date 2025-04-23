# Use the official Python 3.10 image as a parent image
FROM python:3.10

# Set environment variables for Python (optional but recommended)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends libmemcached-dev && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy only the dependency definition first to leverage Docker cache
COPY ./pyproject.toml /app/pyproject.toml

# Install production dependencies using uv
# The --system flag installs packages into the global site-packages directory
RUN uv pip install --system .

# Copy the rest of the application code
COPY . /app

RUN chmod +x /app/run.sh

# Gunicorn is specified as a dependency in pyproject.toml, so it will be available
# Command to run the application using the script which handles migrations etc.
ENTRYPOINT ["bash", "/app/run.sh"]
# Gunicorn command is now in run.sh
# ENTRYPOINT [ "gunicorn", "config.wsgi:application" ]
