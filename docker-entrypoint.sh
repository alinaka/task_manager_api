#!/bin/sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py launchbot &
gunicorn --workers=1 --threads=2 --bind 0.0.0.0:8000 task_manager_api.wsgi:application -p /code/gunicorn.pid --log-level=info --access-logfile=/var/log/task_manager_api/access.log --error-logfile=/var/log/task_manager_api/error.log --timeout 300 --capture-output
