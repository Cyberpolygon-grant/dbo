FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# При старте контейнера:
# 1) ждём, пока поднимется Postgres
# 2) применяем миграции
# 3) собираем статику
# 4) инициализируем демо-данные (в т.ч. новости для бегущей строки)
# 5) стартуем Gunicorn
CMD sh -c "\
  echo 'Waiting for PostgreSQL...' && \
  while ! nc -z db 5432; do sleep 1; done && \
  echo 'PostgreSQL is ready!' && \
  echo 'Creating migrations...' && \
  python manage.py makemigrations --noinput && \
  echo 'Running migrations...' && \
  python manage.py migrate --noinput 2>&1 | tee /tmp/migrate.log || { \
    if grep -q 'duplicate key\|pg_type_typname' /tmp/migrate.log; then \
      echo '⚠️  Duplicate PostgreSQL types detected (non-critical), verifying tables...'; \
      python -c \"from django.contrib.auth.models import User; User.objects.count(); print('✓ Tables exist, continuing...')\" || exit 1; \
    else \
      echo '❌ Migration failed!'; \
      cat /tmp/migrate.log; \
      exit 1; \
    fi \
  } && \
  echo 'Migrations completed!' && \
  echo 'Verifying migrations...' && \
  python manage.py shell -c \"from django.contrib.auth.models import User; User.objects.count(); print('✓ auth_user table exists')\" || (echo '⚠️  Warning: auth_user check failed, but continuing...' && sleep 2) && \
  echo 'Collecting static files...' && \
  python manage.py collectstatic --noinput && \
  echo 'Checking if demo data needs initialization...' && \
  python manage.py shell -c \"from dbo.models import Client; import sys; sys.exit(0 if Client.objects.exists() else 1)\" || (echo 'Initializing demo data (users, news, activities)...' && python init_data.py) && \
  mkdir -p /app/logs && \
  echo 'Starting Gunicorn...' && \
  gunicorn cyberpolygon.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 --access-logfile /app/logs/gunicorn-access.log --error-logfile /app/logs/gunicorn-error.log --log-level info"


