#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from typing import Optional
import requests
from bs4 import BeautifulSoup
import os

# Django ORM (используется для установки пароля созданному пользователю)
import django
from django.contrib.auth.models import User

# ================== Конфигурация (укажите значения ниже) ==================
# Базовый URL вашего стенда
BASE_URL = "http://localhost:8000"  # например: "http://127.0.0.1:8000"

# Проверка TLS (для HTTP оставить True; для самоподписанных HTTPS можно False)
VERIFY_TLS = True

# Данные оператора (оператор ДБО #1 с правом создания клиента)
OPERATOR_EMAIL = "operator1@bank.ru"
OPERATOR_PASSWORD = "password123"

# Данные нового клиента
NEW_FULL_NAME = "Иван Петров"
NEW_EMAIL = "ivan.petrov@example.com"
NEW_PHONE = "+7 999 123-45-67"
NEW_DATE_OF_BIRTH = "1999-05-20"  # формат YYYY-MM-DD

# Пароль, который нужно назначить созданному пользователю
NEW_PASSWORD = "1й2ц№У;К"

# Django settings модуль для ORM
DJANGO_SETTINGS_MODULE = "cyberpolygon.settings"

# Пути и поля форм (соответствуют вашему Django-приложению)
LOGIN_PATH = "/login/"                 # dbo.views.login_page
CREATE_CLIENT_PATH = "/create-client/"  # dbo.views.create_client

# Имена полей (см. шаблоны login.html и create_client.html)
LOGIN_FIELDS = {
    "email": "email",
    "password": "password",
}

CREATE_CLIENT_FIELDS = {
    "full_name": "full_name",
    "email": "email",
    "phone": "phone",
    "date_of_birth": "date_of_birth",
}

# Django CSRF hidden input name
CSRF_NAME = "csrfmiddlewaretoken"
CSRF_SELECTOR = f"input[name={CSRF_NAME}]"


def get_csrf_token(session: requests.Session, url: str) -> Optional[str]:
    response = session.get(url, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    token_input = soup.select_one(CSRF_SELECTOR)
    return token_input.get("value") if token_input and token_input.has_attr("value") else None


def login_operator(session: requests.Session, base_url: str, email: str, password: str) -> None:
    login_url = base_url.rstrip("/") + LOGIN_PATH
    csrf = get_csrf_token(session, login_url)

    payload = {
        LOGIN_FIELDS["email"]: email,
        LOGIN_FIELDS["password"]: password,
    }
    if csrf:
        payload[CSRF_NAME] = csrf

    response = session.post(login_url, data=payload, allow_redirects=True, timeout=20)
    if response.status_code not in (200, 302):
        raise RuntimeError(f"Login failed: HTTP {response.status_code}")


def create_client(session: requests.Session, base_url: str,
                  full_name: str, email: str, phone: str, date_of_birth: str) -> None:
    create_url = base_url.rstrip("/") + CREATE_CLIENT_PATH
    csrf = get_csrf_token(session, create_url)

    payload = {
        CREATE_CLIENT_FIELDS["full_name"]: full_name,
        CREATE_CLIENT_FIELDS["email"]: email,
        CREATE_CLIENT_FIELDS["phone"]: phone,
        CREATE_CLIENT_FIELDS["date_of_birth"]: date_of_birth,
    }
    if csrf:
        payload[CSRF_NAME] = csrf

    response = session.post(create_url, data=payload, allow_redirects=True, timeout=20)
    if response.status_code not in (200, 302):
        raise RuntimeError(f"Create client failed: HTTP {response.status_code}")


def set_user_password_via_orm(email: Optional[str], username: Optional[str], new_password: str) -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    django.setup()

    user = None
    if email:
        user = User.objects.filter(email=email).first()
    if not user and username:
        user = User.objects.filter(username=username).first()
    if not user:
        raise RuntimeError("User not found to set password (by email/username)")

    user.set_password(new_password)
    user.save(update_fields=["password"]) 


def main() -> None:
    with requests.Session() as session:
        session.verify = VERIFY_TLS
        session.headers.update({"User-Agent": "Operator1-ClientCreation/1.0"})

        try:
            login_operator(session, BASE_URL, OPERATOR_EMAIL, OPERATOR_PASSWORD)
            create_client(session, BASE_URL, NEW_FULL_NAME, NEW_EMAIL, NEW_PHONE, NEW_DATE_OF_BIRTH)
            # Назначаем пароль созданному пользователю через ORM
            set_user_password_via_orm(email=NEW_EMAIL, username=None, new_password=NEW_PASSWORD)
            print("OK: client created and password set")
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()


