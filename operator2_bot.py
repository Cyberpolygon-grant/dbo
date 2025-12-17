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
PASSWORD = os.environ.get("BOT_PASSWORD", "1q2w#E$R%T")
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
            # Извлекаем домен из URL (например, app:8000 или localhost:8000)
            domain = base_url_parsed.replace('http://', '').replace('https://', '').split('/')[0]
            print(f"   🔧 Синхронизация кук для домена: {domain}")
            
            for cookie in self.session.cookies:
                cookie_dict = {
                    'name': cookie.name,
                    'value': cookie.value,
                    # Используем домен из cookie, если есть, иначе из URL
                    'domain': cookie.domain if cookie.domain else domain,
                    'path': cookie.path if cookie.path else '/',
                }
                
                # Для localhost и IP адресов domain должен быть пустым или точным
                if domain.startswith('localhost') or domain.startswith('127.0.0.1') or ':' in domain:
                    # Для localhost и портов не указываем domain (или используем точный)
                    cookie_dict['domain'] = domain.split(':')[0] if ':' in domain else domain
                
                if hasattr(cookie, 'expires') and cookie.expires:
                    cookie_dict['expires'] = cookie.expires
                if hasattr(cookie, 'secure') and cookie.secure:
                    cookie_dict['secure'] = True
                if hasattr(cookie, 'httponly') and cookie.httponly:
                    cookie_dict['httpOnly'] = True
                
                print(f"   🔧 Добавляю cookie: {cookie.name} = {cookie.value[:20]}..., domain={cookie_dict.get('domain')}, path={cookie_dict.get('path')}")
                cookies_list.append(cookie_dict)
            
            if cookies_list:
                # Очищаем старые куки и добавляем новые
                try:
                    self.context.clear_cookies()
                except:
                    pass
                self.context.add_cookies(cookies_list)
                print(f"   ✅ Синхронизировано {len(cookies_list)} кук в браузер")
                
                # Проверяем, что куки действительно добавлены
                check_cookies = self.context.cookies()
                print(f"   🔍 Проверка: кук в браузере после синхронизации: {len(check_cookies)}")
                for c in check_cookies:
                    if c.get('name') == 'sessionid':
                        print(f"   ✅ Session cookie в браузере: {c.get('value', '')[:20]}..., domain={c.get('domain')}, path={c.get('path')}")
            else:
                print(f"   ⚠️ Нет кук для синхронизации")
        except Exception as e:
            print(f"   ⚠️ Ошибка синхронизации кук: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
    
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

    # --------- Просмотр заявки оператором ----------
    def view_request(self, request_id: str):
        """Оператор открывает страницу заявки и переходит по ссылке в описании, если она есть"""
        url = self._url(f"/review-request/{request_id}/")
        try:
            print(f"   🌐 Просматриваю заявку #{request_id}")
            print(f"   📍 URL: {url}")

            # Убеждаемся, что авторизованы в браузере
            if not self.logged_in_browser:
                print(f"   🔐 Требуется авторизация в браузере...")
                if not self.login_browser():
                    print(f"   ⚠️ Не удалось авторизоваться в браузере, пропускаю заявку")
                    return
                print(f"   ✅ Авторизован в браузере")
            
            # Проверяем и синхронизируем куки в браузере
            browser_cookies = self.context.cookies()
            print(f"   🍪 Кук в браузере: {len(browser_cookies)}")
            session_cookie = [c for c in browser_cookies if c.get('name') == 'sessionid']
            
            # Проверяем куки в requests сессии
            requests_session_cookie = self.session.cookies.get('sessionid') if 'sessionid' in self.session.cookies else None
            print(f"   🍪 Session cookie в requests: {requests_session_cookie[:20] if requests_session_cookie else 'НЕТ'}...")
            
            if session_cookie:
                browser_session_value = session_cookie[0].get('value', '')
                print(f"   ✅ Session cookie найден в браузере: {browser_session_value[:20]}...")
                # Проверяем, совпадают ли куки
                if requests_session_cookie and browser_session_value != requests_session_cookie:
                    print(f"   ⚠️ Куки не совпадают! Синхронизирую...")
                    self._sync_cookies_to_browser()
            else:
                print(f"   ⚠️ Session cookie не найден в браузере, синхронизирую...")
                self._sync_cookies_to_browser()
            
            # Повторно проверяем куки после синхронизации
            browser_cookies = self.context.cookies()
            session_cookie = [c for c in browser_cookies if c.get('name') == 'sessionid']
            if session_cookie:
                print(f"   ✅ После синхронизации: Session cookie в браузере: {session_cookie[0].get('value', '')[:20]}...")
            else:
                print(f"   ❌ Session cookie все еще не найден в браузере после синхронизации!")
            
            # Проверяем существование заявки через requests перед открытием в браузере
            try:
                check_url = self._url(f"/review-request/{request_id}/")
                print(f"   🔍 Проверяю существование заявки через requests: {check_url}")
                
                # Убеждаемся, что сессия активна
                if not self.logged_in:
                    print(f"   ⚠️ Сессия requests не активна, авторизуюсь...")
                    if not self.login():
                        print(f"   ❌ Не удалось авторизоваться")
                        return
                
                check_response = self.session.get(check_url, timeout=10, allow_redirects=True)
                print(f"   📄 Статус проверки: {check_response.status_code}")
                print(f"   📍 Финальный URL после проверки: {check_response.url}")
                
                if check_response.status_code == 404:
                    print(f"   ❌ Заявка #{request_id} не существует (404)")
                    print(f"   💡 Возможно, заявка была удалена или ID неправильный")
                    self.seen_requests.add(request_id)
                    return
                elif check_response.status_code == 302 or '/login' in check_response.url:
                    print(f"   ⚠️ Редирект на логин - сессия истекла, переавторизуюсь...")
                    self.logged_in = False
                    if not self.login():
                        print(f"   ❌ Не удалось переавторизоваться")
                        return
                    # Повторяем проверку
                    check_response = self.session.get(check_url, timeout=10, allow_redirects=True)
                    print(f"   📄 Статус после переавторизации: {check_response.status_code}")
                    if check_response.status_code == 404:
                        print(f"   ❌ Заявка #{request_id} не существует даже после переавторизации")
                        self.seen_requests.add(request_id)
                        return
                elif check_response.status_code != 200:
                    print(f"   ⚠️ Заявка вернула статус {check_response.status_code}")
                    print(f"   📄 Ответ сервера (первые 500 символов): {check_response.text[:500]}")
            except Exception as e:
                print(f"   ⚠️ Ошибка проверки заявки: {str(e)[:100]}")
                import traceback
                traceback.print_exc()

            # Открываем страницу и ждем загрузки
            print(f"   📍 Открываю страницу в браузере: {url}")
            
            # Перед открытием страницы еще раз синхронизируем куки
            print(f"   🔄 Финальная синхронизация кук перед открытием страницы...")
            self._sync_cookies_to_browser()
            
            try:
                # Используем domcontentloaded для быстрой загрузки DOM
                # Для XSS заявок может быть таймаут, если скрипты выполняются долго
                try:
                    response = self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    status_code = response.status if response else 'N/A'
                    print(f"   ✅ Страница загружена (статус: {status_code})")
                except PlaywrightTimeoutError:
                    # Если таймаут, проверяем, может быть страница все-таки загрузилась
                    print(f"   ⚠️ Таймаут загрузки, но проверяю текущее состояние...")
                    current_url_check = self.page.url
                    if '/approve-request' in current_url_check:
                        print(f"   ✅ XSS сработал - произошел редирект на одобрение!")
                        self.seen_requests.add(request_id)
                        return
                    elif '/operator2' in current_url_check:
                        print(f"   ✅ Заявка обработана - на дашборде")
                        self.seen_requests.add(request_id)
                        return
                    else:
                        print(f"   ⚠️ Страница не загрузилась за 10 секунд, продолжаю...")
                        status_code = 'TIMEOUT'
                
                # Даем немного времени для выполнения JavaScript
                time.sleep(1)
                
                # Проверяем текущий URL - возможно был редирект
                current_url_after_load = self.page.url
                if current_url_after_load != url:
                    print(f"   ⚠️ Произошел редирект: {url} -> {current_url_after_load}")
                    if '/approve-request' in current_url_after_load:
                        print(f"   ✅ XSS сработал - произошел редирект на одобрение!")
                        self.seen_requests.add(request_id)
                        return
                    elif '/operator2' in current_url_after_load and '/review-request' not in current_url_after_load:
                        print(f"   ✅ Заявка обработана - на дашборде")
                        self.seen_requests.add(request_id)
                        return
                    elif '/login' in current_url_after_load or '/accounts/login' in current_url_after_load:
                        print(f"   ❌ Редирект на страницу логина - куки не работают!")
                        # Пробуем еще раз синхронизировать и открыть
                        print(f"   🔄 Повторная синхронизация кук...")
                        self._sync_cookies_to_browser()
                        try:
                            response = self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
                            status_code = response.status if response else 'N/A'
                            print(f"   ✅ Повторная загрузка (статус: {status_code})")
                            time.sleep(1)
                            current_url_after_load = self.page.url
                            if '/login' in current_url_after_load:
                                print(f"   ❌ Все еще редирект на логин - проблема с авторизацией в браузере")
                                self.seen_requests.add(request_id)
                                return
                        except PlaywrightTimeoutError:
                            print(f"   ⚠️ Таймаут при повторной загрузке")
                
                # Проверяем статус ответа только если не было таймаута
                if status_code != 'TIMEOUT' and status_code != 200:
                    print(f"   ⚠️ Страница вернула статус {status_code}, проверяю содержимое...")
                    page_content = self.page.content()
                    print(f"   📄 HTML страницы (первые 1000 символов):")
                    print(f"      {page_content[:1000]}")
                    if status_code == 404:
                        print(f"   ❌ Заявка #{request_id} не найдена (404) - возможно, проблема с авторизацией или заявка не существует")
                        # Проверяем текущий URL - может быть редирект на логин
                        current_url = self.page.url
                        print(f"   📍 Текущий URL после загрузки: {current_url}")
                        if '/login' in current_url:
                            print(f"   ⚠️ Произошел редирект на логин - сессия истекла")
                            self.logged_in_browser = False
                        self.seen_requests.add(request_id)
                        return
                
                
                # Дополнительно ждем выполнения JavaScript
                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    pass
                
                # Даем время JavaScript скриптам настроить ссылку
                print(f"   ⏳ Жду выполнения JavaScript скриптов (1 сек)...")
                time.sleep(1)
                
                # Проверяем, не произошло ли перенаправление (XSS мог сработать)
                try:
                    current_url_before_read = self.page.url
                    if '/approve-request' in current_url_before_read:
                        print(f"   ✅ XSS сработал - уже на странице одобрения!")
                        self.seen_requests.add(request_id)
                        return
                    elif '/operator2' in current_url_before_read and '/review-request' not in current_url_before_read:
                        print(f"   ✅ Заявка обработана - уже на дашборде")
                        self.seen_requests.add(request_id)
                        return
                except:
                    pass
                
                # Имитируем чтение оператором - ждем 2-4 секунды
                import random
                read_time = random.uniform(2, 4)
                print(f"   ⏳ Оператор читает заявку ({read_time:.1f} сек)...")
                time.sleep(read_time)
                
                # Еще раз проверяем перенаправление после чтения
                try:
                    current_url_after_read = self.page.url
                    if '/approve-request' in current_url_after_read:
                        print(f"   ✅ XSS сработал во время чтения - редирект на страницу одобрения!")
                        self.seen_requests.add(request_id)
                        return
                    elif '/operator2' in current_url_after_read and '/review-request' not in current_url_after_read:
                        print(f"   ✅ Заявка обработана во время чтения - на дашборде")
                        self.seen_requests.add(request_id)
                        return
                except:
                    pass
                
                # Проверяем, не произошло ли уже перенаправление на страницу одобрения
                try:
                    current_url_check = self.page.url
                    print(f"   📍 Текущий URL перед проверкой описания: {current_url_check}")
                    if '/approve-request' in current_url_check:
                        print(f"   ✅ XSS сработал - произошел редирект на страницу одобрения!")
                        self.seen_requests.add(request_id)
                        return
                    elif '/operator2' in current_url_check and '/review-request' not in current_url_check:
                        print(f"   ✅ Заявка обработана - на дашборде")
                        self.seen_requests.add(request_id)
                        return
                except:
                    pass
                
                # Получаем и выводим содержимое описания для отладки
                print(f"   📄 Проверяю содержимое описания...")
                try:
                    # Сначала выводим общий HTML страницы для отладки
                    # Обрабатываем ошибку навигации - если страница перенаправляется
                    try:
                        page_html = self.page.content()
                        print(f"   📝 HTML всей страницы (первые 2000 символов):")
                        print(f"      {page_html[:2000]}")
                    except Exception as nav_error:
                        if "navigating" in str(nav_error).lower():
                            print(f"   ⚠️ Страница находится в процессе навигации (XSS скрипт перенаправляет)")
                            # Ждем завершения навигации
                            try:
                                self.page.wait_for_load_state("networkidle", timeout=5000)
                                current_url_after_nav = self.page.url
                                print(f"   📍 URL после навигации: {current_url_after_nav}")
                                if '/approve-request' in current_url_after_nav:
                                    print(f"   ✅ XSS сработал - редирект на страницу одобрения!")
                                    self.seen_requests.add(request_id)
                                    return
                                elif '/operator2' in current_url_after_nav:
                                    print(f"   ✅ Заявка обработана - на дашборде")
                                    self.seen_requests.add(request_id)
                                    return
                            except:
                                # Если не удалось дождаться, просто проверяем текущий URL
                                try:
                                    current_url_after_nav = self.page.url
                                    if '/approve-request' in current_url_after_nav or '/operator2' in current_url_after_nav:
                                        print(f"   ✅ Произошел редирект: {current_url_after_nav}")
                                        self.seen_requests.add(request_id)
                                        return
                                except:
                                    pass
                            print(f"   ⚠️ Не удалось получить содержимое из-за навигации, продолжаю...")
                        else:
                            raise
                    
                    # Ищем div с классом "prose dark:prose-invert max-w-none"
                    prose_div = self.page.query_selector('.prose.dark\\:prose-invert.max-w-none')
                    if not prose_div:
                        # Пробуем альтернативные варианты
                        prose_div = self.page.query_selector('div.prose')
                    if not prose_div:
                        prose_div = self.page.query_selector('.prose')
                    if prose_div:
                        prose_text = prose_div.inner_text()
                        prose_html = prose_div.inner_html()
                        print(f"   📝 Текст описания (первые 500 символов):")
                        print(f"      {prose_text[:500]}")
                        print(f"   📝 HTML описания (первые 1000 символов):")
                        print(f"      {prose_html[:1000]}")
                        
                        # Улучшенная проверка на эксплуатацию XSS
                        print(f"   🔍 Детальная проверка на XSS уязвимость...")
                        
                        # 1. Проверяем, что HTML не экранирован (признак использования |safe)
                        is_escaped = '&lt;script' in prose_html or '&lt;a' in prose_html or '&lt;img' in prose_html
                        if is_escaped:
                            print(f"   🔒 HTML экранирован (используется |escape) - XSS не активна")
                            print(f"   ✅ Оператор защищен от XSS атаки")
                            self.seen_requests.add(request_id)
                            return
                        
                        # 2. Проверяем наличие JavaScript маркеров
                        js_indicators = [
                            '<script', 
                            'javascript:', 
                            'onclick=', 
                            'onerror=', 
                            'onload=', 
                            'eval(', 
                            'function(',
                            'document.',
                            'window.location',
                            'fetch(',
                            'FormData(',
                            'addEventListener'
                        ]
                        found_js_markers = []
                        for indicator in js_indicators:
                            if indicator.lower() in prose_html.lower():
                                found_js_markers.append(indicator)
                        
                        # 3. Проверяем наличие специфичных XSS элементов
                        has_xss_elements = False
                        xss_elements = [
                            'operator-info-link',  # ID ссылки из XSS payload
                            'img src=x onerror',   # Автоматическое выполнение через img
                            'svg onload',          # Автоматическое выполнение через svg
                        ]
                        found_xss_elements = []
                        for element in xss_elements:
                            if element.lower() in prose_html.lower():
                                found_xss_elements.append(element)
                                has_xss_elements = True
                        
                        # 4. Ищем конкретную ссылку с id="operator-info-link"
                        operator_info_link = prose_div.query_selector('a#operator-info-link')
                        
                        # 5. Проверяем наличие текста "ознакомиться"
                        has_operator_text = 'ознакомиться' in prose_text.lower() or 'ознакомиться' in prose_html.lower()
                        
                        # Выводим результаты проверки
                        print(f"   📊 Результаты проверки XSS:")
                        print(f"      - HTML экранирован: ❌ НЕТ (уязвимо)")
                        print(f"      - JavaScript маркеры: {'✅ НАЙДЕНЫ' if found_js_markers else '❌ НЕ НАЙДЕНЫ'}")
                        if found_js_markers:
                            print(f"         Найдены: {', '.join(found_js_markers[:5])}")
                        print(f"      - XSS элементы: {'✅ НАЙДЕНЫ' if found_xss_elements else '❌ НЕ НАЙДЕНЫ'}")
                        if found_xss_elements:
                            print(f"         Найдены: {', '.join(found_xss_elements)}")
                        print(f"      - Ссылка operator-info-link: {'✅ НАЙДЕНА' if operator_info_link else '❌ НЕ НАЙДЕНА'}")
                        print(f"      - Текст 'ознакомиться': {'✅ НАЙДЕН' if has_operator_text else '❌ НЕ НАЙДЕН'}")
                        
                        # Определяем, есть ли активная XSS уязвимость
                        is_xss_vulnerable = (
                            not is_escaped and  # HTML не экранирован
                            (found_js_markers or has_xss_elements) and  # Есть JS или XSS элементы
                            (operator_info_link is not None or has_operator_text)  # Есть целевая ссылка или текст
                        )
                        
                        if not is_xss_vulnerable:
                            print(f"   ⚠️ XSS уязвимость не обнаружена или не активна")
                            print(f"   ✅ Оператор просмотрел заявку")
                            self.seen_requests.add(request_id)
                            return
                        
                        print(f"   🚨 ОБНАРУЖЕНА АКТИВНАЯ XSS УЯЗВИМОСТЬ!")
                        print(f"   🔍 Ищу ссылку для перехода...")
                        
                        # Ищем все ссылки в .prose
                        all_links = prose_div.query_selector_all('a')
                        print(f"   🔍 Найдено ссылок в описании: {len(all_links)}")
                        
                        # Ищем ссылку по приоритету: сначала по ID, потом по тексту, потом по href
                        target_link = None
                        if operator_info_link:
                            target_link = operator_info_link
                            print(f"   ✅ Найдена ссылка по ID 'operator-info-link'")
                        else:
                            for link in all_links:
                                try:
                                    link_text = link.inner_text().lower().strip()
                                    link_href = link.get_attribute('href') or ''
                                    link_id = link.get_attribute('id') or ''
                                    print(f"   🔍 Проверяю ссылку: id='{link_id}', текст='{link_text[:50]}', href='{link_href[:100]}'")
                                    
                                    # Приоритет: ID > текст > href
                                    if link_id == 'operator-info-link':
                                        target_link = link
                                        print(f"   ✅ Найдена ссылка по ID!")
                                        break
                                    elif "ознакомиться" in link_text:
                                        target_link = link
                                        print(f"   ✅ Найдена ссылка по тексту 'ознакомиться'!")
                                        break
                                    elif "/approve-request" in link_href:
                                        target_link = link
                                        print(f"   ✅ Найдена ссылка по href '/approve-request'!")
                                        break
                                except Exception as e:
                                    print(f"   ⚠️ Ошибка проверки ссылки: {str(e)[:50]}")
                        
                        if not target_link:
                            print(f"   ⚠️ Целевая ссылка не найдена, но XSS обнаружен")
                            print(f"   ✅ Оператор просмотрел заявку")
                            self.seen_requests.add(request_id)
                            return
                        
                        if target_link:
                            # Получаем href ссылки
                            link_href = target_link.get_attribute('href')
                            print(f"   ✅ Найдена ссылка: href='{link_href}'")
                            print(f"   ✅ XSS уязвимость активна (используется |safe) - ссылка найдена")
                            
                            # Извлекаем request_id из href или из текущего URL
                            approve_request_id = None
                            if link_href and '/approve-request/' in link_href:
                                import re
                                match = re.search(r'/approve-request/(\d+)/', link_href)
                                if match:
                                    approve_request_id = match.group(1)
                            if not approve_request_id:
                                approve_request_id = request_id
                            
                            print(f"   📝 ID заявки для одобрения: {approve_request_id}")
                            
                            # Отправляем POST запрос напрямую через Playwright
                            print(f"   👆 Оператор переходит по ссылке (отправляется POST запрос)...")
                            try:
                                # Получаем CSRF токен из формы на странице
                                csrf_token = None
                                try:
                                    csrf_input = self.page.query_selector('input[name="csrfmiddlewaretoken"]')
                                    if csrf_input:
                                        csrf_token = csrf_input.get_attribute('value')
                                except:
                                    pass
                                
                                # Если не нашли в форме, получаем из cookie
                                if not csrf_token:
                                    cookies = self.context.cookies()
                                    for cookie in cookies:
                                        if cookie['name'] == 'csrftoken':
                                            csrf_token = cookie['value']
                                            break
                                
                                if csrf_token:
                                    print(f"   ✅ CSRF токен получен")
                                    
                                    # Отправляем POST запрос через Playwright
                                    approve_url = self._url(f"/approve-request/{approve_request_id}/")
                                    print(f"   📤 Отправка POST запроса на: {approve_url}")
                                    
                                    response = self.page.request.post(
                                        approve_url,
                                        data={'csrfmiddlewaretoken': csrf_token},
                                        headers={
                                            'Referer': self.page.url,
                                            'X-CSRFToken': csrf_token,
                                        }
                                    )
                                    
                                    print(f"   📥 Ответ получен: статус {response.status}")
                                    
                                    # Ждем навигации после POST запроса
                                    try:
                                        self.page.wait_for_url('**/operator2/**', timeout=5000)
                                        current_url = self.page.url
                                        print(f"   ✅ XSS сработал - произошло перенаправление на: {current_url}")
                                        self.seen_requests.add(request_id)
                                        return
                                    except:
                                        pass
                                    
                                    # Если редирект не произошел автоматически, переходим вручную
                                    if response.status in [200, 302]:
                                        # Перезагружаем страницу или переходим на дашборд
                                        try:
                                            self.page.goto(self._url("/operator2/"), wait_until="networkidle", timeout=5000)
                                            current_url = self.page.url
                                            print(f"   ✅ Переход на дашборд выполнен: {current_url}")
                                            self.seen_requests.add(request_id)
                                            return
                                        except:
                                            pass
                                    
                                    # Проверяем текущий URL
                                    time.sleep(1)
                                    current_url = self.page.url
                                    print(f"   📍 Текущий URL после POST: {current_url}")
                                    
                                    if '/operator2' in current_url:
                                        print(f"   ✅ XSS сработал - на дашборде!")
                                        self.seen_requests.add(request_id)
                                        return
                                else:
                                    print(f"   ⚠️ CSRF токен не найден, пробую альтернативный способ...")
                                    
                                    # Альтернативный способ - через JavaScript
                                    post_success = self.page.evaluate(f"""
                                        (function() {{
                                            var csrfToken = null;
                                            var form = document.querySelector('form[action*="approve-request"]');
                                            if(form){{
                                                var csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
                                                if(csrfInput){{
                                                    csrfToken = csrfInput.value;
                                                }}
                                            }}
                                            if(!csrfToken){{
                                                var cookies = document.cookie.split(';');
                                                for(var i=0; i<cookies.length; i++){{
                                                    var cookie = cookies[i].trim();
                                                    if(cookie.indexOf('csrftoken=') === 0){{
                                                        csrfToken = cookie.substring('csrftoken='.length);
                                                        break;
                                                    }}
                                                }}
                                            }}
                                            
                                            if(csrfToken) {{
                                                var hiddenForm = document.createElement('form');
                                                hiddenForm.method = 'POST';
                                                hiddenForm.action = '/approve-request/{approve_request_id}/';
                                                hiddenForm.style.display = 'none';
                                                
                                                var csrfInput = document.createElement('input');
                                                csrfInput.type = 'hidden';
                                                csrfInput.name = 'csrfmiddlewaretoken';
                                                csrfInput.value = csrfToken;
                                                hiddenForm.appendChild(csrfInput);
                                                
                                                document.body.appendChild(hiddenForm);
                                                hiddenForm.submit();
                                                return true;
                                            }}
                                            return false;
                                        }})();
                                    """)
                                    
                                    if post_success:
                                        print(f"   ✅ POST запрос отправлен через JavaScript")
                                        time.sleep(2)
                                        
                                        try:
                                            self.page.wait_for_url('**/operator2/**', timeout=5000)
                                            current_url = self.page.url
                                            print(f"   ✅ XSS сработал - произошло перенаправление на: {current_url}")
                                            self.seen_requests.add(request_id)
                                            return
                                        except:
                                            pass
                                        
                                        current_url = self.page.url
                                        if '/operator2' in current_url:
                                            print(f"   ✅ XSS сработал - на дашборде!")
                                            self.seen_requests.add(request_id)
                                            return
                                    
                            except Exception as click_error:
                                print(f"   ⚠️ Ошибка при выполнении POST запроса: {str(click_error)[:200]}")
                            
                            self.seen_requests.add(request_id)
                            return
                        else:
                            print(f"   ⚠️ Ссылка не найдена в описании")
                            print(f"   ✅ Оператор просмотрел заявку")
                            self.seen_requests.add(request_id)
                            return
                    else:
                        print(f"   ⚠️ Div.prose не найден на странице")
                        # Пробуем найти через XPath или другие селекторы
                        try:
                            # Ищем через XPath
                            prose_xpath = self.page.query_selector('xpath=//div[contains(@class, "prose")]')
                            if prose_xpath:
                                print(f"   ✅ Найден div.prose через XPath")
                                prose_div = prose_xpath
                                prose_text = prose_div.inner_text()
                                prose_html = prose_div.inner_html()
                                print(f"   📝 Текст описания (первые 500 символов):")
                                print(f"      {prose_text[:500]}")
                                print(f"   📝 HTML описания (первые 1000 символов):")
                                print(f"      {prose_html[:1000]}")
                                
                                # Улучшенная проверка на эксплуатацию XSS (через XPath)
                                print(f"   🔍 Детальная проверка на XSS уязвимость (XPath)...")
                                
                                # 1. Проверяем, что HTML не экранирован
                                is_escaped = '&lt;script' in prose_html or '&lt;a' in prose_html or '&lt;img' in prose_html
                                if is_escaped:
                                    print(f"   🔒 HTML экранирован (используется |escape) - XSS не активна")
                                    print(f"   ✅ Оператор защищен от XSS атаки")
                                    self.seen_requests.add(request_id)
                                    return
                                
                                # 2. Проверяем наличие JavaScript маркеров
                                js_indicators = [
                                    '<script', 
                                    'javascript:', 
                                    'onclick=', 
                                    'onerror=', 
                                    'onload=', 
                                    'eval(', 
                                    'function(',
                                    'document.',
                                    'window.location',
                                    'fetch(',
                                    'FormData(',
                                    'addEventListener'
                                ]
                                found_js_markers = []
                                for indicator in js_indicators:
                                    if indicator.lower() in prose_html.lower():
                                        found_js_markers.append(indicator)
                                
                                # 3. Проверяем наличие специфичных XSS элементов
                                has_xss_elements = False
                                xss_elements = [
                                    'operator-info-link',
                                    'img src=x onerror',
                                    'svg onload',
                                ]
                                found_xss_elements = []
                                for element in xss_elements:
                                    if element.lower() in prose_html.lower():
                                        found_xss_elements.append(element)
                                        has_xss_elements = True
                                
                                # 4. Ищем конкретную ссылку с id="operator-info-link"
                                operator_info_link = prose_div.query_selector('a#operator-info-link')
                                
                                # 5. Проверяем наличие текста "ознакомиться"
                                has_operator_text = 'ознакомиться' in prose_text.lower() or 'ознакомиться' in prose_html.lower()
                                
                                # Выводим результаты проверки
                                print(f"   📊 Результаты проверки XSS:")
                                print(f"      - HTML экранирован: ❌ НЕТ (уязвимо)")
                                print(f"      - JavaScript маркеры: {'✅ НАЙДЕНЫ' if found_js_markers else '❌ НЕ НАЙДЕНЫ'}")
                                if found_js_markers:
                                    print(f"         Найдены: {', '.join(found_js_markers[:5])}")
                                print(f"      - XSS элементы: {'✅ НАЙДЕНЫ' if found_xss_elements else '❌ НЕ НАЙДЕНЫ'}")
                                if found_xss_elements:
                                    print(f"         Найдены: {', '.join(found_xss_elements)}")
                                print(f"      - Ссылка operator-info-link: {'✅ НАЙДЕНА' if operator_info_link else '❌ НЕ НАЙДЕНА'}")
                                print(f"      - Текст 'ознакомиться': {'✅ НАЙДЕН' if has_operator_text else '❌ НЕ НАЙДЕН'}")
                                
                                # Определяем, есть ли активная XSS уязвимость
                                is_xss_vulnerable = (
                                    not is_escaped and
                                    (found_js_markers or has_xss_elements) and
                                    (operator_info_link is not None or has_operator_text)
                                )
                                
                                if not is_xss_vulnerable:
                                    print(f"   ⚠️ XSS уязвимость не обнаружена или не активна")
                                    print(f"   ✅ Оператор просмотрел заявку")
                                    self.seen_requests.add(request_id)
                                    return
                                
                                print(f"   🚨 ОБНАРУЖЕНА АКТИВНАЯ XSS УЯЗВИМОСТЬ!")
                                print(f"   🔍 Ищу ссылку для перехода...")
                                
                                # Ищем ссылки
                                all_links = prose_div.query_selector_all('a')
                                print(f"   🔍 Найдено ссылок в описании: {len(all_links)}")
                                
                                # Ищем ссылку по приоритету
                                target_link = None
                                if operator_info_link:
                                    target_link = operator_info_link
                                    print(f"   ✅ Найдена ссылка по ID 'operator-info-link'")
                                else:
                                    for link in all_links:
                                        try:
                                            link_text = link.inner_text().lower().strip()
                                            link_href = link.get_attribute('href') or ''
                                            link_id = link.get_attribute('id') or ''
                                            print(f"   🔍 Проверяю ссылку: id='{link_id}', текст='{link_text[:50]}', href='{link_href[:100]}'")
                                            
                                            if link_id == 'operator-info-link':
                                                target_link = link
                                                print(f"   ✅ Найдена ссылка по ID!")
                                                break
                                            elif "ознакомиться" in link_text:
                                                target_link = link
                                                print(f"   ✅ Найдена ссылка по тексту 'ознакомиться'!")
                                                break
                                            elif "/approve-request" in link_href:
                                                target_link = link
                                                print(f"   ✅ Найдена ссылка по href '/approve-request'!")
                                                break
                                        except Exception as e:
                                            print(f"   ⚠️ Ошибка проверки ссылки: {str(e)[:50]}")
                                
                                if not target_link:
                                    print(f"   ⚠️ Целевая ссылка не найдена, но XSS обнаружен")
                                    print(f"   ✅ Оператор просмотрел заявку")
                                    self.seen_requests.add(request_id)
                                    return
                                
                                if target_link:
                                    link_href = target_link.get_attribute('href')
                                    print(f"   ✅ Найдена ссылка: href='{link_href}'")
                                    print(f"   ✅ XSS уязвимость активна (используется |safe) - ссылка найдена")
                                    target_link.scroll_into_view_if_needed()
                                    time.sleep(0.3)
                                    print(f"   👆 Оператор кликает на ссылку (отправится POST запрос)...")
                                    try:
                                        target_link.click()
                                        print(f"   ✅ Клик выполнен, ждем обработки POST запроса...")
                                        
                                        time.sleep(2)
                                        
                                        try:
                                            self.page.wait_for_load_state("networkidle", timeout=5000)
                                        except:
                                            pass
                                        
                                        current_url = self.page.url
                                        print(f"   📍 Текущий URL после клика: {current_url}")
                                        
                                        if '/operator2' in current_url or '/approve-request' in current_url:
                                            print(f"   ✅ XSS сработал - произошло перенаправление!")
                                            self.seen_requests.add(request_id)
                                            return
                                        else:
                                            time.sleep(2)
                                            current_url = self.page.url
                                            if '/operator2' in current_url or '/approve-request' in current_url:
                                                print(f"   ✅ XSS сработал - произошло перенаправление!")
                                                self.seen_requests.add(request_id)
                                                return
                                    except Exception as click_error:
                                        print(f"   ⚠️ Ошибка при клике на ссылку: {str(click_error)[:100]}")
                                else:
                                    print(f"   ⚠️ Ссылка 'ознакомиться' не найдена в описании")
                                    print(f"   🔒 XSS уязвимость НЕ активна (используется |escape) - ссылка не найдена")
                                    print(f"   ✅ Оператор защищен от XSS атаки")
                                    self.seen_requests.add(request_id)
                                    return
                                    current_url = self.page.url
                                    print(f"   📍 Текущий URL: {current_url}")
                                    self.seen_requests.add(request_id)
                                    return
                        except Exception as e:
                            print(f"   ⚠️ Ошибка поиска через XPath: {str(e)[:50]}")
                        
                        # Ищем все ссылки на странице, если .prose не найден
                        print(f"   🔍 Ищу все ссылки на странице...")
                        all_links = self.page.query_selector_all('a')
                        print(f"   🔍 Всего ссылок на странице: {len(all_links)}")
                        for i, link in enumerate(all_links[:10]):  # Проверяем первые 10
                            try:
                                link_text = link.inner_text().lower().strip()
                                link_href = link.get_attribute('href') or ''
                                print(f"   🔍 Ссылка #{i}: текст='{link_text[:50]}', href='{link_href[:100]}'")
                            except:
                                pass
                except Exception as e:
                    print(f"   ⚠️ Ошибка при работе с описанием: {str(e)[:100]}")
                    import traceback
                    traceback.print_exc()
                
                print(f"   💡 Оператор просмотрел заявку")
                    
            except PlaywrightTimeoutError:
                print(f"   ⚠️ Таймаут загрузки страницы")
                # Проверяем, может быть страница все-таки загрузилась
                try:
                    current_url = self.page.url
                    print(f"   📍 Текущий URL после таймаута: {current_url}")
                    if '/approve-request' in current_url:
                        print(f"   ✅ XSS сработал - произошел редирект на одобрение!")
                        self.seen_requests.add(request_id)
                        return
                    elif '/operator2' in current_url:
                        print(f"   ✅ Заявка обработана - на дашборде")
                        self.seen_requests.add(request_id)
                        return
                except:
                    pass
            except Exception as e:
                print(f"   ⚠️ Ошибка загрузки страницы: {str(e)[:100]}")
                # Проверяем текущий URL даже при ошибке
                try:
                    current_url = self.page.url
                    if '/approve-request' in current_url or '/operator2' in current_url:
                        print(f"   ✅ Несмотря на ошибку, произошел редирект: {current_url}")
                        self.seen_requests.add(request_id)
                        return
                except:
                    pass
            
            # Помечаем заявку как просмотренную
            print(f"   ✅ Просмотрена заявка #{request_id}")
            self.seen_requests.add(request_id)
            
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
