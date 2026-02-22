#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Tesseract OCR (needed for attendance OCR feature)
apt-get update && apt-get install -y tesseract-ocr

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
