#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError  # type: ignore
import subprocess
import shutil
import os
import re
import time
from typing import List


# ========= Конфигурация =========
BASE_URL = os.environ.get("BASE_URL", "http://192.168.35.134")
REVIEW_OPERATOR_EMAIL = os.environ.get("REVIEW_OPERATOR_EMAIL", "operator2@bank.ru")
REVIEW_OPERATOR_PASSWORD = os.environ.get("REVIEW_OPERATOR_PASSWORD", "password123")

# Если пусто — ID будут автоматически извлечены с дашборда оператора #2
def _parse_ids(env_val: str) -> List[int]:
    ids: List[int] = []
    for chunk in env_val.split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.append(int(chunk))
        except ValueError:
            pass
    return ids

REVIEW_REQUEST_IDS: List[int] = _parse_ids(os.environ.get("REVIEW_REQUEST_IDS", ""))

# Режимы работы
BROWSER_HEADLESS = os.environ.get("BROWSER_HEADLESS", "true").lower() in {"1", "true", "yes"}
REVIEW_POLL_INTERVAL_SEC = int(os.environ.get("REVIEW_POLL_INTERVAL_SEC", "30"))
REVIEW_DWELL_MS = int(os.environ.get("REVIEW_DWELL_MS", "2000"))  # Сколько держать страницу, чтобы JS выполнился

# Простой вывод в консоль (print)


def login_operator2(page) -> None:
    print(f"[INFO] Opening login page: {BASE_URL.rstrip('/') + '/login/'}")
    page.goto(BASE_URL.rstrip('/') + '/login/', wait_until='load')
    page.fill('input[name="email"]', REVIEW_OPERATOR_EMAIL)
    page.fill('input[name="password"]', REVIEW_OPERATOR_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    print(f"[INFO] Logged in as operator2: {REVIEW_OPERATOR_EMAIL}")


def collect_review_ids(page) -> List[int]:
    """Собирает ID заявок /review-request/<id>/ с дашборда оператора #2."""
    ids: List[int] = []
    seen = set()
    print("[INFO] Navigating to operator2 dashboard to collect review IDs")
    page.goto(BASE_URL.rstrip('/') + '/operator2/', wait_until='load')
    page.wait_for_load_state('networkidle')
    links = page.locator('a[href*="/review-request/"]')
    try:
        count = links.count()
    except Exception:
        count = 0
    print(f"[INFO] Found {count} links to review pages")
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
    print(f"[INFO] Collected review IDs: {ids}")
    return ids


def open_review_pages(page, ids: List[int]) -> None:
    for rid in ids:
        url = BASE_URL.rstrip('/') + f'/review-request/{rid}/'
        print(f"[INFO] Opening review page: {url}")
        page.goto(url, wait_until='load')
        page.wait_for_load_state('networkidle')
        print(f"[INFO] Dwelling on page for {REVIEW_DWELL_MS} ms to allow JS execution")
        page.wait_for_timeout(REVIEW_DWELL_MS)


def ensure_playwright_browsers_installed() -> None:
    """Пытается установить браузеры Playwright автоматически при необходимости."""
    # Если playwright browsers не установлены, команда ниже установит их.
    # Пробуем использовать системный Python для универсальности.
    try:
        print("[INFO] Ensuring Playwright chromium browser is installed (via python -m playwright)")
        subprocess.run([shutil.which("python") or "python", "-m", "playwright", "install", "chromium"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Пытаемся альтернативно вызвать бинарь playwright, если доступен
        try:
            print("[INFO] Ensuring Playwright chromium browser is installed (via playwright CLI)")
            subprocess.run([shutil.which("playwright") or "playwright", "install", "chromium"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            # Оставляем как есть — запуск ниже упадет с понятной ошибкой
            print("[WARN] Could not auto-install Playwright browsers; proceeding anyway")
            pass


def main() -> None:
    print(f"[INFO] Starting review worker | base_url={BASE_URL} headless={BROWSER_HEADLESS} interval={REVIEW_POLL_INTERVAL_SEC}s dwell={REVIEW_DWELL_MS}ms")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=BROWSER_HEADLESS)
        except PlaywrightError:
            # Автоустановка браузеров и повторная попытка
            ensure_playwright_browsers_installed()
            browser = p.chromium.launch(headless=BROWSER_HEADLESS)
        context = browser.new_context()
        page = context.new_page()

        # Логин как оператор #2
        login_operator2(page)

        # Фоновый цикл
        while True:
            try:
                # Если нас выкинуло на страницу логина — перелогиниваемся
                if page.url.endswith('/login/'):
                    print("[INFO] Session seems logged out, re-authenticating")
                    login_operator2(page)
                ids = list(REVIEW_REQUEST_IDS)
                if not ids:
                    ids = collect_review_ids(page)
                if ids:
                    print(f"[INFO] Processing {len(ids)} review pages")
                    open_review_pages(page, ids)
                else:
                    print("[INFO] No review pages found; sleeping")
            except Exception as e:
                print(f"[WARN] Iteration error: {e}")
            print(f"[INFO] Sleeping for {REVIEW_POLL_INTERVAL_SEC} seconds")
            time.sleep(REVIEW_POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()


