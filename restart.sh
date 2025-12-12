#!/usr/bin/env bash
set -euo pipefail

echo "🛑 Остановка контейнеров..."
sudo docker compose down -v 2>/dev/null

echo "🔨 Сборка образов..."
sudo docker compose build --quiet

echo "🚀 Запуск контейнеров..."
sudo docker compose up -d

echo "⏳ Ожидание БД..."
timeout=60
counter=0
while ! sudo docker compose exec -T db pg_isready -U appuser -d appdb >/dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    [ $counter -ge $timeout ] && echo "❌ Таймаут БД" && exit 1
done

echo "🗑️ Очистка БД..."
sudo docker compose exec -T db psql -U appuser -d appdb <<EOF >/dev/null 2>&1 || true
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO appuser, public;
EOF

echo "⏳ Ожидание приложения..."
counter=0
while ! sudo docker compose exec -T app nc -z localhost 8000 >/dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    [ $counter -ge $timeout ] && break
done

echo "📦 Создание миграций..."
sudo docker compose exec -T app python manage.py makemigrations --noinput >/dev/null 2>&1 || true

echo "📦 Применение миграций..."
sudo docker compose exec -T app python manage.py migrate --noinput >/dev/null 2>&1

echo "💾 Создание демо-данных..."
sudo docker compose exec -T app python init_data.py >/dev/null 2>&1 || echo "⚠️ Ошибка init_data.py"

echo "✅ Готово! http://localhost:8000"
