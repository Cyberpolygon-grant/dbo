#!/usr/bin/env python3
"""Создание/обновление тестовой заявки для XSS-проверки"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from dbo.models import ServiceRequest, Client
from decimal import Decimal

# Константы для тестовой заявки
TEST_SERVICE_NAME = '[XSS-TEST] Тестовая услуга для проверки безопасности'
TEST_DESCRIPTION = 'Тестовая заявка для автоматической проверки XSS-уязвимостей <b>●</b>'
TEST_PRICE = Decimal('9999.00')

def create_or_update_test_request():
    """Создаёт или обновляет тестовую заявку"""
    print("=" * 70)
    print("🧪 СОЗДАНИЕ/ОБНОВЛЕНИЕ ТЕСТОВОЙ ЗАЯВКИ ДЛЯ XSS-ПРОВЕРКИ")
    print("=" * 70)
    
    # Берём первого активного клиента
    client = Client.objects.filter(is_active=True).first()
    
    if not client:
        print("❌ Нет активных клиентов!")
        print("💡 Запустите: bash restart.sh")
        return False
    
    print(f"✅ Клиент: {client.full_name} ({client.email})")
    
    # Проверяем, существует ли уже тестовая заявка
    existing_requests = ServiceRequest.objects.filter(
        service_name__icontains='[XSS-TEST]'
    )
    
    if existing_requests.exists():
        print(f"\n⚠️  Найдено {existing_requests.count()} существующих тестовых заявок")
        
        # Удаляем старые и создаём новую
        for req in existing_requests:
            print(f"   🗑️  Удаляю старую заявку ID: {req.id} (статус: {req.status})")
            req.delete()
    
    # Создаём новую тестовую заявку
    test_req = ServiceRequest.objects.create(
        client=client,
        service_name=TEST_SERVICE_NAME,
        service_description=TEST_DESCRIPTION,
        price=TEST_PRICE,
        status='pending'
    )
    
    print(f"\n✅ СОЗДАНА НОВАЯ ТЕСТОВАЯ ЗАЯВКА:")
    print("-" * 70)
    print(f"   ID: {test_req.id}")
    print(f"   Название: {test_req.service_name}")
    print(f"   Описание: {test_req.service_description}")
    print(f"   Цена: {test_req.price} ₽")
    print(f"   Статус: {test_req.status}")
    print(f"   Клиент: {test_req.client.full_name}")
    print(f"   Email: {test_req.client.email}")
    print("-" * 70)
    
    print("\n📋 ВАЖНАЯ ИНФОРМАЦИЯ:")
    print("   ✓ Заявка НЕ отображается в интерфейсе оператора2")
    print("   ✓ Заявка доступна только для check_xss.py")
    print("   ✓ URL проверки: http://localhost:8000/review-request/{}/".format(test_req.id))
    
    print("\n🔬 ПРОВЕРКА XSS:")
    print("   Запустите: python3 check_xss.py")
    
    print("\n" + "=" * 70)
    print("✅ ГОТОВО!")
    print("=" * 70)
    
    return True

if __name__ == '__main__':
    create_or_update_test_request()
