#!/usr/bin/env python3
"""Создание/обновление тестовой заявки для XSS-проверки"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from dbo.models import ServiceRequest, Client
from django.db import connection
from decimal import Decimal

# Константы для тестовой заявки
# Выглядит как обычная заявка, идентифицируется по слову "Тест" в начале названия
TEST_SERVICE_NAME = 'Тестирование безопасности сети'
TEST_DESCRIPTION = 'Проведение комплексного аудита безопасности корпоративной сети и веб-приложений <b>●</b>'
TEST_PRICE = Decimal('15000.00')  # Обычная цена

def create_or_update_test_request():
    """Создаёт или обновляет тестовую заявку с ID=1"""
    print("=" * 70)
    print("🧪 СОЗДАНИЕ СЛУЖЕБНОЙ ЗАЯВКИ ДЛЯ АВТОМАТИЧЕСКОЙ ПРОВЕРКИ")
    print("=" * 70)
    
    # Берём первого активного клиента (или создаём, если нет)
    client = Client.objects.filter(is_active=True).first()
    
    if not client:
        print("⚠️  Нет активных клиентов!")
        print("💡 Создаём временного клиента для тестовой заявки...")
        
        # Создаём пользователя
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            username='client1',
            defaults={
                'email': 'client1@financepro.ru',
                'first_name': 'Петр',
                'last_name': 'Иванов'
            }
        )
        if created:
            user.set_password('1q2w#E$R')
            user.save()
            print("   ✓ Создан пользователь client1")
        
        # Создаём клиента (без оператора, т.к. его тоже может не быть)
        client, created = Client.objects.get_or_create(
            user=user,
            defaults={
                'client_id': 'CLI001',
                'full_name': 'Петр Иванов',
                'email': 'client1@financepro.ru',
                'phone': '79991234567',
                'is_active': True
            }
        )
        if created:
            print("   ✓ Создан клиент CLI001")
    
    print(f"✅ Клиент: {client.full_name} ({client.email})")
    
    # Попытки создать заявку с ID=1 (максимум 3 попытки)
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\n{'🔄 ПОПЫТКА #' + str(attempt) if attempt > 1 else '📊 Текущее состояние'}")
        
        # Проверяем текущее состояние таблицы заявок
        all_requests = ServiceRequest.objects.all()
        requests_count = all_requests.count()
        
        print(f"   Заявок в БД: {requests_count}")
        
        # Удаляем ВСЕ заявки для гарантии
        if requests_count > 0:
            print(f"   🗑️  Удаляю все существующие заявки...")
            ServiceRequest.objects.all().delete()
        
        # СБРОС SEQUENCE для гарантии ID=1
        print(f"   🔄 Сброс sequence для ServiceRequest...")
        with connection.cursor() as cursor:
            # Находим имя sequence для таблицы dbo_servicerequest
            cursor.execute("""
                SELECT pg_get_serial_sequence('dbo_servicerequest', 'id');
            """)
            sequence_name = cursor.fetchone()[0]
            
            if sequence_name:
                # Сбрасываем sequence на 1
                cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1;")
                print(f"   ✓ Sequence сброшен: {sequence_name}")
            else:
                print(f"   ⚠️  Sequence не найден")
        
        # Создаём новую служебную заявку (должна получить ID=1)
        print(f"   📝 Создание тестовой заявки...")
        test_req = ServiceRequest.objects.create(
            client=client,
            service_name=TEST_SERVICE_NAME,
            service_description=TEST_DESCRIPTION,
            price=TEST_PRICE,
            status='pending'
        )
        
        # ПРОВЕРКА: ID должен быть 1
        if test_req.id == 1:
            # УСПЕХ! ID = 1
            break
        else:
            # ID != 1, удаляем и пробуем снова
            print(f"   ⚠️  ID заявки = {test_req.id}, ожидалось 1")
            if attempt < max_attempts:
                print(f"   🔄 Перезапуск создания...")
                test_req.delete()
            else:
                print(f"\n❌ ОШИБКА: Не удалось создать заявку с ID=1 за {max_attempts} попытки!")
                print(f"   💡 Попробуйте полностью перезапустить систему: bash restart.sh")
                return False
    
    # Финальная проверка
    if test_req.id != 1:
        print(f"\n❌ ОШИБКА: ID заявки = {test_req.id}, ожидалось 1!")
        print(f"   💡 Попробуйте полностью перезапустить систему: bash restart.sh")
        return False
    
    print(f"\n✅ СОЗДАНА СЛУЖЕБНАЯ ЗАЯВКА С ID=1:")
    print("-" * 70)
    print(f"   ⭐ ID: {test_req.id} {'✓ ПЕРВАЯ!' if test_req.id == 1 else '⚠️ НЕ 1!'}")
    print(f"   Название: {test_req.service_name}")
    print(f"   Описание: {test_req.service_description[:60]}...")
    print(f"   Цена: {test_req.price} ₽")
    print(f"   Статус: {test_req.status}")
    print(f"   🔍 Маркер: название начинается с 'Тестирование'")
    print(f"   Клиент: {test_req.client.full_name}")
    print(f"   Email: {test_req.client.email}")
    print("-" * 70)
    
    print("\n📋 ВАЖНАЯ ИНФОРМАЦИЯ:")
    print("   ✓ Заявка выглядит как обычная услуга тестирования")
    print("   ✓ Идентифицируется по слову 'Тестирование' в начале названия")
    print("   ✓ Содержит XSS-маркер <b>●</b> в описании")
    print(f"   ✓ URL проверки: http://10.18.2.7:8000/review-services/{test_req.id}/")
    
    print("\n🔬 ПРОВЕРКА XSS:")
    print("   Запустите: python3 check_xss.py")
    
    print("\n" + "=" * 70)
    print(f"✅ ГОТОВО! Тестовая заявка {'ПЕРВАЯ (ID=1)' if test_req.id == 1 else f'создана с ID={test_req.id}'}")
    print("=" * 70)
    
    return True

if __name__ == '__main__':
    create_or_update_test_request()
