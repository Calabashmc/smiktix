#!/bin/bash
set -e

echo "🕒 Waiting for Postgres to be ready..."
while ! nc -z postgres 5432; do
  sleep 0.5
done

echo "🔨 Creating tables and seeding database ..."
python init_db_and_seed_tables.py

echo "🚀 Starting Flask app..."
exec gunicorn -b 0.0.0.0:5000 "wsgi:app"
