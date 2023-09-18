#!/bin/bash

if [ -v CLEAR_DB ]; then
  echo "Clearing database..."
  python3 manage.py cleardb --force
fi

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

if [ -v SYNC_SEQUENCES ]; then
  echo "Setting up integration data..."
  python3 manage.py sync_sequences
fi

if [ -v CREATE_THUMBNAILS ]; then
  echo "Populating database with dummy data..."
  python3 manage.py create_thumbnails
fi

gunicorn --bind :8000 --workers "$UVICORN_WORKERS" --threads "$UVICORN_THREADS" --worker-class saleor.asgi.gunicorn_worker.UvicornWorker saleor.asgi:application
