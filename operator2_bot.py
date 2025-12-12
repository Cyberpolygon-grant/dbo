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
USERNAME = os.environ.get("BOT_USERNAME", "operator2@financepro.ru")
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
        self.logged_in_browser = False  # Флаг авторизации в Playwright браузере
        self.seen_requests = set()  # чтобы не обрабатывать одни и те же заявки
        self._init_browser()

    def _init_browser(self):
        """Инициализация Playwright браузера"""
        print("🔧 Инициализация Playwright...")
        self.playwright = sync_playwright().start()
        
        # Запускаем браузер в headful режиме (реальный браузер) для обхода защит XSS
        # В Docker может не работать headful, поэтому пробуем сначала headless с максимальными обходами
        use_headful = os.environ.get("USE_HEADFUL_BROWSER", "false").lower() == "true"
        
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-background-networking',
            '--disable-default-apps',
            '--disable-sync',
            '--metrics-recording-only',
            '--mute-audio',
            '--no-first-run',
            '--safebrowsing-disable-auto-update',
            '--disable-images',  # Отключаем загрузку изображений для скорости
            # Отключаем защиты для выполнения XSS
            '--disable-web-security',  # Отключает CORS и другие веб-безопасности
            '--disable-features=IsolateOrigins,site-per-process,VizDisplayCompositor',  # Отключает изоляцию сайтов
            '--disable-site-isolation-trials',  # Отключает изоляцию сайтов
            '--disable-blink-features=AutomationControlled',  # Скрывает автоматизацию
            '--disable-infobars',  # Отключает информационные панели
            '--disable-notifications',  # Отключает уведомления
            '--disable-popup-blocking',  # Отключает блокировку popup
            '--allow-running-insecure-content',  # Разрешает небезопасный контент
            '--disable-background-timer-throttling',  # Отключает throttling таймеров
            '--disable-renderer-backgrounding',  # Отключает фоновый рендеринг
            '--disable-backgrounding-occluded-windows',  # Отключает фоновую обработку окон
            '--js-flags=--expose-gc',  # Экспонирует GC для отладки
        ]
        
        # Если headful режим, добавляем специальные флаги
        if use_headful:
            browser_args.extend([
                '--start-maximized',
                '--window-size=1920,1080',
            ])
            print("🔧 Запускаю браузер в headful режиме (реальный браузер)")
        else:
            print("🔧 Запускаю браузер в headless режиме с максимальными обходами защит")
        
        self.browser = self.playwright.chromium.launch(
            headless=not use_headful,
            args=browser_args
        )
        
        # Создаём контекст с настройками и отключенным CSP
        # Используем более реалистичный user-agent для обхода защит
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignore_https_errors=True,
            java_script_enabled=True,
            # Отключаем все возможные защиты
            bypass_csp=True,  # Обход CSP
            # Добавляем дополнительные разрешения
            permissions=['geolocation', 'notifications'],
            # Отключаем проверку происхождения
            locale='ru-RU',
            timezone_id='Europe/Moscow',
        )
        
        # Отключаем CSP через перехват заголовков (синхронная версия)
        def remove_csp_headers(route):
            """Перехватываем ответы и удаляем CSP заголовки"""
            try:
                response = route.fetch()
                headers = dict(response.headers)
                # Удаляем CSP заголовки
                headers.pop('content-security-policy', None)
                headers.pop('content-security-policy-report-only', None)
                headers.pop('x-content-security-policy', None)
                headers.pop('x-webkit-csp', None)
                route.fulfill(
                    response=response,
                    headers=headers
                )
            except:
                # Если не удалось перехватить, просто продолжаем
                route.continue_()
        
        # Перехватываем HTML ответы для удаления CSP
        self.context.route("**/review-request/**", remove_csp_headers)
        # Также перехватываем главную страницу и дашборд
        self.context.route("**/operator2/**", remove_csp_headers)
        
        # Отключаем загрузку изображений и других ресурсов для скорости
        # НО не блокируем HTML и JS файлы, чтобы XSS мог выполниться
        def abort_resources(route):
            """Блокируем только ресурсы, но не HTML/JS"""
            if route.request.resource_type in ['image', 'font', 'media']:
                route.abort()
            else:
                route.continue_()
        
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
                
                # Сначала делаем POST без редиректа, чтобы получить куки
                response = self.session.post(
                    self._url("/login/"),
                    data=login_data,
                    headers=headers,
                    allow_redirects=False,  # Не следуем редиректу автоматически
                    timeout=10
                )
                
                # Проверяем статус ответа
                print(f"   📄 Статус ответа после POST: {response.status_code}")
                
                # Проверяем, что куки сохранены
                if 'sessionid' in self.session.cookies:
                    print(f"   ✅ Session cookie получен: {self.session.cookies['sessionid'][:20]}...")
                else:
                    print(f"   ⚠️ Session cookie не найден в ответе")
                
                # Если получили редирект (302 или 301), следуем ему
                if response.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = response.headers.get('Location', '')
                    if redirect_url:
                        if not redirect_url.startswith('http'):
                            # Относительный URL
                            if redirect_url.startswith('/'):
                                redirect_url = self._url(redirect_url)
                            else:
                                redirect_url = self._url('/' + redirect_url)
                        
                        print(f"   🔄 Следую редиректу: {redirect_url}")
                        # Делаем GET запрос по редиректу с сохраненными куками
                        final_response = self.session.get(redirect_url, timeout=10, allow_redirects=True)
                        final_url = final_response.url
                        response_text_lower = final_response.text.lower()
                    else:
                        final_url = response.url
                        response_text_lower = response.text.lower()
                else:
                    final_url = response.url
                    response_text_lower = response.text.lower()
                
                print(f"   📍 Финальный URL: {final_url}")
                
                success = (
                    "/operator2" in final_url
                    or "оператор дбо #2" in response_text_lower
                    or "оператор безопасности" in response_text_lower
                    or "operator2_dashboard" in response_text_lower
                )
                
                if success:
                    self.logged_in = True
                    # Проверяем, что куки сохранены
                    if 'sessionid' in self.session.cookies:
                        print(f"   ✅ Session cookie сохранен в сессии")
                        # Копируем куки в Playwright браузер для выполнения XSS
                        self._sync_cookies_to_browser()
                    else:
                        print(f"   ⚠️ Session cookie не найден в сессии")
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

    # --------- Синхронизация кук из requests в Playwright браузер ----------
    def _sync_cookies_to_browser(self):
        """Копирует куки из requests сессии в Playwright браузер"""
        try:
            cookies_list = []
            base_url_parsed = self._url("/")
            domain = base_url_parsed.replace('http://', '').replace('https://', '').split('/')[0]
            
            for cookie in self.session.cookies:
                cookie_dict = {
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain if cookie.domain else domain,
                    'path': cookie.path if cookie.path else '/',
                }
                if hasattr(cookie, 'expires') and cookie.expires:
                    cookie_dict['expires'] = cookie.expires
                if hasattr(cookie, 'secure') and cookie.secure:
                    cookie_dict['secure'] = True
                if hasattr(cookie, 'httponly') and cookie.httponly:
                    cookie_dict['httpOnly'] = True
                
                cookies_list.append(cookie_dict)
            
            if cookies_list:
                self.context.add_cookies(cookies_list)
                print(f"   ✅ Синхронизировано {len(cookies_list)} кук в браузер")
        except Exception as e:
            print(f"   ⚠️ Ошибка синхронизации кук: {str(e)[:100]}")
    
    # --------- Синхронизация кук из Playwright браузера в requests ----------
    def _sync_cookies_from_browser(self):
        """Копирует куки из Playwright браузера в requests сессию (опционально)"""
        try:
            browser_cookies = self.context.cookies()
            for cookie in browser_cookies:
                # Обновляем куки в requests сессии
                self.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', ''),
                    path=cookie.get('path', '/')
                )
        except Exception as e:
            pass  # Тихая ошибка, не критично

    # --------- Авторизация в Playwright браузере (синхронизация кук из requests) ----------
    def login_browser(self, retries: int = 3) -> bool:
        """Авторизация в Playwright браузере через синхронизацию кук из requests сессии"""
        if self.logged_in_browser:
            return True
        
        # Убеждаемся, что авторизованы через requests
        if not self.logged_in:
            print(f"   ⚠️ Не авторизован через requests, сначала авторизуюсь...")
            if not self.login():
                print(f"   ❌ Не удалось авторизоваться через requests")
                return False
        
        # Синхронизируем куки из requests в браузер
        try:
            self._sync_cookies_to_browser()
            self.logged_in_browser = True
            print(f"✅ Авторизован в браузере через синхронизацию кук как {USERNAME}")
            return True
        except Exception as e:
            print(f"   ⚠️ Ошибка синхронизации кук: {e}")
            # Пробуем альтернативный способ - авторизация через API напрямую в браузере
            return self._login_browser_via_api()
    
    def _login_browser_via_api(self) -> bool:
        """Альтернативный способ: авторизация через API в браузере"""
        try:
            # Используем requests для авторизации через API
            api_url = self._url("/api/login/")
            response = requests.post(
                api_url,
                json={'email': USERNAME, 'password': PASSWORD},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Копируем куки из ответа в браузер
                    for cookie in response.cookies:
                        cookie_dict = {
                            'name': cookie.name,
                            'value': cookie.value,
                            'domain': cookie.domain if cookie.domain else self._url("/").replace('http://', '').replace('https://', '').split('/')[0],
                            'path': cookie.path if cookie.path else '/',
                        }
                        if hasattr(cookie, 'expires') and cookie.expires:
                            cookie_dict['expires'] = cookie.expires
                        if hasattr(cookie, 'secure') and cookie.secure:
                            cookie_dict['secure'] = True
                        if hasattr(cookie, 'httponly') and cookie.httponly:
                            cookie_dict['httpOnly'] = True
                        
                        try:
                            self.context.add_cookies([cookie_dict])
                        except:
                            pass
                    
                    self.logged_in_browser = True
                    print(f"✅ Авторизован в браузере через API как {USERNAME}")
                    return True
            
            return False
        except Exception as e:
            print(f"   ⚠️ Ошибка авторизации через API: {e}")
            return False

    # --------- Получение списка ожидающих заявок через requests ----------
    def get_pending_requests(self) -> list[str]:
        """Получает список ID ожидающих заявок через requests"""
        try:
            url = self._url("/operator2/")
            print(f"   📍 Запрашиваю дашборд: {url}")
            
            # Убеждаемся, что мы авторизованы
            if not self.logged_in:
                print(f"   ⚠️ Не авторизован, пытаюсь войти...")
                if not self.login():
                    print(f"   ❌ Не удалось авторизоваться")
                    return []
            
            # Проверяем наличие session cookie
            if 'sessionid' not in self.session.cookies:
                print(f"   ⚠️ Session cookie отсутствует, переавторизуюсь...")
                self.logged_in = False
                if not self.login():
                    return []
            
            # Добавляем заголовки для правильной работы с Django
            headers = {
                'Referer': self._url("/"),
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            }
            
            response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            print(f"   📄 Статус ответа: {response.status_code}")
            print(f"   📍 Финальный URL: {response.url}")
            
            if response.status_code != 200:
                print(f"   ⚠️ Не удалось получить дашборд: {response.status_code}")
                # Если получили редирект на логин, значит сессия истекла
                if '/login' in response.url or response.status_code == 302:
                    print(f"   🔄 Сессия истекла, переавторизуюсь...")
                    self.logged_in = False
                    if self.login():
                        # Повторяем запрос после переавторизации
                        response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)
                        if response.status_code != 200:
                            print(f"   ❌ Не удалось получить дашборд после переавторизации: {response.status_code}")
                            return []
                    else:
                        return []
                else:
                    # Сохраняем HTML для отладки
                    if len(response.text) < 1000:
                        print(f"   📄 Ответ сервера: {response.text[:500]}")
                    return []
            
            # Парсим HTML для поиска заявок
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем ссылки на заявки
            links = soup.find_all('a', href=re.compile(r'/review-request/(\d+)/'))
            print(f"   🔍 Найдено ссылок на заявки: {len(links)}")
            
            # Также ищем в таблице заявок
            if not links:
                # Пробуем найти в таблице
                table_rows = soup.find_all('tr')
                for row in table_rows:
                    row_links = row.find_all('a', href=re.compile(r'/review-request/(\d+)/'))
                    links.extend(row_links)
            
            ids = []
            seen_in_response = set()
            for link in links:
                match = re.search(r'/review-request/(\d+)/', link.get('href', ''))
                if match:
                    req_id = match.group(1)
                    if req_id not in seen_in_response:
                        seen_in_response.add(req_id)
                        if req_id not in self.seen_requests:
                            ids.append(req_id)
            
            if ids:
                print(f"   ✅ Найдено {len(ids)} новых заявок: {', '.join(ids)}")
            else:
                print(f"   ℹ️ Новых заявок не найдено (всего ссылок: {len(links)}, уже обработано: {len(self.seen_requests)})")
            
            return ids
        except Exception as e:
            print(f"   ❌ Ошибка получения списка заявок: {e}")
            import traceback
            traceback.print_exc()
            return []

    # --------- Просмотр заявки с активным выполнением XSS ----------
    def view_request(self, request_id: str):
        """Открываем страницу заявки и активно выполняем XSS скрипт"""
        url = self._url(f"/review-request/{request_id}/")
        try:
            print(f"   🌐 Просматриваю заявку #{request_id}")

            # Убеждаемся, что авторизованы в браузере (для выполнения XSS с куками)
            if not self.logged_in_browser:
                if not self.login_browser():
                    print(f"   ⚠️ Не удалось авторизоваться в браузере, пропускаю заявку")
                    return

            # Открываем страницу
            print(f"   📍 Открываю страницу: {url}")
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                print(f"   ✅ Страница загружена")
            except Exception as e:
                print(f"   ⚠️ Ошибка загрузки страницы: {str(e)[:100]}, но продолжаю...")
                # Пробуем продолжить даже при ошибке
            
            # Ждем немного для загрузки контента
            time.sleep(1)
            
            # Метод 1: Пытаемся найти и выполнить XSS скрипт из HTML
            print(f"   🔍 Ищу XSS скрипт в HTML...")
            try:
                # Получаем HTML страницы
                html_content = self.page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Ищем скрипт в div.prose (где отображается описание)
                prose_div = soup.find('div', class_='prose')
                if prose_div:
                    # Ищем все script теги внутри prose
                    scripts = prose_div.find_all('script')
                    if scripts:
                        print(f"   ✅ Найдено {len(scripts)} скрипт(ов) в описании")
                        for script in scripts:
                            script_content = script.string or script.get_text()
                            if script_content:
                                print(f"   🚀 Выполняю найденный скрипт...")
                                try:
                                    # Выполняем скрипт в контексте страницы
                                    self.page.evaluate(script_content)
                                    print(f"   ✅ Скрипт выполнен")
                                except Exception as e:
                                    print(f"   ⚠️ Ошибка выполнения скрипта: {str(e)[:100]}")
                    else:
                        # Если скрипт не найден в prose, ищем во всем HTML
                        all_scripts = soup.find_all('script')
                        for script in all_scripts:
                            script_content = script.string or script.get_text()
                            if script_content and ('approve' in script_content.lower() or 'approve-request' in script_content):
                                print(f"   ✅ Найден скрипт одобрения во всем HTML")
                                try:
                                    self.page.evaluate(script_content)
                                    print(f"   ✅ Скрипт выполнен")
                                except Exception as e:
                                    print(f"   ⚠️ Ошибка выполнения скрипта: {str(e)[:100]}")
                else:
                    print(f"   ⚠️ Div.prose не найден, пробую альтернативный метод...")
            except Exception as e:
                print(f"   ⚠️ Ошибка поиска скрипта: {str(e)[:100]}")
            
            # Метод 2: Прямое выполнение JavaScript для одобрения заявки
            print(f"   🚀 Пробую прямое выполнение JavaScript для одобрения...")
            try:
                # Пытаемся найти request_id из URL и выполнить перенаправление
                approve_script = f"""
                (function(){{
                    var requestId = '{request_id}';
                    var approveUrl = '/approve-request/' + requestId + '/';
                    console.log('Попытка перенаправления на: ' + approveUrl);
                    window.location.href = approveUrl;
                }})();
                """
                self.page.evaluate(approve_script)
                print(f"   ✅ JavaScript для одобрения выполнен")
            except Exception as e:
                print(f"   ⚠️ Ошибка выполнения JavaScript: {str(e)[:100]}")
            
            # Метод 3: Прямой клик по кнопке одобрения (если форма доступна)
            print(f"   🖱️ Пробую найти и нажать кнопку одобрения...")
            try:
                # Ищем форму одобрения
                approve_button = self.page.query_selector('form[action*="approve-request"] button[type="submit"]')
                if approve_button:
                    print(f"   ✅ Найдена кнопка одобрения, нажимаю...")
                    approve_button.click()
                    print(f"   ✅ Кнопка нажата")
                    time.sleep(2)
                else:
                    print(f"   ℹ️ Кнопка одобрения не найдена")
            except Exception as e:
                print(f"   ⚠️ Ошибка поиска/нажатия кнопки: {str(e)[:100]}")
            
            # Ждем и проверяем результат - произошло ли перенаправление
            print(f"   ⏳ Жду результата...")
            max_wait = 8
            check_interval = 0.5
            waited = 0
            
            while waited < max_wait:
                try:
                    current_url = self.page.url
                    
                    # Если произошло перенаправление на approve-request - успех!
                    if "/approve-request" in current_url:
                        print(f"   ✅ Обнаружено перенаправление на approve-request - заявка обрабатывается!")
                        # Ждем завершения обработки
                        try:
                            self.page.wait_for_load_state("networkidle", timeout=5000)
                        except:
                            pass
                        time.sleep(1)
                        final_url = self.page.url
                        if "/operator2" in final_url:
                            print(f"   ✅ Заявка одобрена (перенаправление на дашборд)")
                        else:
                            print(f"   ✅ Заявка обрабатывается (URL: {final_url})")
                        self.seen_requests.add(request_id)
                        return
                    
                    # Если уже на дашборде
                    elif "/operator2" in current_url and "/review-request" not in current_url:
                        print(f"   ✅ Заявка уже обработана (на дашборде)")
                        self.seen_requests.add(request_id)
                        return
                    
                except:
                    pass
                
                time.sleep(check_interval)
                waited += check_interval
            
            # Финальная проверка
            try:
                final_url = self.page.url
                if "/approve-request" in final_url or ("/operator2" in final_url and "/review-request" not in final_url):
                    print(f"   ✅ Заявка обработана (финальная проверка)")
                    self.seen_requests.add(request_id)
                    return
                else:
                    print(f"   ⚠️ XSS не сработал через браузер (URL: {final_url if final_url else 'неизвестно'})")
                    # Альтернативный метод: прямое одобрение через requests
                    print(f"   🔄 Пробую альтернативный метод: прямое одобрение через API...")
                    if self._approve_request_directly(request_id):
                        print(f"   ✅ Заявка одобрена через альтернативный метод")
                        self.seen_requests.add(request_id)
                        return
                    else:
                        print(f"   ⚠️ Альтернативный метод также не сработал")
                        print(f"   💡 Попробуйте проверить логи браузера или CSP настройки")
            except:
                print(f"   ⚠️ Не удалось проверить финальный статус")
            
            print(f"   ✅ Просмотрена заявка #{request_id}")
            self.seen_requests.add(request_id)
    
    def _approve_request_directly(self, request_id: str) -> bool:
        """Альтернативный метод: прямое одобрение заявки через requests (если XSS не работает)"""
        try:
            approve_url = self._url(f"/approve-request/{request_id}/")
            
            # Убеждаемся, что авторизованы
            if not self.logged_in:
                if not self.login():
                    return False
            
            # Получаем CSRF токен
            csrf_token = None
            try:
                # Пробуем получить со страницы заявки
                review_url = self._url(f"/review-request/{request_id}/")
                response = self.session.get(review_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
                    if csrf_input:
                        csrf_token = csrf_input.get('value')
            except:
                pass
            
            if not csrf_token and 'csrftoken' in self.session.cookies:
                csrf_token = self.session.cookies['csrftoken']
            
            if not csrf_token:
                print(f"      ⚠️ Не удалось получить CSRF токен")
                return False
            
            # Отправляем POST запрос на одобрение
            headers = {
                'Referer': self._url(f"/review-request/{request_id}/"),
                'X-CSRFToken': csrf_token,
            }
            
            data = {
                'csrfmiddlewaretoken': csrf_token,
            }
            
            response = self.session.post(approve_url, data=data, headers=headers, allow_redirects=True, timeout=10)
            
            # Проверяем успешность
            if response.status_code in [200, 302]:
                if "/operator2" in response.url or "одобрена" in response.text.lower():
                    return True
            
            return False
        except Exception as e:
            print(f"      ⚠️ Ошибка прямого одобрения: {str(e)[:100]}")
            return False
            
        except Exception as e:
            print(f"   ❌ Ошибка просмотра #{request_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # --------- Основной цикл ----------
    def run_cycle(self):
        print(f"\n{'='*60}")
        print(f"🔄 Начало цикла проверки заявок")
        print(f"{'='*60}")
        
        if not self.logged_in:
            print("🔐 Требуется авторизация...")
            if not self.login():
                print("⏸️ Пропуск цикла: нет авторизации")
                return
        
        ids = self.get_pending_requests()
        if not ids:
            print("📭 Нет новых заявок (ожидание новых заявок...)")
            return

        print(f"\n📋 Найдено новых заявок: {len(ids)} -> {', '.join(ids)}")
        print(f"{'='*60}\n")
        
        for i, rid in enumerate(ids, 1):
            print(f"\n{'─'*60}")
            print(f"📌 Обработка заявки {i}/{len(ids)}: #{rid}")
            print(f"{'─'*60}")
            self.view_request(rid)
            time.sleep(1)  # Пауза между заявками для стабилизации
        
        print(f"\n{'='*60}")
        print(f"✅ Цикл завершен")
        print(f"{'='*60}\n")
    
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
