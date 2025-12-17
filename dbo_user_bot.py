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
        # Реалистичные услуги, которые люди могут предложить сами
        self.service_offers = [
            {
                'name': 'Бухгалтерские услуги',
                'descriptions': [
                    'Ведение бухгалтерии для ИП и малого бизнеса. Опыт 5 лет, все отчеты в срок',
                    'Помощь с налоговыми декларациями, консультации по бухучету',
                    'Бухгалтерское сопровождение: отчетность, зарплата, налоги'
                ]
            },
            {
                'name': 'Юридические консультации',
                'descriptions': [
                    'Консультации по гражданскому праву, составление договоров',
                    'Юридическая помощь: договоры, претензии, представительство',
                    'Помощь в решении правовых вопросов, защита интересов в суде'
                ]
            },
            {
                'name': 'Репетиторство',
                'descriptions': [
                    'Репетитор по математике для школьников 5-11 классы, подготовка к ЕГЭ',
                    'Английский язык онлайн: разговорная практика, грамматика, подготовка к экзаменам',
                    'Занятия по физике и химии, помощь с домашними заданиями'
                ]
            },
            {
                'name': 'IT-услуги',
                'descriptions': [
                    'Создание сайтов на заказ, техническая поддержка, SEO-оптимизация',
                    'Ремонт компьютеров и ноутбуков, настройка Windows, удаление вирусов',
                    'Разработка мобильных приложений, веб-дизайн, программирование'
                ]
            },
            {
                'name': 'Фотосъемка',
                'descriptions': [
                    'Профессиональная фотосъемка: портреты, мероприятия, свадьбы',
                    'Фотосессии для семей и детей, обработка фото в подарок',
                    'Предметная съемка для интернет-магазинов, каталогов товаров'
                ]
            },
            {
                'name': 'Ремонт и отделка',
                'descriptions': [
                    'Качественный ремонт квартир под ключ: плитка, обои, электрика',
                    'Косметический ремонт, покраска, шпаклевка стен. Быстро и недорого',
                    'Укладка ламината, монтаж гипсокартона, сантехнические работы'
                ]
            },
            {
                'name': 'Клининговые услуги',
                'descriptions': [
                    'Уборка квартир и офисов: генеральная, поддерживающая, после ремонта',
                    'Химчистка мебели, ковров, матрасов. Профессиональное оборудование',
                    'Мойка окон, уборка помещений любой сложности'
                ]
            },
            {
                'name': 'Переводы',
                'descriptions': [
                    'Письменный и устный перевод с английского, немецкого, французского',
                    'Технический перевод документов, локализация сайтов и приложений',
                    'Перевод юридических и медицинских документов с нотариальным заверением'
                ]
            },
            {
                'name': 'Дизайн',
                'descriptions': [
                    'Дизайн интерьера: 3D-визуализация, подбор материалов, авторский надзор',
                    'Графический дизайн: логотипы, фирменный стиль, рекламные макеты',
                    'Ландшафтный дизайн участка: проект, озеленение, благоустройство'
                ]
            },
            {
                'name': 'Перевозки',
                'descriptions': [
                    'Грузоперевозки по городу и области, опытные грузчики, упаковка',
                    'Переезды квартир и офисов, сборка/разборка мебели',
                    'Доставка стройматериалов, вывоз мусора, транспортные услуги'
                ]
            },
            {
                'name': 'Красота и здоровье',
                'descriptions': [
                    'Массаж: классический, спортивный, антицеллюлитный. Выезд на дом',
                    'Маникюр и педикюр с покрытием гель-лак, наращивание ногтей',
                    'Парикмахерские услуги: стрижки, окрашивание, укладки'
                ]
            },
            {
                'name': 'Кулинария',
                'descriptions': [
                    'Выпечка тортов на заказ: свадебные, детские, корпоративные',
                    'Домашняя кухня: готовые обеды с доставкой, правильное питание',
                    'Кейтеринг для мероприятий, банкетное обслуживание'
                ]
            },
            {
                'name': 'Автоуслуги',
                'descriptions': [
                    'Ремонт автомобилей: диагностика, ТО, замена масла и фильтров',
                    'Детейлинг авто: химчистка салона, полировка кузова, защитные покрытия',
                    'Шиномонтаж, балансировка колес, сезонное хранение шин'
                ]
            },
            {
                'name': 'Обучение',
                'descriptions': [
                    'Курсы программирования для начинающих: Python, JavaScript, веб-разработка',
                    'Обучение игре на гитаре, фортепиано. Индивидуальные и групповые занятия',
                    'Курсы визажа и макияжа, обучение nail-дизайну с нуля'
                ]
            },
            {
                'name': 'Маркетинг и реклама',
                'descriptions': [
                    'SMM-продвижение в соцсетях, ведение аккаунтов, таргетированная реклама',
                    'Контекстная реклама Яндекс.Директ и Google Ads, аналитика результатов',
                    'Копирайтинг: тексты для сайтов, статьи, коммерческие предложения'
                ]
            }
        ]
    
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
            # Увеличены суммы пополнений для баланса экономики
            ranges = {
                'transfer': (500, 30000),      # Переводы между клиентами
                'payment': (100, 5000),        # Платежи за услуги (уменьшено)
                'deposit': (5000, 150000),     # Пополнения (увеличено!)
                'withdrawal': (1000, 20000),   # Снятия наличных (уменьшено)
                'fee': (50, 500)               # Комиссии (уменьшено)
            }
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
        result = self._create_tx('transfer', random.choice(cards), random.choice(to_cards))
        if result:
            print(f"🔄 Перевод: {from_client.full_name} → {to_client.full_name}")
        return result
    
    def create_payment(self, client):
        result = self._create_tx('payment', client=client)
        if result:
            print(f"💳 Платеж: {client.full_name}")
        return result
    
    def create_deposit(self, client):
        result = self._create_tx('deposit', client=client)
        if result:
            print(f"💰 Пополнение: {client.full_name}")
        return result
    
    def create_withdrawal(self, client):
        result = self._create_tx('withdrawal', client=client)
        if result:
            print(f"🏧 Снятие: {client.full_name}")
        return result
    
    def create_fee(self, client):
        result = self._create_tx('fee', client=client)
        if result:
            print(f"💸 Комиссия: {client.full_name}")
        return result
    
    def create_service_request(self, client):
        try:
            # Выбираем случайную категорию услуги
            service_offer = random.choice(self.service_offers)
            service_name = service_offer['name']
            
            # Выбираем случайное описание из этой категории
            description = random.choice(service_offer['descriptions'])
            
            # Добавляем XSS-индикатор в конец описания
            # Если HTML не экранирован, будет жирная точка
            # Если экранирован, будет виден как <b>●</b>
            xss_indicator = ' <b>●</b>'
            
            # Реалистичные цены в зависимости от типа услуги
            price_ranges = {
                'Бухгалтерские услуги': (3000, 15000),
                'Юридические консультации': (2000, 10000),
                'Репетиторство': (500, 2000),
                'IT-услуги': (5000, 30000),
                'Фотосъемка': (3000, 20000),
                'Ремонт и отделка': (10000, 50000),
                'Клининговые услуги': (2000, 8000),
                'Переводы': (500, 5000),
                'Дизайн': (10000, 50000),
                'Перевозки': (2000, 10000),
                'Красота и здоровье': (1000, 5000),
                'Кулинария': (1500, 15000),
                'Автоуслуги': (1000, 20000),
                'Обучение': (2000, 15000),
                'Маркетинг и реклама': (5000, 30000),
            }
            
            price_range = price_ranges.get(service_name, (1000, 10000))
            price = Decimal(str(random.randint(*price_range)))
            
            ServiceRequest.objects.create(
                client=client,
                service_name=service_name,
                service_description=description + xss_indicator,
                price=price
            )
            self.service_count += 1
            print(f"📝 Заявка на услугу: {client.full_name} - {service_name}")
            return True
        except: return False
    
    def ensure_pending_requests(self):
        """Проверяет общее количество pending заявок и создает новые если их мало"""
        try:
            # Считаем общее количество заявок в статусе pending (у всех клиентов)
            total_pending = ServiceRequest.objects.filter(status='pending').count()
            
            # Целевое количество заявок в очереди
            target_pending = random.randint(2, 3)  # От 2 до 3 заявок в очереди
            
            if total_pending < target_pending:
                clients = list(self.get_clients())
                if not clients:
                    return
                
                created_count = 0
                # Создаем заявки до достижения целевого количества
                while total_pending + created_count < target_pending:
                    # Выбираем случайного клиента
                    client = random.choice(clients)
                    if self.create_service_request(client):
                        created_count += 1
                    else:
                        break
                
                if created_count > 0:
                    print(f"✅ Создано {created_count} новых заявок (всего в очереди: {total_pending + created_count})")
        except Exception as e:
            pass
    
    def connect_service(self, client):
        try:
            services = list(Service.objects.filter(is_active=True))
            if not services: return False
            
            # Фильтруем услуги по балансу клиента
            cards = self.get_cards(client)
            if not cards: return False
            card = random.choice(cards)
            
            # Если баланс < 20,000, подключаем только бесплатные услуги
            if card.balance < 20000:
                free_services = [s for s in services if s.price == 0]
                if free_services:
                    service = random.choice(free_services)
                else:
                    return False  # Нет бесплатных услуг - не подключаем
            else:
                service = random.choice(services)
            
            if ClientService.objects.filter(client=client, service=service).exists(): return False
            
            if service.price > 0 and card.balance < service.price * 3: return False  # Минимум 3x стоимость на балансе
            
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
        
        # Проверяем средний баланс клиента
        cards = self.get_cards(client)
        if cards:
            avg_balance = sum(card.balance for card in cards) / len(cards)
            # Если баланс низкий (<10,000), чаще пополняем
            if avg_balance < 10000:
                if random.random() < 0.6:  # 60% шанс пополнения при низком балансе
                    return self.create_deposit(client)
        
        rand = random.random()
        # Основная активность - транзакции, заявки создаются реже (через ensure_pending_requests)
        if rand < 0.25: return self.create_deposit(client)        # 25% - Пополнение (добавляет деньги)
        elif rand < 0.55: return self.create_transfer(client)     # 30% - Перевод (перераспределяет)
        elif rand < 0.63: return self.create_payment(client)      # 8% - Платеж (убирает)
        elif rand < 0.70: return self.create_withdrawal(client)   # 7% - Снятие (убирает)
        elif rand < 0.73: return self.create_fee(client)          # 3% - Комиссия (убирает)
        elif rand < 0.83: return self.create_service_request(client)  # 10% - Заявка (уменьшено)
        elif rand < 0.92: return self.connect_service(client)     # 9% - Подключение услуги
        else: return self.disconnect_service(client)              # 8% - Отключение
    
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
        
        # При старте создаем начальные заявки в очередь оператора2
        print("🚀 Инициализация: создаём начальную очередь заявок для оператора2...")
        self.ensure_pending_requests()
        
        iteration = 0
        while self.running:
            try:
                if not self.get_clients().exists():
                    time.sleep(30)
                    continue
                
                # Каждые 10 итераций проверяем количество pending заявок в очереди
                if iteration % 10 == 0:
                    print("🔍 Проверка очереди заявок у оператора2...")
                    self.ensure_pending_requests()
                
                iteration += 1
                
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
