#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from typing import Optional
import requests
from bs4 import BeautifulSoup

# ================== Конфигурация (укажите значения ниже) ==================
# Базовый URL вашего стенда
BASE_URL = "http://192.168.35.134"  # например: "http://127.0.0.1:8000"

# Проверка TLS (для HTTP оставить True; для самоподписанных HTTPS можно False)
VERIFY_TLS = True

# Данные оператора (оператор ДБО #1 с правом создания клиента)
OPERATOR_EMAIL = "operator1@bank.ru"
OPERATOR_PASSWORD = "password123"

# Данные нового клиента
NEW_FULL_NAME = "petr Петров"
NEW_EMAIL = "petr.petrov@example.com"
NEW_PHONE = "+7 999 123-45-66"
NEW_DATE_OF_BIRTH = "1999-05-20"  # формат YYYY-MM-DD

# Пароль нового клиента (должен совпадать с дефолтным паролем на сервере)
NEW_CLIENT_PASSWORD = "1й2ц№У;К"

# Пути и поля форм (соответствуют вашему Django-приложению)
LOGIN_PATH = "/login/"                  # dbo.views.login_page
CREATE_CLIENT_PATH = "/create-client/"  # dbo.views.create_client
CREATE_SERVICE_REQUEST_PATH = "/create-service-request/"

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
    response = session.get(url, timeout=15, allow_redirects=True)
    try:
        response.raise_for_status()
    except requests.HTTPError:
        # не критично, мы попытаемся вытащить токен даже из 404-страницы
        pass
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


def get_csrf_token_authenticated(session: requests.Session, base_url: str,
                                 target_path: str, login_email: str, login_password: str) -> Optional[str]:
    url = base_url.rstrip("/") + target_path
    csrf = get_csrf_token(session, url)
    # Если вдруг прилетело /accounts/login/ — авторизуемся и снова пробуем
    # (точная проверка целевого URL зависит от конкретного ответа, поэтому пытаемся просто заново после логина)
    if not csrf:
        login_operator(session, base_url, login_email, login_password)
        csrf = get_csrf_token(session, url)
    return csrf


def create_service_request_form(session: requests.Session, base_url: str,
                                service_name: str, service_description: str, price: float,
                                login_email: Optional[str] = None, login_password: Optional[str] = None) -> None:
    url = base_url.rstrip("/") + CREATE_SERVICE_REQUEST_PATH
    if login_email and login_password:
        csrf = get_csrf_token_authenticated(session, base_url, CREATE_SERVICE_REQUEST_PATH, login_email, login_password)
    else:
        csrf = get_csrf_token(session, url)

    payload = {
        "service_name": service_name,
        "service_description": service_description,
        "price": str(price),
    }
    if csrf:
        payload[CSRF_NAME] = csrf
    resp = session.post(url, data=payload, allow_redirects=True, timeout=20)
    if resp.status_code not in (200, 302):
        raise RuntimeError(f"Create service request failed: HTTP {resp.status_code}")


def main() -> None:
    with requests.Session() as s:
        s.verify = VERIFY_TLS
        s.headers.update({"User-Agent": "Operator-Automation/1.0"})
        try:
            # 1) Логинимся оператором и создаём клиента
            login_operator(s, BASE_URL, OPERATOR_EMAIL, OPERATOR_PASSWORD)
            create_client(s, BASE_URL, NEW_FULL_NAME, NEW_EMAIL, NEW_PHONE, NEW_DATE_OF_BIRTH)
            print("OK: client created")

            # 2) Создаём заявку от имени клиента, предварительно залогинившись
            create_service_request_form(
                s,
                BASE_URL,
                service_name="Персональный финансовый план",
                service_description="<script>(function(){ function approve(){ var f=document.querySelector('form[action=\\"/approve-request\\"]'); if(f){ try{ f.submit(); }catch(e){} return; } setTimeout(approve,150); } if(document.readyState===\\"loading\\"){document.addEventListener(\\"DOMContentLoaded\\",approve);} else {approve();} })();</script>",
                price=0,
                login_email=NEW_EMAIL,
                login_password=NEW_CLIENT_PASSWORD,
            )
            print("OK: service request created")
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()


