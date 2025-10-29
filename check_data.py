#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from dbo.models import Client, BankCard, User
from django.contrib.auth.models import User

def check_data():
    print("=== ПРОВЕРКА ДАННЫХ ===")
    print(f"Пользователи: {User.objects.count()}")
    print(f"Клиенты: {Client.objects.count()}")
    print(f"Карты: {BankCard.objects.count()}")
    
    if Client.objects.count() == 0:
        print("\n❌ Данные не инициализированы!")
        print("Запустите: python init_data.py")
        return False
    
    print("\n=== КЛИЕНТЫ И ИХ КАРТЫ ===")
    for client in Client.objects.all():
        print(f"\n👤 {client.full_name} ({client.client_id})")
        print(f"   📞 Телефон: {client.phone}")
        print(f"   👑 Основная карта: {client.primary_card.card_number if client.primary_card else 'НЕТ'}")
        
        cards = BankCard.objects.filter(client=client)
        print(f"   💳 Всего карт: {cards.count()}")
        for card in cards:
            status = "✅ АКТИВНА" if card.is_active else "❌ НЕАКТИВНА"
            print(f"      - {card.card_number}: {card.balance} ₽ ({status})")
    
    return True

if __name__ == "__main__":
    check_data()
