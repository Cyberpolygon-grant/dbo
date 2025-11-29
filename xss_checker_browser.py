#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XSS чекер (без ORM):
- Логинится как operator2 через Playwright (headless)
- Открывает каталог услуг и ищет JS-паттерны в HTML
- Печатает: "Взломано" если найдено, иначе "Безопасно"

Коды выхода:
 0 — безопасно, 10 — взломано, 2 — ошибка
"""

import os
import re
import sys
import subprocess
import shutil
from typing import List
import html as html_mod

from playwright.sync_api import sync_playwright
from playwright._impl._errors import Error as PlaywrightError  # type: ignore

# ========= Конфигурация =========
BASE_URL = os.environ.get("BASE_URL", "http://192.168.35.134")
REVIEW_OPERATOR_EMAIL = os.environ.get("REVIEW_OPERATOR_EMAIL", "operator2@bank.ru")
REVIEW_OPERATOR_PASSWORD = os.environ.get("REVIEW_OPERATOR_PASSWORD", "password123")
BROWSER_HEADLESS = os.environ.get("BROWSER_HEADLESS", "true").lower() in {"1", "true", "yes"}

# Какие страницы услуг обходить (для режима detail-сканирования; в текущей задаче сканируем каталог):
SERVICE_IDS = [int(x) for x in os.environ.get("SERVICE_IDS", "").split(',') if x.strip().isdigit()]
SERVICE_ID_START = int(os.environ.get("SERVICE_ID_START", "20"))
SERVICE_ID_END = int(os.environ.get("SERVICE_ID_END", "20"))


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
    login_url = BASE_URL.rstrip('/') + '/login/'
    print(f"[INFO] Opening login page: {login_url}")
    page.goto(login_url, wait_until='load')
    page.fill('input[name="email"]', REVIEW_OPERATOR_EMAIL)
    page.fill('input[name="password"]', REVIEW_OPERATOR_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    print(f"[INFO] Logged in as operator2: {REVIEW_OPERATOR_EMAIL}")


EXACT_RE = re.compile(r"<script>\s*\(function\(\)\s*\{\s*function\s+approve\(\)\s*\{\s*var\s+", re.IGNORECASE | re.DOTALL)
JS_PATTERNS: List[re.Pattern] = []  # основной поиск идёт через EXACT_RE


def html_has_js(html: str) -> bool:
    if not html:
        return False
    # Разворачиваем HTML сущности (на случай, если <script> экранирован как &lt;script&gt;)
    text = html_mod.unescape(html)
    return bool(EXACT_RE.search(text))

def extract_service_cards(page) -> list:
    """Пытается извлечь карточки услуг: имя и HTML блока (на основе типовой верстки)."""
    try:
        return page.evaluate(
            """
(() => {
  const sels = ['.service-card', '.card', '[data-service-id]'];
  const titleSels = ['.card-title', '.service-name', 'h3', 'h2'];
  const seen = new Set();
  const results = [];
  for (const s of sels) {
    document.querySelectorAll(s).forEach(el => {
      const titleEl = titleSels.map(ts => el.querySelector(ts)).find(Boolean);
      const name = (titleEl && (titleEl.textContent||'').trim()) || '';
      const html = el.innerHTML || '';
      const key = name + '|' + html.length;
      if (!seen.has(key)) { seen.add(key); results.push({ name, html }); }
    });
  }
  if (results.length === 0) {
    document.querySelectorAll('section, article, li').forEach(el => {
      const titleEl = ['.card-title','h3','h2'].map(ts => el.querySelector(ts)).find(Boolean);
      const name = (titleEl && (titleEl.textContent||'').trim()) || '';
      const html = el.innerHTML || '';
      if (html.length > 100) results.push({ name, html });
    });
  }
  return results;
})()
            """
        ) or []
    except Exception:
        return []


def extract_service_detail(page) -> dict:
    """Пытается извлечь имя услуги и описание (HTML) на странице детали услуги."""
    try:
        return page.evaluate(
            """
(() => {
  const title = document.querySelector('.service-title, h1, h2, .card-title');
  let name = title ? (title.textContent||'').trim() : '';
  // Ищем строго внутри <p class="text-lg text-base-content/80 leading-relaxed">
  let descHtml = '';
  const strictP = document.querySelector(
    'p.text-lg.leading-relaxed[class*="text-base-content/80"]'
  );
  if (strictP) {
    descHtml = strictP.innerHTML || '';
  } else {
    // Фолбэк: ближайший блок после заголовка
    if (title) {
      let el = title.nextElementSibling;
      while (el && !descHtml) {
        const txt = (el.textContent||'').trim();
        if (txt && txt.length > 0) {
          descHtml = el.innerHTML || '';
          break;
        }
        el = el.nextElementSibling;
      }
    }
    if (!descHtml) {
      const cand = document.querySelector('.service-description, .description, article, .prose, .content, .card-body');
      if (cand) descHtml = cand.innerHTML || '';
    }
  }
  return { name, descHtml };
})()
            """
        ) or {"name": "", "descHtml": ""}
    except Exception:
        return {"name": "", "descHtml": ""}


def scan_service_ids(page) -> bool:
    """Обходит /services/<id>/ и проверяет JS в описании под заголовком. Логирует услугу при обнаружении."""
    ids = SERVICE_IDS or list(range(SERVICE_ID_START, SERVICE_ID_END + 1))
    if not ids:
        print("[WARN] No SERVICE_IDS or range provided; nothing to scan")
        return False
    for sid in ids:
        url = BASE_URL.rstrip('/') + f"/services/{sid}/"
        print(f"[INFO] Opening service detail: {url}")
        page.goto(url, wait_until='load')
        page.wait_for_load_state('networkidle')
        data = extract_service_detail(page)
        name = (data.get('name') or '').strip() or f'id={sid}'
        desc_html = data.get('descHtml') or ''
        if html_has_js(desc_html):
            print(f"[HIT] JS-like patterns in service: '{name}' ({sid}) @ {url}")
            return True
    return False


def scan_banking_services_cards(page) -> bool:
    """Сканирует страницу каталога /banking-services/ и ищет JS внутри <div class="card-body p-6">.
    Логирует название услуги (если удалось извлечь) и URL.
    """
    url = BASE_URL.rstrip('/') + '/banking-services/'
    print(f"[INFO] Opening catalog: {url}")
    page.goto(url, wait_until='load')
    try:
        page.wait_for_selector('div.card-body.p-6', timeout=5000)
    except Exception:
        pass
    page.wait_for_load_state('networkidle')

    # По требованию: сначала проверяем всю страницу целиком
    full_html = page.content()
    if html_has_js(full_html):
        print(f"[HIT] Exact payload substring found in full page HTML: {url}")
        return True

    try:
        cards = page.evaluate(
            """
(() => {
  const nodes = Array.from(document.querySelectorAll('div.card-body.p-6'));
  return nodes.map(el => {
    const titleEl = el.querySelector('.card-title, .service-name, h3, h2')
                  || el.closest('.card')?.querySelector('.card-title, .service-name, h3, h2');
    const name = (titleEl && (titleEl.textContent||'').trim()) || '';
    const html = el.innerHTML || '';
    return { name, html };
  });
})()
            """
        ) or []
    except Exception:
        cards = []

    found = False
    for c in cards:
        desc_html = c.get('html') or ''
        if html_has_js(desc_html):
            name = (c.get('name') or '').strip() or 'unknown'
            print(f"[HIT] JS-like patterns in service: '{name}' @ {url}")
            found = True
    return found


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

        # По требованию: сканировать /banking-services/ внутри <div class="card-body p-6">
        compromised = scan_banking_services_cards(page)
        context.close()
        browser.close()

        if compromised:
            print("Взломано")
            sys.exit(10)
        else:
            print("Безопасно")
            sys.exit(0)


if __name__ == '__main__':
    main()
