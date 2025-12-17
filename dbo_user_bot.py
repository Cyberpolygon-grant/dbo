#!/usr/bin/env python3
import os, sys, django, time, random
from decimal import Decimal
from datetime import datetime, date, timedelta
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()
from django.utils import timezone
from dbo.models import Client, BankCard, Transaction, Service, ServiceRequest, ClientService, ServiceCategory

class DBOUserBot:
    def __init__(self):
        self.running = True
        self.count = 0
        self.service_count = 0
        self.descriptions = {
            'transfer': ["Перевод другу", "Перевод родственнику", "Возврат долга", "Оплата услуг", "Перевод на другой счет"],
            'payment': ["Оплата интернета", "Оплата мобильной связи", "Оплата ЖКХ", "Оплата подписки", "Оплата товаров", "Оплата электроэнергии"],
            'deposit': ["Пополнение через банкомат", "Зарплата", "Возврат средств", "Пополнение карты", "Пополнение с другого счета"],
            'withdrawal': ["Снятие наличных в банкомате", "Снятие наличных в отделении", "Снятие наличных"],
            'fee': ["Комиссия за обслуживание", "Комиссия за перевод", "Ежемесячная комиссия"]
        }
        self.service_names = ["Онлайн-консультация", "Мобильное приложение", "СМС-уведомления", "Кэшбэк программа", "Премиум поддержка", "Автоплатежи", "Инвестиции", "Страхование", "Кредитная карта", "Депозит"]
        self.service_descriptions = ["Удобный сервис для клиентов", "Полезная услуга для управления финансами", "Современное решение для банковских операций", "Выгодное предложение", "Качественный сервис"]
    
    def get_clients(self):
        return Client.objects.filter(is_active=True).prefetch_related('cards').filter(cards__is_active=True).distinct()
    
    def get_cards(self, client):
        return list(client.cards.filter(is_active=True))
    
    def _create_tx(self, tx_type, from_card=None, to_card=None, amount=None, client=None):
        if client:
            cards = self.get_cards(client)
            if not cards: return False
            card = random.choice(cards)
            if from_card is None: from_card = card
            if to_card is None and tx_type == 'deposit': to_card = card
        
        if not amount:
            ranges = {'transfer': (100, 50000), 'payment': (50, 10000), 'deposit': (500, 100000), 
                     'withdrawal': (500, 50000), 'fee': (10, 500)}
            amount = Decimal(str(random.randint(*ranges[tx_type])))
        
        if from_card and from_card.balance < amount: return False
        
        if from_card:
            from_card.balance -= amount
            from_card.save(update_fields=['balance'])
        if to_card:
            to_card.balance += amount
            to_card.save(update_fields=['balance'])
        
        Transaction.objects.create(
            from_card=from_card, to_card=to_card, amount=amount, currency='RUB',
            transaction_type=tx_type, description=random.choice(self.descriptions[tx_type]),
            status='completed', created_at=timezone.now(), completed_at=timezone.now()
        )
        self.count += 1
        return True
    
    def create_transfer(self, from_client, to_client=None):
        cards = self.get_cards(from_client)
        if not cards: return False
        if not to_client:
            clients = list(self.get_clients().exclude(id=from_client.id))
            if not clients: return False
            to_client = random.choice(clients)
        to_cards = self.get_cards(to_client)
        if not to_cards: return False
        return self._create_tx('transfer', random.choice(cards), random.choice(to_cards))
    
    def create_payment(self, client):
        return self._create_tx('payment', client=client)
    
    def create_deposit(self, client):
        return self._create_tx('deposit', client=client)
    
    def create_withdrawal(self, client):
        return self._create_tx('withdrawal', client=client)
    
    def create_fee(self, client):
        return self._create_tx('fee', client=client)
    
    def create_service_request(self, client):
        try:
            # Добавляем XSS-индикатор в конец описания
            # Если HTML не экранирован, символ будет выделен (жирный/красный)
            # Если экранирован, будет виден как текст <b>●</b>
            description = random.choice(self.service_descriptions)
            xss_indicator = " <b>●</b>"  # Жирная точка - индикатор XSS
            
            ServiceRequest.objects.create(
                client=client,
                service_name=random.choice(self.service_names) + f" {random.randint(1, 100)}",
                service_description=description + xss_indicator,
                price=Decimal(str(random.randint(0, 5000)))
            )
            self.service_count += 1
            return True
        except: return False
    
    def connect_service(self, client):
        try:
            services = list(Service.objects.filter(is_active=True))
            if not services: return False
            service = random.choice(services)
            if ClientService.objects.filter(client=client, service=service).exists(): return False
            
            cards = self.get_cards(client)
            if not cards: return False
            card = random.choice(cards)
            
            if service.price > 0 and card.balance < service.price: return False
            
            next_payment = date.today() + timedelta(days=30) if service.price > 0 else None
            ClientService.objects.create(
                client=client, service=service, monthly_fee=service.price,
                next_payment_date=next_payment, status='active'
            )
            
            if service.price > 0:
                card.balance -= service.price
                card.save(update_fields=['balance'])
                Transaction.objects.create(
                    from_card=card, to_card=None, amount=service.price, currency='RUB',
                    transaction_type='payment', description=f'Оплата подключения услуги "{service.name}"',
                    status='completed', created_at=timezone.now(), completed_at=timezone.now()
                )
                self.count += 1
            self.service_count += 1
            return True
        except: return False
    
    def disconnect_service(self, client):
        try:
            services = list(ClientService.objects.filter(client=client, status='active', is_active=True))
            if not services: return False
            cs = random.choice(services)
            cs.status = 'cancelled'
            cs.is_active = False
            cs.cancelled_at = timezone.now()
            cs.save()
            self.service_count += 1
            return True
        except: return False
    
    def get_interval(self):
        h = datetime.now().hour
        mult = 1.0 if 9 <= h <= 21 else 0.3 if (22 <= h <= 23 or 0 <= h <= 8) else 0.5
        return max(5, min(300, int(30 * mult * random.uniform(0.5, 2.0))))
    
    def generate(self):
        client = random.choice(list(self.get_clients())) if self.get_clients().exists() else None
        if not client: return False
        rand = random.random()
        if rand < 0.15: return self.create_deposit(client)
        elif rand < 0.35: return self.create_payment(client)
        elif rand < 0.55: return self.create_transfer(client)
        elif rand < 0.70: return self.create_withdrawal(client)
        elif rand < 0.80: return self.create_fee(client)
        elif rand < 0.90: return self.create_service_request(client)
        elif rand < 0.97: return self.connect_service(client)
        else: return self.disconnect_service(client)
    
    def wait_db(self):
        from django.db import connection
        for i in range(60):
            try:
                connection.ensure_connection()
                Client.objects.count()
                return True
            except: time.sleep(2)
        return False
    
    def run(self):
        self.wait_db()
        while self.running:
            try:
                if not self.get_clients().exists():
                    time.sleep(30)
                    continue
                if self.generate():
                    time.sleep(self.get_interval())
                else:
                    time.sleep(5)
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                time.sleep(10)

if __name__ == '__main__':
    DBOUserBot().run()
