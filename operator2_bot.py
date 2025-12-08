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
            soup = BeautifulSoup(resp.text, 'html.parser')
            csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            csrf_token = csrf_input['value'] if csrf_input else ''
            
            # Логинимся
            login_data = {
                'csrfmiddlewaretoken': csrf_token,
                'email': USERNAME,
                'password': PASSWORD,
            }
            resp = self.session.post(
                f'{BASE_URL}/login/',
                data=login_data,
                headers={'Referer': f'{BASE_URL}/login/'},
                timeout=10
            )
            
            if 'operator2' in resp.url or resp.status_code == 200:
                self.logged_in = True
                print(f'✅ Авторизован как {USERNAME}')
                return True
            else:
                print(f'❌ Ошибка авторизации')
                return False
        except Exception as e:
            print(f'❌ Ошибка: {e}')
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
                return
        
        request_ids = self.get_pending_requests()
        if request_ids:
            print(f'📋 Найдено заявок: {len(request_ids)}')
            for req_id in request_ids:
                self.view_request(req_id)
                time.sleep(1)  # пауза между просмотрами
        else:
            print('📭 Нет новых заявок')
    
    def run(self):
        """Запуск бота в бесконечном цикле"""
        print(f'🤖 Бот оператора 2 запущен')
        print(f'   URL: {BASE_URL}')
        print(f'   Интервал: {INTERVAL} сек')
        
        # Ждём пока приложение запустится
        print('⏳ Ожидание готовности приложения...')
        for _ in range(30):
            try:
                resp = requests.get(f'{BASE_URL}/', timeout=5)
                if resp.status_code == 200:
                    break
            except:
                pass
            time.sleep(2)
        
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                print(f'❌ Ошибка цикла: {e}')
                self.logged_in = False  # переавторизация при ошибке
            
            time.sleep(INTERVAL)

if __name__ == '__main__':
    bot = Operator2Bot()
    bot.run()

