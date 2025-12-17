#!/bin/bash
#
# Скрипт для перезапуска системы ДБО
#

set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "============================================================"
echo -e "${BLUE}Скрипт перезапуска системы ДБО${NC}"
echo "============================================================"
echo ""

# Функция для отображения статуса
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "ok" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" = "info" ]; then
        echo -e "${BLUE}ℹ${NC} $message"
    elif [ "$status" = "warn" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
    fi
}

# Проверяем наличие docker-compose
if command -v docker-compose &> /dev/null; then
    print_status "info" "Используется docker-compose"
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    print_status "info" "Используется docker compose"
    COMPOSE_CMD="docker compose"
else
    print_status "error" "Docker Compose не найден"
    exit 1
fi

# Останавливаем контейнеры и удаляем все данные
echo ""
print_status "warn" "ВНИМАНИЕ: Все данные будут удалены!"
print_status "info" "Остановка контейнеров и удаление volumes..."
$COMPOSE_CMD down -v

# Пересобираем и запускаем контейнеры
echo ""
print_status "info" "Пересборка и запуск контейнеров..."
$COMPOSE_CMD up -d --build

# Ждём запуска
echo ""
print_status "info" "Ожидание запуска сервисов..."
sleep 5

# Проверяем статус
echo ""
print_status "info" "Проверка статуса контейнеров..."
$COMPOSE_CMD ps

# Применяем миграции
echo ""
print_status "info" "Применение миграций базы данных..."
$COMPOSE_CMD exec -T app python manage.py migrate --noinput

# Создаем суперпользователя
echo ""
print_status "info" "Создание суперпользователя admin..."
$COMPOSE_CMD exec -T -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD=admin -e DJANGO_SUPERUSER_EMAIL=admin@example.com app python manage.py createsuperuser --noinput || print_status "warn" "Суперпользователь уже существует"

# Собираем статические файлы
echo ""
print_status "info" "Сборка статических файлов..."
$COMPOSE_CMD exec -T app python manage.py collectstatic --noinput

# Инициализируем демо-данные
echo ""
print_status "info" "Инициализация демо-данных..."
$COMPOSE_CMD exec -T app python init_data.py

echo ""
echo "============================================================"
print_status "ok" "Система перезапущена успешно!"
echo "============================================================"
echo ""
print_status "info" "Учетные записи:"
echo "  - Суперпользователь: admin / admin"
echo "  - Оператор ДБО #1: operator1@financepro.ru / 1q2w#E\$R"
echo "  - Оператор ДБО #2: operator2@financepro.ru / 1q2w#E\$R%T"
echo "  - Клиенты: client1-5@financepro.ru / 1q2w#E\$R%T"
echo ""

exit 0
