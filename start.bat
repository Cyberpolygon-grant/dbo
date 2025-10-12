@echo off
echo 🏦 Запуск системы ДБО - Киберполигон
echo ======================================

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.8+
    pause
    exit /b 1
)

REM Проверяем наличие Django
python -c "import django" >nul 2>&1
if errorlevel 1 (
    echo 📦 Установка Django...
    pip install django
)

echo 🔄 Выполнение миграций...
python manage.py makemigrations
python manage.py migrate

echo 📊 Создание демо-данных...
python manage.py init_demo_data

echo 🚀 Запуск сервера...
echo.
echo ✅ Система запущена!
echo 🌐 Откройте браузер и перейдите по адресу: http://127.0.0.1:8000
echo.
echo 👤 Демо-аккаунты:
echo    Оператор ДБО #1: operator1 / password123
echo    Оператор ДБО #2: operator2 / password123
echo    Клиент ДБО: client1 / password123
echo.
echo ⚠️  Для остановки сервера нажмите Ctrl+C

python manage.py runserver
pause
