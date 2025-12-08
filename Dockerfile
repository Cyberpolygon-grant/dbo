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
  echo 'Running migrations...' && \
  python manage.py migrate --noinput && \
  echo 'Collecting static files...' && \
  python manage.py collectstatic --noinput && \
  echo 'Checking if demo data needs initialization...' && \
  python -c \"from dbo.models import Client; import sys; sys.exit(0 if Client.objects.exists() else 1)\" || (echo 'Initializing demo data (users, news, activities)...' && python init_data.py) && \
  echo 'Starting Gunicorn...' && \
  gunicorn cyberpolygon.wsgi:application --bind 0.0.0.0:8000 --workers 4"


