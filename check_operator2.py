#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from django.contrib.auth.models import User
from dbo.models import Operator

print("🔍 Проверка пользователя operator2...")

try:
    user = User.objects.get(username='operator2')
    print(f"✅ Пользователь найден:")
    print(f"   - username: {user.username}")
    print(f"   - email: {user.email}")
    print(f"   - is_active: {user.is_active}")
    print(f"   - first_name: {user.first_name}")
    print(f"   - last_name: {user.last_name}")
    
    # Проверяем пароль
    if user.check_password('password123'):
        print(f"   ✅ Пароль 'password123' ВЕРНЫЙ")
    else:
        print(f"   ❌ Пароль 'password123' НЕВЕРНЫЙ")
    
    # Проверяем оператора
    try:
        operator = Operator.objects.get(user=user)
        print(f"✅ Оператор найден:")
        print(f"   - operator_type: {operator.operator_type}")
        print(f"   - email: {operator.email}")
        print(f"   - is_active: {operator.is_active}")
    except Operator.DoesNotExist:
        print(f"❌ Запись Operator для user operator2 не найдена!")
        
except User.DoesNotExist:
    print(f"❌ Пользователь operator2 НЕ НАЙДЕН в базе данных!")
    print(f"\nСоздаю пользователя operator2...")
    user = User.objects.create_user(
        username='operator2',
        email='operator2@financepro.ru',
        password='password123',
        first_name='Иван',
        last_name='Сидоров'
    )
    print(f"✅ Пользователь создан")
    
    # Создаём оператора
    operator = Operator.objects.create(
        user=user,
        operator_type='security',
        email='operator2@financepro.ru',
        is_active=True
    )
    print(f"✅ Оператор создан")
