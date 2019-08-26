#!/bin/sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn task_manager_api.wsgi:application -p /code/gunicorn.pid --timeout 300
