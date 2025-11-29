#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XSS чекер, ориентируется на браузер (без ORM):
- Логинится как operator2 через Playwright
- Открывает страницы каталога услуг и ищет JS-паттерны в HTML
- Печатает: «Взломано», если нашёл, иначе «Безопасно»
Коды выхода: 0 — безопасно, 10 — взломано, 2 — ошибка
"""

import os
import re
import sys
import subprocess
import shutil
from typing import List

from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError  # type: ignore

# ========= Конфигурация =========
BASE_URL = os.environ.get("BASE_URL", "http://192.168.35.134")
REVIEW_OPERATOR_EMAIL = os.environ.get("REVIEW_OPERATOR_EMAIL", "operator2@bank.ru")
REVIEW_OPERATOR_PASSWORD = os.environ.get("REVIEW_OPERATOR_PASSWORD", "password123")
BROWSER_HEADLESS = os.environ.get("BROWSER_HEADLESS", "true").lower() in {"1", "true", "yes"}


def ensure_playwright_browsers_installed() -> None:
    try:
        print("[INFO] Ensuring Playwright chromium browser is installed (via python -m playwright)")
        subprocess.run([shutil.which("python") or "python", "-m", "playwright", "install", "chromium"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            print("[INFO] Ensuring Playwright chromium browser is installed (via playwright CLI)")
            subprocess.run([shutil.which("playwright") or "playwright", "install", "chromium"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            print("[WARN] Could not auto-install Playwright browsers; proceeding anyway")


def login_operator2(page) -> None:
    print(f"[INFO] Opening login page: {BASE_URL.rstrip('/') + '/login/'}")
    page.goto(BASE_URL.rstrip('/') + '/login/', wait_until='load')
    page.fill('input[name="email"]', REVIEW_OPERATOR_EMAIL)
    page.fill('input[name="password"]', REVIEW_OPERATOR_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    print(f"[INFO] Logged in as operator2: {REVIEW_OPERATOR_EMAIL}")


JS_PATTERNS: List[re.Pattern] = [
    re.compile(r"<\s*script\b", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"javascript:\s*", re.IGNORECASE),
]


def html_has_js(html: str) -> bool:
    if not html:
        return False
    for pat in JS_PATTERNS:
        if pat.search(html):
            return True
    return False


def scan_catalog(page) -> bool:
    """Возвращает True, если найден потенциальный JS в HTML каталога."""
    # Основной публичный каталог
    url = BASE_URL.rstrip('/') + '/banking-services/'
    print(f"[INFO] Opening catalog: {url}")
    page.goto(url, wait_until='load')
    page.wait_for_load_state('networkidle')
    html = page.content()
    return html_has_js(html)


def main() -> None:
    print(f"[INFO] Starting XSS checker (browser) | base_url={BASE_URL} headless={BROWSER_HEADLESS}")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=BROWSER_HEADLESS)
        except PlaywrightError:
            ensure_playwright_browsers_installed()
            browser = p.chromium.launch(headless=BROWSER_HEADLESS)
        context = browser.new_context()
        page = context.new_page()

        # Логин как оператор #2
        login_operator2(page)

        compromised = scan_catalog(page)
        if compromised:
            print("Взломано")
            sys.exit(10)
        else:
            print("Безопасно")
            sys.exit(0)


if __name__ == '__main__':
    main()


