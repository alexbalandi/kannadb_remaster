FROM ubuntu:22.04
RUN apt-get -y update && apt-get install software-properties-common \
&& add-apt-repository ppa:deadsnakes/ppa && apt install python3.10
# Install dependencies
RUN python -m venv --copies /opt/venv && . /opt/venv/bin/activate && pip install -r requirements.txt
RUN python manage.py migrate && python manage.py curl_heroes && python manage.py import_heroes && python manage.py clear_cache
ENTRYPOINT [ "gunicorn config.wsgi:application" ]
