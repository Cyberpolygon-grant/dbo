#!/usr/bin/env python3
"""
Бот оператора 2: автоматически просматривает заявки на создание услуг.
Симулирует действия оператора - заходит в ЛК и открывает каждую заявку.
"""
import requests
import time
import re
import os
from bs4 import BeautifulSoup

BASE_URL = os.environ.get('APP_URL', 'http://app:8000')
USERNAME = os.environ.get('BOT_USERNAME', 'operator2')
PASSWORD = os.environ.get('BOT_PASSWORD', 'operator2pass')
INTERVAL = int(os.environ.get('CHECK_INTERVAL', '30'))  # секунд между проверками

class Operator2Bot:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self):
        """Авторизация под оператором 2"""
        try:
            # Получаем CSRF токен
            resp = self.session.get(f'{BASE_URL}/login/', timeout=10)
            if resp.status_code != 200:
                print(f'❌ Ошибка получения страницы логина: статус {resp.status_code}')
                return False
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            csrf_token = csrf_input['value'] if csrf_input else ''
            
            if not csrf_token:
                print(f'❌ Не удалось получить CSRF токен')
                return False
            
            # Логинимся (allow_redirects=True для следования редиректам)
            login_data = {
                'csrfmiddlewaretoken': csrf_token,
                'email': USERNAME,
                'password': PASSWORD,
            }
            resp = self.session.post(
                f'{BASE_URL}/login/',
                data=login_data,
                headers={'Referer': f'{BASE_URL}/login/'},
                timeout=10,
                allow_redirects=True
            )
            
            # Проверяем успешность авторизации:
            # 1. Проверяем финальный URL после всех редиректов
            final_url = resp.url
            # 2. Проверяем содержимое страницы на наличие признаков дашборда оператора
            page_content = resp.text.lower()
            
            # Успешная авторизация если:
            # - URL содержит /operator2/ (редирект на дашборд)
            # - ИЛИ страница содержит признаки дашборда оператора
            # - И статус код 200
            is_success = (
                resp.status_code == 200 and
                ('/operator2/' in final_url or 
                 'operator2' in final_url or
                 'operator2_dashboard' in page_content or
                 'заявки на создание услуг' in page_content or
                 'review-request' in page_content)
            )
            
            if is_success:
                self.logged_in = True
                print(f'✅ Авторизован как {USERNAME}')
                return True
            else:
                # Дополнительная диагностика
                if '/login/' in final_url:
                    print(f'❌ Ошибка авторизации: остались на странице логина')
                    # Проверяем наличие сообщений об ошибке
                    if 'неверные' in page_content or 'ошибка' in page_content:
                        print(f'   Причина: неверные учетные данные')
                else:
                    print(f'❌ Ошибка авторизации: неожиданный URL {final_url[:100]}')
                print(f'   Статус: {resp.status_code}, URL: {final_url}')
                return False
        except requests.exceptions.RequestException as e:
            print(f'❌ Ошибка сети при авторизации: {e}')
            return False
        except Exception as e:
            print(f'❌ Ошибка авторизации: {e}')
            import traceback
            traceback.print_exc()
            return False
    
    def get_pending_requests(self):
        """Получает список заявок из дашборда оператора 2"""
        try:
            resp = self.session.get(f'{BASE_URL}/operator2/', timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Ищем ссылки на просмотр заявок
            request_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'review-request' in href:
                    match = re.search(r'/review-request/(\d+)/', href)
                    if match:
                        request_id = match.group(1)
                        request_links.append(request_id)
            
            return list(set(request_links))  # уникальные ID
        except Exception as e:
            print(f'❌ Ошибка получения заявок: {e}')
            return []
    
    def view_request(self, request_id):
        """Просматривает заявку (открывает страницу)"""
        try:
            url = f'{BASE_URL}/review-request/{request_id}/'
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                print(f'   👁️ Просмотрена заявка #{request_id}')
                return True
            else:
                print(f'   ⚠️ Заявка #{request_id}: код {resp.status_code}')
                return False
        except Exception as e:
            print(f'   ❌ Ошибка просмотра #{request_id}: {e}')
            return False
    
    def run_cycle(self):
        """Один цикл проверки заявок"""
        if not self.logged_in:
            if not self.login():
                print('⏸️ Пропуск цикла из-за ошибки авторизации')
                return
        
        try:
            request_ids = self.get_pending_requests()
            if request_ids:
                print(f'📋 Найдено заявок: {len(request_ids)}')
                for req_id in request_ids:
                    self.view_request(req_id)
                    time.sleep(1)  # пауза между просмотрами
            else:
                print('📭 Нет новых заявок')
        except requests.exceptions.RequestException as e:
            print(f'❌ Ошибка сети при получении заявок: {e}')
            self.logged_in = False  # Требуем переавторизацию
        except Exception as e:
            print(f'❌ Ошибка в цикле проверки: {e}')
            self.logged_in = False  # Требуем переавторизацию
    
    def run(self):
        """Запуск бота в бесконечном цикле"""
        print(f'🤖 Бот оператора 2 запущен')
        print(f'   URL: {BASE_URL}')
        print(f'   Интервал: {INTERVAL} сек')
        
        # Ждём пока приложение запустится
        print('⏳ Ожидание готовности приложения...')
        app_ready = False
        for attempt in range(30):
            try:
                resp = requests.get(f'{BASE_URL}/', timeout=5)
                if resp.status_code == 200:
                    print('✅ Приложение готово')
                    app_ready = True
                    break
            except Exception as e:
                if attempt % 5 == 0:  # Показываем прогресс каждые 5 попыток
                    print(f'   Попытка {attempt + 1}/30...')
            time.sleep(2)
        
        if not app_ready:
            print('⚠️ Приложение не готово после ожидания, продолжаем попытки...')
        
        # Дополнительная пауза для полной инициализации
        time.sleep(3)
        
        while True:
            try:
                self.run_cycle()
            except KeyboardInterrupt:
                print('\n🛑 Остановка бота...')
                break
            except Exception as e:
                print(f'❌ Критическая ошибка цикла: {e}')
                import traceback
                traceback.print_exc()
                self.logged_in = False  # переавторизация при ошибке
                time.sleep(5)  # Пауза перед следующей попыткой
            
            time.sleep(INTERVAL)

if __name__ == '__main__':
    bot = Operator2Bot()
    bot.run()

