#!/usr/bin/env python3
"""Создание/обновление тестовой заявки для XSS-проверки"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from dbo.models import ServiceRequest, Client
from decimal import Decimal

# Константы для тестовой заявки
# Выглядит как обычная заявка, идентифицируется по слову "Тест" в начале названия
TEST_SERVICE_NAME = 'Тестирование безопасности сети'
TEST_DESCRIPTION = 'Проведение комплексного аудита безопасности корпоративной сети и веб-приложений <b>●</b>'
TEST_PRICE = Decimal('15000.00')  # Обычная цена

def create_or_update_test_request():
    """Создаёт или обновляет тестовую заявку"""
    print("=" * 70)
    print("🧪 СОЗДАНИЕ СЛУЖЕБНОЙ ЗАЯВКИ ДЛЯ АВТОМАТИЧЕСКОЙ ПРОВЕРКИ")
    print("=" * 70)
    
    # Берём первого активного клиента
    client = Client.objects.filter(is_active=True).first()
    
    if not client:
        print("❌ Нет активных клиентов!")
        print("💡 Запустите: bash restart.sh")
        return False
    
    print(f"✅ Клиент: {client.full_name} ({client.email})")
    
    # Проверяем, существует ли уже тестовая заявка (по слову "Тест" в начале)
    existing_requests = ServiceRequest.objects.filter(
        service_name__istartswith='тест',
        status='pending'
    )
    
    if existing_requests.exists():
        print(f"\n⚠️  Найдено {existing_requests.count()} существующих служебных заявок")
        
        # Удаляем старые и создаём новую
        for req in existing_requests:
            print(f"   🗑️  Удаляю старую заявку ID: {req.id} (статус: {req.status})")
            req.delete()
    
    # Создаём новую служебную заявку
    test_req = ServiceRequest.objects.create(
        client=client,
        service_name=TEST_SERVICE_NAME,
        service_description=TEST_DESCRIPTION,
        price=TEST_PRICE,
        status='pending'
    )
    
    print(f"\n✅ СОЗДАНА СЛУЖЕБНАЯ ЗАЯВКА:")
    print("-" * 70)
    print(f"   ID: {test_req.id}")
    print(f"   Название: {test_req.service_name}")
    print(f"   Описание: {test_req.service_description[:60]}...")
    print(f"   Цена: {test_req.price} ₽")
    print(f"   Статус: {test_req.status}")
    print(f"   🔍 Маркер: название начинается с 'Тест'")
    print(f"   Клиент: {test_req.client.full_name}")
    print(f"   Email: {test_req.client.email}")
    print("-" * 70)
    
    print("\n📋 ВАЖНАЯ ИНФОРМАЦИЯ:")
    print("   ✓ Заявка выглядит как обычная услуга тестирования")
    print("   ✓ Идентифицируется по слову 'Тест' в начале названия")
    print("   ✓ Содержит XSS-маркер <b>●</b> в описании")
    print("   ✓ URL проверки: http://localhost:8000/review-request/{}/".format(test_req.id))
    
    print("\n🔬 ПРОВЕРКА XSS:")
    print("   Запустите: python3 check_xss.py")
    
    print("\n" + "=" * 70)
    print("✅ ГОТОВО!")
    print("=" * 70)
    
    return True

if __name__ == '__main__':
    create_or_update_test_request()
