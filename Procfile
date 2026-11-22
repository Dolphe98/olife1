web: python manage.py migrate --noinput && python scripts/boot_extras.py && python manage.py collectstatic --noinput && gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000} --log-file -
