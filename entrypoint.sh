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

if [ -v DEV_USER ]; then
  echo "Setup DEV Account..."
  python3 manage.py createdevuser
fi

if [ -v STREAM_SETUP ]; then
  echo "Setting up stream data..."
  python3 manage.py streamsetup
fi

if [ -v INTEGRATION_SETUP ]; then
  echo "Setting up integration data..."
  python3 manage.py integrationsetup
fi

if [ -v CREATE_THUMBNAILS ]; then
  echo "Populating database with dummy data..."
  python3 manage.py create_thumbnails
fi

gunicorn --bind :8000 --workers "$UVICORN_WORKERS" --threads "$UVICORN_THREADS" --worker-class uvicorn.workers.UvicornWorker saleor.asgi:application
