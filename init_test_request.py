#!/usr/bin/env python3
"""Создание/обновление тестовой заявки для XSS-проверки"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from django.utils import timezone
from dbo.models import ServiceRequest, Client, Service, ServiceCategory

def create_or_update_test_request():
    """Создаёт или обновляет тестовую заявку для XSS-проверки"""
    try:
        # Получаем клиента client1
        client = Client.objects.get(email='client1@financepro.ru')
        
        # Получаем категорию услуг (любую, кроме служебных)
        category = ServiceCategory.objects.exclude(name__icontains='Служебные').first()
        if not category:
            print("❌ Не найдена категория услуг")
            return False
        
        # Получаем любую услугу из категории
        service = Service.objects.filter(category=category, is_active=True).first()
        if not service:
            print("❌ Не найдена услуга")
            return False
        
        # Ищем существующую заявку от client1
        existing_request = ServiceRequest.objects.filter(client=client).first()
        
        if existing_request:
            # Обновляем существующую заявку
            existing_request.service = service
            existing_request.description = f"<script>alert('XSS')</script>"
            existing_request.status = 'pending'
            existing_request.save()
            print(f"✅ Обновлена заявка #{existing_request.id}")
            return True
        else:
            # Создаём новую заявку
            new_request = ServiceRequest.objects.create(
                client=client,
                service=service,
                description=f"<script>alert('XSS')</script>",
                status='pending'
            )
            print(f"✅ Создана заявка #{new_request.id}")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    create_or_update_test_request()

