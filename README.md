# DBO - Digital Banking Operations

Django-приложение для управления банковскими операциями.

## Структура проекта

```
dbo/
├── cyberpolygon/          # Настройки Django проекта
│   ├── settings.py        # Конфигурация приложения
│   ├── urls.py            # Главный URL роутер
│   ├── wsgi.py            # WSGI конфигурация
│   └── asgi.py            # ASGI конфигурация
│
├── dbo/                   # Основное приложение
│   ├── models.py          # Модели данных
│   ├── views.py           # Представления (views)
│   ├── admin.py           # Админ-панель
│   ├── context_processors.py
│   ├── logging_helper.py
│   │
│   ├── templates/         # HTML шаблоны
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── client_dashboard.html
│   │   ├── operator1_dashboard.html
│   │   ├── operator2_dashboard.html
│   │   └── services/      # Шаблоны сервисов
│   │
│   ├── management/        # Кастомные команды управления
│   │   └── commands/
│   │       ├── init_banking_services.py
│   │       ├── check_users.py
│   │       ├── check_news_stats.py
│   │       ├── clear_demo_data.py
│   │       └── expose_privileged_services.py
│   │
│   ├── migrations/        # Миграции базы данных
│   └── templatetags/     # Кастомные теги шаблонов
│
├── static/                # Статические файлы
│   ├── css/               # Стили (daisyUI, Tailwind)
│   └── js/                # JavaScript файлы
│
├── manage.py              # Django CLI утилита
├── requirements.txt       # Зависимости Python
├── db.sqlite3             # База данных SQLite
│
├── Dockerfile             # Docker образ для приложения
├── Dockerfile.bot         # Docker образ для бота
├── Dockerfile.user_bot    # Docker образ для user бота
├── docker-compose.yml     # Docker Compose конфигурация
│
├── dbo_user_bot.py        # Бот пользователя
├── operator2_bot.py       # Бот оператора 2
├── init_data.py           # Скрипт инициализации данных
├── exploit_sqli_idor.py   # Эксплойт для тестирования
├── create_xss_request.py  # Скрипт создания XSS запроса
│
└── DEPLOYMENT_UBUNTU.md   # Инструкции по развертыванию
```

## Основные компоненты

- **Django 5.2+** - веб-фреймворк
- **daisyUI + Tailwind CSS** - UI компоненты
- **SQLite/PostgreSQL** - база данных
- **Docker** - контейнеризация
- **Gunicorn** - WSGI сервер

## Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# запуск
sudo ./restart.sh
```

