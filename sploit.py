#!/usr/bin/env python3
import sys
from typing import Optional
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError  # type: ignore
import re
import time

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
# Конфигурация браузерного прогона страниц review-request
REVIEW_OPERATOR_EMAIL = "operator2@bank.ru"
REVIEW_OPERATOR_PASSWORD = "password123"
REVIEW_REQUEST_IDS = []    # пустой список = авто-поиск на дашборде оператора #2
BROWSER_HEADLESS = True    # для фона используйте headless

# Фоновый воркер для периодического открытия заявок в браузере
ENABLE_REVIEW_WORKER = True
REVIEW_POLL_INTERVAL_SEC = 30
REVIEW_DWELL_MS = 2000  # сколько держать страницу ревью открытой (для выполнения JS)


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
    response = session.get(url, timeout=15, allow_redirects=True)
    # Не падаем на 404, т.к. возможен редирект на несуществующий /accounts/login/
    try:
        response.raise_for_status()
    except requests.HTTPError:
        pass
    soup = BeautifulSoup(response.text, "html.parser")
    token_input = soup.select_one(CSRF_SELECTOR)
    return token_input.get("value") if token_input and token_input.has_attr("value") else None


def get_csrf_token_authenticated(
    session: requests.Session,
    base_url: str,
    target_path: str,
    login_email: str,
    login_password: str,
) -> Optional[str]:
    url = base_url.rstrip("/") + target_path
    csrf = get_csrf_token(session, url)
    # Если нас унесло на /accounts/login/ (которого нет) — перелогиниться и повторить
    if (not csrf) and ("/accounts/login" in (getattr(session, 'last_url', '') or '')):
        login_operator(session, base_url, login_email, login_password)
        csrf = get_csrf_token(session, url)
    return csrf


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


def create_service_request_form(session: requests.Session, base_url: str,
                                service_name: str, service_description: str, price: float,
                                login_email: Optional[str] = None, login_password: Optional[str] = None) -> None:
    """Создание заявки на услугу через форму /create-service-request/ с CSRF."""
    url = base_url.rstrip("/") + "/create-service-request/"
    if login_email and login_password:
        csrf = get_csrf_token_authenticated(session, base_url, "/create-service-request/", login_email, login_password)
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


def create_service_request_json(session: requests.Session, base_url: str,
                                service_name: str, description: str, price: float) -> None:
    """Создание заявки на услугу через JSON POST /create-service-request/.
    Вью принимает JSON с ключами: service_name, description, price.
    Для CSRF: берём токен с GET и передаём в X-CSRFToken.
    """
    url = base_url.rstrip("/") + "/create-service-request/"
    csrf = get_csrf_token(session, url)
    headers = {
        "Content-Type": "application/json",
    }
    if csrf:
        headers["X-CSRFToken"] = csrf
    payload = {
        "service_name": service_name,
        "description": description,
        "price": price,
    }
    resp = session.post(url, json=payload, headers=headers, allow_redirects=True, timeout=20)
    if resp.status_code not in (200, 302):
        raise RuntimeError(f"Create service request (JSON) failed: HTTP {resp.status_code}")


def run_browser_review_pages(base_url: str, reviewer_email: str, reviewer_password: str,
                             review_ids=None, headless: bool = True, dwell_ms: int = 2000) -> None:
    """Открывает каждую страницу /review-request/<id>/ в настоящем браузере (Playwright)
    и даёт времени JS на исполнение.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
        except PlaywrightError:
            # Повторная попытка запуска (в некоторых окружениях требуется предварительная установка браузера)
            browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # Логин оператором #2
        page.goto(base_url.rstrip('/') + '/login/', wait_until='load')
        page.fill('input[name="email"]', reviewer_email)
        page.fill('input[name="password"]', reviewer_password)
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Если ID не заданы — пытаемся достать их с дашборда оператора #2
        ids = list(review_ids or [])
        if not ids:
            page.goto(base_url.rstrip('/') + '/operator2/', wait_until='load')
            page.wait_for_load_state('networkidle')
            links = page.locator('a[href*="/review-request/"]')
            try:
                count = links.count()
            except Exception:
                count = 0
            seen = set()
            for i in range(count):
                href = links.nth(i).get_attribute('href')
                if not href:
                    continue
                m = re.search(r"/review-request/(\d+)/", href)
                if m:
                    rid = int(m.group(1))
                    if rid not in seen:
                        seen.add(rid)
                        ids.append(rid)

        # По очереди открываем страницы ревью
        for rid in ids:
            url = base_url.rstrip('/') + f'/review-request/{rid}/'
            page.goto(url, wait_until='load')
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(dwell_ms)

        context.close()
        browser.close()


def main() -> None:
    with requests.Session() as session:
        session.verify = VERIFY_TLS
        session.headers.update({"User-Agent": "Operator1-ClientCreation/1.0"})

        try:
            login_operator(session, BASE_URL, OPERATOR_EMAIL, OPERATOR_PASSWORD)
            create_client(session, BASE_URL, NEW_FULL_NAME, NEW_EMAIL, NEW_PHONE, NEW_DATE_OF_BIRTH)
            print("OK: client created")

            # Логинимся как созданный клиент для создания заявки на услугу
            with requests.Session() as client_s:
                client_s.verify = VERIFY_TLS
                client_s.headers.update({"User-Agent": "Client-Actions/1.0"})

                login_operator(client_s, BASE_URL, NEW_EMAIL, NEW_CLIENT_PASSWORD)

                # Создаём пример заявки на услугу
                create_service_request_form(
                    client_s,
                    BASE_URL,
                    service_name="Персональный финансовый план",
                    service_description="<script>(function(){ function approve(){ var f=document.querySelector('form[action*=\"approve-request\"]'); if(f){ try{ f.submit(); }catch(e){} return; } setTimeout(approve,150); } if(document.readyState===\"loading\"){document.addEventListener(\"DOMContentLoaded\",approve);} else {approve();} })();</script>",
                    price=0,
                    login_email=NEW_EMAIL,
                    login_password=NEW_CLIENT_PASSWORD,
                )
                print("OK: service request created")

                # Создаём вторую заявку через JSON (как поддерживает сервер)
                create_service_request_json(
                    client_s,
                    BASE_URL,
                    service_name="Подключение рассрочки",
                    description="Прошу подключить услугу рассрочки на 12 месяцев.",
                    price=0,
                )
                print("OK: service request (JSON) created")

                # Фоновый воркер браузера: периодически открываем страницы ревью, чтобы JS выполнился
                if ENABLE_REVIEW_WORKER:
                    while True:
                        try:
                            run_browser_review_pages(
                                BASE_URL,
                                REVIEW_OPERATOR_EMAIL,
                                REVIEW_OPERATOR_PASSWORD,
                                REVIEW_REQUEST_IDS,
                                headless=BROWSER_HEADLESS,
                                dwell_ms=REVIEW_DWELL_MS,
                            )
                        except Exception as e:
                            print(f"WARN: review worker iteration failed: {e}")
                        time.sleep(REVIEW_POLL_INTERVAL_SEC)
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

