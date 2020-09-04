#!/bin/bash

if [ -v MIGRATE ]; then
  echo "Applying database migrations..."
  python3 manage.py migrate
fi

if [ -v COLLECT_STATIC ]; then
  echo "Collecting static files..."
  python3 manage.py collectstatic --noinput
fi

if [ -v POPULATE ]; then
  echo "Populating database with dummy data..."
  python3 manage.py populatedb --createsuperuser
fi

if [ -v STREAM_SETUP ]; then
  echo "Setting up stream data..."
  python3 manage.py streamsetup
fi

if [ -v CREATE_THUMBNAILS ]; then
  echo "Populating database with dummy data..."
  python3 manage.py create_thumbnails
fi

if [ -v PROD_MODE ]; then
  echo "Running saleor API in production mode..."
  uwsgi --ini /app/saleor/wsgi/uwsgi.ini
else
  echo "Running saleor API in development mode..."
  python manage.py runserver 0.0.0.0:8000
fi
