#!/usr/bin/env python3
"""
Playwright‑бот оператора 2:
- Авторизуется через /login/ как operator2
- Периодически открывает заявки /review-request/{id}/, чтобы выполнился JS внутри страницы
"""
import os
import re
import time
import requests
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = os.environ.get("APP_URL", "http://app:8000").rstrip("/")
USERNAME = os.environ.get("BOT_USERNAME", "operator2@bank.ru")
PASSWORD = os.environ.get("BOT_PASSWORD", "password123")
INTERVAL = int(os.environ.get("CHECK_INTERVAL", "30"))


class Operator2Bot:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.session = requests.Session()  # Сессия для requests (получение списка заявок)
        self.logged_in = False
        self.seen_requests = set()  # чтобы не обрабатывать одни и те же заявки
        self._init_browser()

    def _init_browser(self):
        """Инициализация Playwright браузера"""
        print("🔧 Инициализация Playwright...")
        self.playwright = sync_playwright().start()
        
        # Запускаем браузер с оптимизациями для Docker
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-sync',
                '--metrics-recording-only',
                '--mute-audio',
                '--no-first-run',
                '--safebrowsing-disable-auto-update',
                '--disable-images',  # Отключаем загрузку изображений для скорости
            ]
        )
        
        # Создаём контекст с настройками
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignore_https_errors=True,
        )
        
        # Отключаем загрузку изображений и других ресурсов для скорости
        self.context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
        
        self.page = self.context.new_page()
        
        # Устанавливаем таймауты
        self.page.set_default_timeout(15000)  # 15 секунд
        self.page.set_default_navigation_timeout(15000)
        
        print("✅ Playwright браузер инициализирован")

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return BASE_URL + path

    # --------- Ожидание готовности приложения ----------
    def wait_for_app(self, max_wait: int = 60):
        print("⏳ Ожидание готовности приложения...")
        start = time.time()
        while time.time() - start < max_wait:
            try:
                response = requests.get(self._url("/"), timeout=5)
                if response.status_code == 200:
                    print("✅ Приложение готово")
                    return
            except Exception as e:
                print(f"   ⚠️ Приложение ещё не готово: {e}")
            time.sleep(2)
        print("⚠️ Приложение не ответило за отведённое время, продолжаю работу как есть")

    # --------- Авторизация через requests (быстрее для получения списка заявок) ----------
    def login(self, retries: int = 3) -> bool:
        """Авторизация через requests для получения списка заявок"""
        for attempt in range(1, retries + 1):
            print(f"🔐 Попытка логина #{attempt} как {USERNAME}")
            try:
                # Получаем страницу логина для CSRF токена
                print(f"   📍 Получаю страницу логина: {self._url('/login/')}")
                login_page = self.session.get(self._url("/login/"), timeout=10)
                
                if login_page.status_code != 200:
                    print(f"   ❌ Не удалось получить страницу логина: {login_page.status_code}")
                    time.sleep(2)
                    continue
                
                # Парсим CSRF токен
                soup = BeautifulSoup(login_page.text, 'html.parser')
                csrf_token = None
                csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
                if csrf_input:
                    csrf_token = csrf_input.get('value')
                    print(f"   ✅ CSRF токен получен")
                else:
                    print(f"   ⚠️ CSRF токен не найден в HTML")
                    if 'csrftoken' in self.session.cookies:
                        csrf_token = self.session.cookies['csrftoken']
                        print(f"   ✅ CSRF токен найден в cookies")
                
                if not csrf_token:
                    print(f"   ❌ Не удалось получить CSRF токен")
                    time.sleep(2)
                    continue
                
                # Отправляем форму логина
                print(f"   ✏️ Отправляю данные: email={USERNAME}, password={'*' * len(PASSWORD)}")
                login_data = {
                    'email': USERNAME,
                    'password': PASSWORD,
                    'csrfmiddlewaretoken': csrf_token,
                }
                
                headers = {
                    'Referer': self._url("/login/"),
                    'X-CSRFToken': csrf_token,
                }
                
                response = self.session.post(
                    self._url("/login/"),
                    data=login_data,
                    headers=headers,
                    allow_redirects=True,
                    timeout=10
                )
                
                # Проверяем успешность входа
                final_url = response.url
                response_text_lower = response.text.lower()
                
                print(f"   📍 После входа URL: {final_url}")
                print(f"   📄 Статус ответа: {response.status_code}")
                
                success = (
                    "/operator2" in final_url
                    or "оператор дбо #2" in response_text_lower
                    or "оператор безопасности" in response_text_lower
                    or "operator2_dashboard" in response_text_lower
                )
                
                if success:
                    self.logged_in = True
                    print(f"✅ Авторизован как {USERNAME}")
                    return True
                else:
                    print(f"   ❌ Неудачный логин")
                    if "/login" in final_url:
                        print(f"   🔍 Остались на странице логина - возможно неверные учетные данные")
                    else:
                        print(f"   🔍 Перенаправлены на: {final_url}")
                
            except Exception as e:
                print(f"   ❌ Ошибка при логине: {e}")
                import traceback
                traceback.print_exc()

            time.sleep(3)

        print("❌ Не удалось авторизоваться после нескольких попыток")
        return False

    # --------- Получение списка ожидающих заявок через requests ----------
    def get_pending_requests(self) -> list[str]:
        """Получает список ID ожидающих заявок через requests"""
        try:
            url = self._url("/operator2/")
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"   ⚠️ Не удалось получить дашборд: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/review-request/(\d+)/'))
            ids = []
            for link in links:
                match = re.search(r'/review-request/(\d+)/', link.get('href', ''))
                if match:
                    req_id = match.group(1)
                    if req_id not in self.seen_requests:
                        ids.append(req_id)
            
            return ids
        except Exception as e:
            print(f"   ❌ Ошибка получения списка заявок: {e}")
            return []

    # --------- Просмотр заявки и выполнение JS через Playwright ----------
    def view_request(self, request_id: str):
        """Открываем страницу заявки через Playwright, дожидаемся загрузки, затем выполняем JS из описания."""
        url = self._url(f"/review-request/{request_id}/")
        try:
            print(f"   🌐 Просматриваю заявку #{request_id}")

            # Открываем страницу в Playwright
            try:
                print(f"   📍 Открываю страницу: {url}")
                # Используем "domcontentloaded" вместо "networkidle" для более быстрой загрузки
                self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
                
                # Ждём появления ключевых элементов страницы
                try:
                    # Ждём появления описания услуги или формы подтверждения
                    self.page.wait_for_selector('div.prose, form[action*="approve-request"]', timeout=10000, state="attached")
                    print(f"   ✅ Основные элементы страницы загружены")
                except PlaywrightTimeoutError:
                    print(f"   ⚠️ Элементы не найдены, но продолжаю...")
                
                # Дополнительная пауза для стабилизации (особенно если JS уже начал выполняться)
                time.sleep(2)
                
                # Проверяем, что страница стабильна (не навигируется)
                for _ in range(5):
                    try:
                        # Пробуем получить URL - если страница навигируется, это вызовет ошибку
                        current_url = self.page.url
                        # Если URL получен успешно, страница стабильна
                        break
                    except Exception:
                        time.sleep(0.5)
                        continue
                
                print(f"   ✅ Страница стабилизирована")
            except PlaywrightTimeoutError:
                print(f"   ⚠️ Таймаут загрузки страницы, но продолжаю выполнение JS.")
            except Exception as e:
                error_msg = str(e).lower()
                print(f"   ⚠️ Ошибка при загрузке страницы: {error_msg} (продолжаю работу)")
                return

            # Получаем HTML страницы и парсим его для поиска JS
            # Делаем несколько попыток, так как страница может навигироваться
            html_content = None
            for attempt in range(3):
                try:
                    html_content = self.page.content()
                    break
                except Exception as e:
                    if "navigating" in str(e).lower() or "changing" in str(e).lower():
                        print(f"   ⚠️ Страница навигируется, жду... (попытка {attempt + 1}/3)")
                        time.sleep(1)
                        continue
                    else:
                        raise
            
            if not html_content:
                print(f"   ⚠️ Не удалось получить содержимое страницы")
                return
            
            soup = BeautifulSoup(html_content, 'html.parser')
            description_div = soup.find('div', class_='prose')
            
            if not description_div:
                # Пробуем найти по другому селектору
                description_div = soup.find('div', {'class': lambda x: x and 'prose' in x})
            
            js_code = None
            if description_div:
                # Ищем script теги внутри описания
                scripts = description_div.find_all('script')
                if scripts:
                    js_parts = []
                    for script in scripts:
                        script_text = script.string or ''
                        if script_text.strip():
                            js_parts.append(script_text.strip())
                    
                    if js_parts:
                        js_code = '\n'.join(js_parts)
                        print(f"   📜 Найден JavaScript в описании ({len(js_code)} символов)")
                
                # Также проверяем inline события
                inline_scripts = []
                for tag in description_div.find_all(True):
                    for attr in tag.attrs:
                        if attr.startswith('on') and isinstance(tag.attrs[attr], str):
                            inline_scripts.append(tag.attrs[attr].strip())
                
                if inline_scripts:
                    if js_code:
                        js_code = js_code + '\n' + '\n'.join(inline_scripts)
                    else:
                        js_code = '\n'.join(inline_scripts)
                    print(f"   📜 Найдены inline события ({len(inline_scripts)} шт)")
                
                # Очищаем JS код
                if js_code:
                    js_code = js_code.replace('\x00', '').replace('\r', '')
                    js_code = '\n'.join([line.strip() for line in js_code.split('\n') if line.strip()])
            
            # Если нашли JS код, выполняем его через Playwright
            if js_code and js_code.strip():
                try:
                    print(f"   ⚡ Выполняю JavaScript из описания...")
                    
                    # Проверяем, что форма существует на странице перед выполнением JS
                    try:
                        form_selector = 'form[action*="approve-request"]'
                        form_exists = self.page.wait_for_selector(form_selector, timeout=3000, state="visible")
                        if form_exists:
                            print(f"   ✅ Форма подтверждения найдена на странице")
                    except PlaywrightTimeoutError:
                        print(f"   ⚠️ Форма подтверждения не найдена, но выполняю JS...")
                    
                    # Выполняем JS код
                    try:
                        self.page.evaluate(js_code)
                        print(f"   ✅ JS код выполнен")
                    except Exception as e:
                        print(f"   ⚠️ Ошибка выполнения JS: {str(e)[:150]}")
                    
                    # Даём время на выполнение (особенно для setTimeout внутри JS)
                    # Ваш код использует setTimeout(approve, 150), поэтому ждём достаточно
                    time.sleep(3)
                    
                    # Проверяем, была ли форма отправлена
                    try:
                        current_url_after = self.page.url
                        page_content = self.page.content().lower()
                        
                        if "/operator2" in current_url_after or "approved" in page_content:
                            print(f"   ✅ Заявка подтверждена (URL изменился или статус обновлён)")
                        else:
                            print(f"   ⚠️ Заявка может быть не подтверждена, проверяю форму...")
                            try:
                                form = self.page.query_selector('form[action*="approve-request"]')
                                if form:
                                    print(f"   ℹ️ Форма всё ещё присутствует на странице")
                                else:
                                    print(f"   ✅ Форма исчезла - заявка подтверждена")
                            except:
                                print(f"   ✅ Форма исчезла - заявка подтверждена")
                    except:
                        pass
                    
                    print(f"   ✅ JavaScript выполнен")
                except PlaywrightTimeoutError:
                    print(f"   ⚠️ Таймаут выполнения JS (возможно выполняется асинхронно)")
                except Exception as e:
                    error_msg = str(e)[:200]
                    if "Invalid or unexpected token" in error_msg:
                        print(f"   ⚠️ Синтаксическая ошибка в JS")
                        print(f"   🔍 JS код (первые 300 символов): {js_code[:300]}")
                    else:
                        print(f"   ⚠️ Ошибка выполнения JS: {error_msg}")
            else:
                print(f"   ℹ️ JavaScript в описании не найден")
            
            print(f"   ✅ Просмотрена заявка #{request_id}")
            self.seen_requests.add(request_id)
        except Exception as e:
            print(f"   ❌ Ошибка просмотра #{request_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # --------- Основной цикл ----------
    def run_cycle(self):
        if not self.logged_in:
            if not self.login():
                print("⏸️ Пропуск цикла: нет авторизации")
                return
        
        ids = self.get_pending_requests()
        if not ids:
            print("📭 Нет новых заявок")
            return

        print(f"📋 Новых заявок: {len(ids)} -> {', '.join(ids)}")
        for rid in ids:
            self.view_request(rid)
            time.sleep(0.3)  # Пауза между заявками
    
    def run(self):
        print("🤖 Бот оператора 2 (Playwright) запущен")
        print(f"   Базовый URL: {BASE_URL}, интервал: {INTERVAL} сек")

        self.wait_for_app()

        try:
            while True:
                try:
                    self.run_cycle()
                except KeyboardInterrupt:
                    print("\n🛑 Остановка бота пользователем")
                    break
                except Exception as e:
                    print(f"❌ Критическая ошибка цикла: {e}")
                    self.logged_in = False
                time.sleep(INTERVAL)
        finally:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("🔒 Playwright закрыт")


if __name__ == "__main__":
    Operator2Bot().run()
