#!/bin/bash

# Azure App Service Startup Script for Django
# This script runs on each container startup

echo "🚀 Starting MatchFlix..."

# Navigate to app directory
cd /home/site/wwwroot

# Activate virtual environment if exists
if [ -d "antenv" ]; then
    source antenv/bin/activate
fi

# Run migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# Download ML models from Azure Blob (if configured)
echo "🤖 Checking ML models..."
python download_models.py

# Start Gunicorn
echo "✅ Starting Gunicorn server..."
gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --threads=4 \
         --timeout=120 \
         --access-logfile='-' \
         --error-logfile='-' \
         --capture-output \
         config.wsgi:application
