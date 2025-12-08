#!/usr/bin/env bash
set -euo pipefail

# Полный перезапуск с очисткой volumes
echo "🛑 Остановка контейнеров и удаление volumes..."
sudo docker compose down -v

echo "🔨 Сборка образов..."
sudo docker compose build

echo "🚀 Запуск контейнеров..."
sudo docker compose up -d

echo "⏳ Ожидание готовности базы данных и приложения..."
# Ждем, пока база данных будет готова
echo "   - Ожидание PostgreSQL..."
timeout=60
counter=0
while ! sudo docker compose exec -T db pg_isready -U appuser -d appdb >/dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo "❌ Таймаут ожидания базы данных"
        exit 1
    fi
done
echo "   ✓ PostgreSQL готов"

# Ждем, пока контейнер app будет готов
echo "   - Ожидание готовности приложения..."
counter=0
while ! sudo docker compose exec -T app nc -z localhost 8000 >/dev/null 2>&1; do
    sleep 2
    counter=$((counter + 2))
    if [ $counter -ge $timeout ]; then
        echo "⚠️  Приложение еще не готово, но продолжаем..."
        break
    fi
done

# Явно пересоздаем транзакции для всех клиентов
echo ""
echo "💸 Пересоздание транзакций для всех клиентов..."
if sudo docker compose exec -T app python init_data.py; then
    echo "✅ Транзакции успешно пересозданы!"
else
    echo "⚠️  Предупреждение: не удалось пересоздать транзакции автоматически"
    echo "   Выполните вручную: sudo docker compose exec app python init_data.py"
fi

echo ""
echo "✅ Проект перезапущен с очисткой volumes!"
echo "📊 Просмотр логов: sudo docker compose logs -f app"
echo "🌐 Доступ: http://localhost:8000"
echo ""
echo "💡 Транзакции созданы для всех клиентов:"
echo "   - Петр Иванов (client1)"
echo "   - Мария Смирнова (client2)"
echo "   - Алексей Козлов (client3)"
echo "   - Елена Морозова (client4)"
echo "   - Дмитрий Волков (client5)"

