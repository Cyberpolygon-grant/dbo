#!/bin/bash
#
# Скрипт для ПОЛНОГО перезапуска системы ДБО
#
# ЧТО ДЕЛАЕТ:
# 1. Останавливает контейнеры и удаляет volumes
# 2. ПОЛНОСТЬЮ УДАЛЯЕТ БД (DROP DATABASE)
# 3. Создаёт новую БД (CREATE DATABASE)
# 4. Применяет миграции
# 5. Сбрасывает sequences (ID начинаются с 1)
# 6. Создаёт тестовую заявку ПЕРВОЙ (ID=1)
# 7. Инициализирует демо-данные
#
# ГАРАНТИЯ: После выполнения тестовая заявка будет иметь ID=1
#

set -e

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose не найден"
    exit 1
fi

echo -n "[1/8] Остановка контейнеров... "
$COMPOSE_CMD down -v >/dev/null 2>&1
echo "✓"

echo -n "[2/8] Запуск контейнеров... "
$COMPOSE_CMD up -d --build >/dev/null 2>&1
sleep 5
echo "✓"

echo -n "[3/8] Удаление БД... "
$COMPOSE_CMD exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS dbo;" >/dev/null 2>&1 || true
echo "✓"

echo -n "[4/8] Создание БД... "
$COMPOSE_CMD exec -T db psql -U postgres -c "CREATE DATABASE dbo;" >/dev/null 2>&1 || true
sleep 2
echo "✓"

echo -n "[5/8] Миграции... "
$COMPOSE_CMD exec -T app python manage.py migrate --noinput >/dev/null 2>&1
echo "✓"

echo -n "[6/8] Сброс sequences... "
$COMPOSE_CMD exec -T db psql -U postgres -d dbo -c "DO \$\$ DECLARE r RECORD; BEGIN FOR r IN (SELECT schemaname, sequencename FROM pg_sequences WHERE schemaname = 'public') LOOP EXECUTE 'ALTER SEQUENCE ' || quote_ident(r.schemaname) || '.' || quote_ident(r.sequencename) || ' RESTART WITH 1'; END LOOP; END \$\$;" >/dev/null 2>&1 || true
echo "✓"

echo -n "[7/8] Инициализация данных... "
$COMPOSE_CMD exec -T -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD=admin -e DJANGO_SUPERUSER_EMAIL=admin@example.com app python manage.py createsuperuser --noinput >/dev/null 2>&1 || true
$COMPOSE_CMD exec -T app python manage.py collectstatic --noinput >/dev/null 2>&1
$COMPOSE_CMD exec -T app python create_test_request.py >/dev/null 2>&1
$COMPOSE_CMD exec -T app python init_data.py >/dev/null 2>&1
echo "✓"

echo -n "[8/8] Проверка заявок... "
$COMPOSE_CMD exec -T app python check_requests_order.py --fix >/dev/null 2>&1 || {
    $COMPOSE_CMD exec -T app python create_test_request.py >/dev/null 2>&1
    $COMPOSE_CMD exec -T app python check_requests_order.py >/dev/null 2>&1 || true
}
echo "✓"

echo "✅ Готово"

exit 0
