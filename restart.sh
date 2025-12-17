#!/bin/bash
#
# Скрипт для создания пользователя в системе ДБО
# Подключается как Оператор ДБО 1 и создаёт нового пользователя
#

set -e

# Конфигурация
BASE_URL="http://10.18.2.7:8000"

# Данные оператора ДБО 1
OPERATOR_EMAIL="operator1@financepro.ru"
OPERATOR_PASSWORD="1q2w#E\$R"

# Данные нового пользователя
USER_LAST_NAME="Рутов"
USER_FIRST_NAME="Рут"
USER_MIDDLE_NAME="Рутович"
USER_EMAIL="hacker@hackermail.ru"
USER_PHONE="87777777777"
USER_PASSWORD="1q2w#E\$R%T"

# Временные файлы
COOKIES_FILE=$(mktemp)
RESPONSE_FILE=$(mktemp)
trap "rm -f $COOKIES_FILE $RESPONSE_FILE" EXIT

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Скрипт создания пользователя в системе ДБО"
echo "============================================================"

# Функция для получения CSRF токена
get_csrf_token() {
    local url=$1
    curl -s -c "$COOKIES_FILE" -b "$COOKIES_FILE" "$url" | \
        grep -oP 'csrfmiddlewaretoken.*?value="\K[^"]+' | head -1
}

# Функция для получения CSRF токена из cookies
get_csrf_from_cookie() {
    grep csrftoken "$COOKIES_FILE" | awk '{print $7}'
}

# Шаг 1: Вход как оператор
echo ""
echo -e "${YELLOW}[1/2] Вход в систему как Оператор ДБО 1...${NC}"

LOGIN_URL="${BASE_URL}/login/"
CSRF_TOKEN=$(get_csrf_token "$LOGIN_URL")

if [ -z "$CSRF_TOKEN" ]; then
    CSRF_TOKEN=$(get_csrf_from_cookie)
fi

if [ -z "$CSRF_TOKEN" ]; then
    echo -e "${RED}Ошибка: Не удалось получить CSRF токен${NC}" >&2
    exit 1
fi

# Выполняем логин
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
    -c "$COOKIES_FILE" -b "$COOKIES_FILE" \
    -X POST "$LOGIN_URL" \
    -H "Referer: $LOGIN_URL" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    --data-urlencode "email=$OPERATOR_EMAIL" \
    --data-urlencode "password=$OPERATOR_PASSWORD" \
    --data-urlencode "csrfmiddlewaretoken=$CSRF_TOKEN" \
    -L)

if [ "$HTTP_CODE" -eq 200 ]; then
    # Проверяем, что мы не на странице логина
    if grep -q "/login" "$RESPONSE_FILE"; then
        echo -e "${RED}Ошибка: Неверные данные оператора${NC}" >&2
        exit 1
    fi
    echo -e "${GREEN}✓ Успешный вход как оператор: $OPERATOR_EMAIL${NC}"
else
    echo -e "${RED}Ошибка: HTTP $HTTP_CODE${NC}" >&2
    exit 1
fi

# Шаг 2: Создание пользователя
echo ""
echo -e "${YELLOW}[2/2] Создание нового пользователя...${NC}"

# Возможные URL для создания пользователя
POSSIBLE_URLS=(
    "${BASE_URL}/admin/users/create/"
    "${BASE_URL}/users/create/"
    "${BASE_URL}/admin/user/add/"
    "${BASE_URL}/create-user/"
    "${BASE_URL}/operator/create-user/"
    "${BASE_URL}/operator/users/create/"
    "${BASE_URL}/api/users/create/"
)

CREATE_URL=""
CREATE_CSRF=""

# Пробуем найти рабочий URL
for url in "${POSSIBLE_URLS[@]}"; do
    CREATE_CSRF=$(get_csrf_token "$url")
    if [ -n "$CREATE_CSRF" ]; then
        CREATE_URL="$url"
        echo -e "${GREEN}✓ Найдена страница создания пользователя: $url${NC}"
        break
    fi
done

if [ -z "$CREATE_URL" ]; then
    # Пробуем получить CSRF из cookies
    CREATE_CSRF=$(get_csrf_from_cookie)
    if [ -n "$CREATE_CSRF" ]; then
        # Используем первый URL как дефолтный
        CREATE_URL="${POSSIBLE_URLS[0]}"
        echo -e "${YELLOW}⚠ Используется URL по умолчанию: $CREATE_URL${NC}"
    else
        echo -e "${RED}Ошибка: Не удалось найти страницу создания пользователя${NC}" >&2
        echo -e "${RED}Попробуйте указать корректный URL в скрипте${NC}" >&2
        exit 1
    fi
fi

# Отправляем запрос на создание пользователя
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
    -c "$COOKIES_FILE" -b "$COOKIES_FILE" \
    -X POST "$CREATE_URL" \
    -H "Referer: $CREATE_URL" \
    -H "X-CSRFToken: $CREATE_CSRF" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    --data-urlencode "last_name=$USER_LAST_NAME" \
    --data-urlencode "first_name=$USER_FIRST_NAME" \
    --data-urlencode "middle_name=$USER_MIDDLE_NAME" \
    --data-urlencode "email=$USER_EMAIL" \
    --data-urlencode "phone=$USER_PHONE" \
    --data-urlencode "password=$USER_PASSWORD" \
    --data-urlencode "password_confirm=$USER_PASSWORD" \
    --data-urlencode "csrfmiddlewaretoken=$CREATE_CSRF" \
    -L)

# Проверяем результат
if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
    # Проверяем наличие ошибок в ответе
    if grep -qi "error\|invalid\|required" "$RESPONSE_FILE"; then
        echo -e "${RED}Ошибка при создании пользователя${NC}" >&2
        grep -oP '(?<=error|alert)[^<]+' "$RESPONSE_FILE" | head -5
        exit 1
    fi
    
    echo -e "${GREEN}✓ Пользователь успешно создан!${NC}"
    echo "  ФИО: $USER_LAST_NAME $USER_FIRST_NAME $USER_MIDDLE_NAME"
    echo "  Email: $USER_EMAIL"
    echo "  Телефон: $USER_PHONE"
    echo "  Пароль: $USER_PASSWORD"
else
    echo -e "${RED}Ошибка: HTTP $HTTP_CODE${NC}" >&2
    cat "$RESPONSE_FILE"
    exit 1
fi

echo ""
echo "============================================================"
echo -e "${GREEN}✓ Операция завершена успешно!${NC}"
echo "============================================================"

exit 0
