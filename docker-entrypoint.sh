#!/bin/sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py launchbot &
gunicorn --workers=1 --threads=2 --bind 0.0.0.0:8000 task_manager_api.wsgi:application -p /code/gunicorn.pid
