#!/bin/sh

echo "Waiting for postgres at $POSTGRES_HOST:$POSTGRES_PORT..."

while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

echo "Postgres is up"

python manage.py migrate
exec "$@"
python manage.py runserver 0.0.0.0:8000