FROM ubuntu:22.04

# Set up non-interactive apt installation
ENV DEBIAN_FRONTEND=noninteractive

# Update and install required build tools and libraries for Python
RUN apt-get update -y && \
    apt-get install -y wget build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git

# Download, compile, and install Python 3.10
RUN cd /tmp && \
    wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz && \
    tar -xvf Python-3.10.0.tgz && \
    cd Python-3.10.0 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall

# Install dependencies
RUN which python3
RUN python3 -m venv --copies /opt/venv && \
    . /opt/venv/bin/activate && \
    pip3 install -r requirements.txt

RUN python3 manage.py migrate && \
    python3 manage.py curl_heroes && \
    python3 manage.py import_heroes && \
    python3 manage.py clear_cache

ENTRYPOINT [ "gunicorn config.wsgi:application" ]
