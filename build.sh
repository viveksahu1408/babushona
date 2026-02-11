#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Static files collect karo
python manage.py collectstatic --no-input

# 👇 YE NAYI LINE JOD DO (Magic Script) 👇
python db_setup.py