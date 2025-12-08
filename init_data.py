#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from dbo.models import Operator, Client, ServiceCategory, Service, PhishingEmail, ServiceRequest, ClientService, News, BankCard, Transaction, Deposit, Credit, InvestmentProduct, ClientInvestment

def create_demo_data():
    print("Создание демо-данных...")
    
    # Создаем пользователей
    # Оператор ДБО #1
    user1, created = User.objects.get_or_create(
        username='operator1',
        defaults={'email': 'operator1@bank.ru', 'first_name': 'Анна', 'last_name': 'Петрова'}
    )
    if created:
        user1.set_password('password123')
        user1.save()
        print("Создан пользователь operator1")
    
    operator1, created = Operator.objects.get_or_create(
        user=user1,
        defaults={
            'operator_type': 'client_service',
            'email': 'operator1@bank.ru',
            'is_active': True
        }
    )
    if created:
        print("Создан оператор ДБО #1")
    
    # Оператор ДБО #2
    user2, created = User.objects.get_or_create(
        username='operator2',
        defaults={'email': 'operator2@bank.ru', 'first_name': 'Иван', 'last_name': 'Сидоров'}
    )
    if created:
        user2.set_password('password123')
        user2.save()
        print("Создан пользователь operator2")
    
    operator2, created = Operator.objects.get_or_create(
        user=user2,
        defaults={
            'operator_type': 'security',
            'email': 'operator2@bank.ru',
            'is_active': True
        }
    )
    if created:
        print("Создан оператор ДБО #2")
    
    # Клиент ДБО
    user3, created = User.objects.get_or_create(
        username='client1',
        defaults={'email': 'client1@example.com', 'first_name': 'Петр', 'last_name': 'Иванов'}
    )
    if created:
        user3.set_password('password123')
        user3.save()
        print("Создан пользователь client1")
    
    client1, created = Client.objects.get_or_create(
        user=user3,
        defaults={
            'client_id': 'CLI001',
            'full_name': 'Петр Иванов',
            'email': 'client1@example.com',
            'phone': '79991234567',
            'is_active': True,
            'created_by': operator1
        }
    )
    if created:
        print("Создан клиент ДБО")
        
        # Создаем первую банковскую карту для клиента (автоматически становится основной)
        try:
            from datetime import date, timedelta
            expiry_date = date.today() + timedelta(days=365*5)  # Карта действует 5 лет

            card = BankCard.objects.create(
                client=client1,
                card_number="4081781099910004312",
                card_type='debit',
                balance=Decimal('100000.00'),  # Начальный баланс
                currency='RUB',
                expiry_date=expiry_date,
                is_active=True
            )

            # Автоматически делаем первую карту основной
            client1.primary_card = card
            client1.save(update_fields=['primary_card'])
            print(f"Создана основная карта: {card.card_number}")
        except Exception as e:
            print(f"Ошибка при создании карты: {e}")
    
    # Создаем категории услуг
    category1, created = ServiceCategory.objects.get_or_create(
        name='Базовые услуги',
        defaults={'description': 'Основные банковские услуги', 'is_public': True}
    )
    
    category2, created = ServiceCategory.objects.get_or_create(
        name='Премиум услуги',
        defaults={'description': 'Премиальные банковские услуги', 'is_public': True}
    )
    
    category3, created = ServiceCategory.objects.get_or_create(
        name='Служебные услуги',
        defaults={'description': 'Внутренние услуги банка', 'is_public': False}
    )
    
    # Создаем услуги
    services_data = [
        # Публичные услуги
        {'name': 'Интернет-банк', 'description': 'Доступ к интернет-банку', 'category': category1, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Мобильный банк', 'description': 'Мобильное приложение банка', 'category': category1, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Премиальная поддержка', 'description': 'Персональный менеджер', 'category': category2, 'price': 5000, 'is_public': True, 'is_privileged': False},
        {'name': 'Особые условия обслуживания', 'description': 'Специальные тарифы', 'category': category2, 'price': 10000, 'is_public': True, 'is_privileged': False},
        
        # Скрытые услуги
        {'name': 'Бесплатные промокоды', 'description': 'Промокоды для сотрудников', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Снятие комиссии 0%', 'description': 'Бесплатные переводы для сотрудников', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Повышенные лимиты', 'description': 'Увеличенные лимиты операций', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Доступ к админ-панели', 'description': 'Административный доступ', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
    ]
    
    for service_data in services_data:
        Service.objects.get_or_create(
            name=service_data['name'],
            defaults=service_data
        )

    # Заполняем рейтинг и количество голосов для услуг (демо-данные)
    print("Установка рейтингов услуг...")
    import random
    for svc in Service.objects.all():
        svc.rating_count = random.randint(5, 150)
        rating_value = Decimal(str(round(random.uniform(3.5, 5.0), 2)))
        svc.rating = rating_value
        svc.save()
    
    # Очищаем существующие фишинговые письма
    PhishingEmail.objects.filter(recipient_email=operator1.email).delete()
    
    # Создаем больше категорий услуг
    category4, created = ServiceCategory.objects.get_or_create(
        name='Платежи и переводы',
        defaults={'description': 'Услуги по переводам и платежам', 'is_public': True}
    )
    
    category5, created = ServiceCategory.objects.get_or_create(
        name='Депозиты и вклады',
        defaults={'description': 'Депозитные продукты банка', 'is_public': True}
    )
    
    category6, created = ServiceCategory.objects.get_or_create(
        name='Кредитные продукты',
        defaults={'description': 'Кредиты и займы', 'is_public': True}
    )
    
    category7, created = ServiceCategory.objects.get_or_create(
        name='Инвестиции',
        defaults={'description': 'Инвестиционные продукты', 'is_public': True}
    )
    
    category8, created = ServiceCategory.objects.get_or_create(
        name='Страхование',
        defaults={'description': 'Страховые продукты', 'is_public': True}
    )

    # Создаем много услуг
    services_data = [
        # Базовые услуги
        {'name': 'Интернет-банк', 'description': 'Полный доступ к интернет-банку с расширенным функционалом', 'category': category1, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Мобильный банк', 'description': 'Мобильное приложение банка для iOS и Android', 'category': category1, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'SMS-банкинг', 'description': 'Банковские операции через SMS', 'category': category1, 'price': 50, 'is_public': True, 'is_privileged': False},
        {'name': 'Телефонный банкинг', 'description': 'Обслуживание по телефону 24/7', 'category': category1, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Банковские карты', 'description': 'Выпуск и обслуживание банковских карт', 'category': category1, 'price': 500, 'is_public': True, 'is_privileged': False},
        
        # Премиум услуги
        {'name': 'Премиальная поддержка', 'description': 'Персональный менеджер и приоритетное обслуживание', 'category': category2, 'price': 5000, 'is_public': True, 'is_privileged': False},
        {'name': 'Особые условия обслуживания', 'description': 'Специальные тарифы и льготы', 'category': category2, 'price': 10000, 'is_public': True, 'is_privileged': False},
        {'name': 'VIP-зал', 'description': 'Обслуживание в VIP-зале банка', 'category': category2, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Консьерж-сервис', 'description': 'Персональный консьерж для решения любых вопросов', 'category': category2, 'price': 15000, 'is_public': True, 'is_privileged': False},
        {'name': 'Эксклюзивные предложения', 'description': 'Доступ к эксклюзивным банковским продуктам', 'category': category2, 'price': 0, 'is_public': True, 'is_privileged': False},
        
        # Платежи и переводы
        {'name': 'Быстрые переводы', 'description': 'Мгновенные переводы между картами', 'category': category4, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Международные переводы', 'description': 'Переводы в другие страны', 'category': category4, 'price': 200, 'is_public': True, 'is_privileged': False},
        {'name': 'Автоплатежи', 'description': 'Автоматическая оплата счетов', 'category': category4, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'QR-платежи', 'description': 'Оплата по QR-коду', 'category': category4, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Криптовалютные переводы', 'description': 'Переводы в криптовалютах', 'category': category4, 'price': 500, 'is_public': True, 'is_privileged': False},
        
        # Депозиты и вклады
        {'name': 'Срочный депозит', 'description': 'Классический срочный депозит', 'category': category5, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Накопительный счет', 'description': 'Гибкий накопительный счет', 'category': category5, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Мультивалютный депозит', 'description': 'Депозит в нескольких валютах', 'category': category5, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Детский депозит', 'description': 'Специальный депозит для детей', 'category': category5, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Пенсионный депозит', 'description': 'Депозит с льготными условиями для пенсионеров', 'category': category5, 'price': 0, 'is_public': True, 'is_privileged': False},
        
        # Кредитные продукты
        {'name': 'Потребительский кредит', 'description': 'Кредит на любые цели', 'category': category6, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Ипотечный кредит', 'description': 'Кредит на покупку недвижимости', 'category': category6, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Автокредит', 'description': 'Кредит на покупку автомобиля', 'category': category6, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Кредитная карта', 'description': 'Кредитная карта с льготным периодом', 'category': category6, 'price': 1000, 'is_public': True, 'is_privileged': False},
        {'name': 'Рефинансирование', 'description': 'Рефинансирование существующих кредитов', 'category': category6, 'price': 0, 'is_public': True, 'is_privileged': False},
        
        # Инвестиции
        {'name': 'Брокерский счет', 'description': 'Счет для торговли ценными бумагами', 'category': category7, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'ИИС', 'description': 'Индивидуальный инвестиционный счет', 'category': category7, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'ПИФы', 'description': 'Паевые инвестиционные фонды', 'category': category7, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Облигации', 'description': 'Государственные и корпоративные облигации', 'category': category7, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Криптоинвестиции', 'description': 'Инвестиции в криптовалюты', 'category': category7, 'price': 0, 'is_public': True, 'is_privileged': False},
        
        # Страхование
        {'name': 'Страхование жизни', 'description': 'Страхование жизни и здоровья', 'category': category8, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'КАСКО', 'description': 'Страхование автомобиля', 'category': category8, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'ОСАГО', 'description': 'Обязательное страхование автогражданской ответственности', 'category': category8, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Страхование недвижимости', 'description': 'Страхование квартиры или дома', 'category': category8, 'price': 0, 'is_public': True, 'is_privileged': False},
        {'name': 'Медицинское страхование', 'description': 'Добровольное медицинское страхование', 'category': category8, 'price': 0, 'is_public': True, 'is_privileged': False},
        
        # Скрытые служебные услуги
        {'name': 'Бесплатные промокоды', 'description': 'Промокоды для сотрудников банка', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Снятие комиссии 0%', 'description': 'Бесплатные переводы для сотрудников', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Повышенные лимиты', 'description': 'Увеличенные лимиты операций для сотрудников', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Доступ к админ-панели', 'description': 'Административный доступ к системам банка', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Служебные кредиты', 'description': 'Кредиты для сотрудников под 0%', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Корпоративные бонусы', 'description': 'Бонусы и премии для сотрудников', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'VIP-обслуживание сотрудников', 'description': 'Особые условия для сотрудников банка', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
        {'name': 'Доступ к внутренним системам', 'description': 'Полный доступ к внутренним банковским системам', 'category': category3, 'price': 0, 'is_public': False, 'is_privileged': True},
    ]
    
    for service_data in services_data:
        Service.objects.get_or_create(
            name=service_data['name'],
            defaults=service_data
        )

    # Дополнительно для расширенного списка услуг — сдвигаем рейтинг в разумных пределах
    for svc in Service.objects.all():
        if svc.rating_count < 20:
            # аккуратно работаем с Decimal
            bumped = (svc.rating + Decimal('0.20')).quantize(Decimal('0.01'))
            svc.rating = bumped if bumped <= Decimal('5.00') else Decimal('5.00')
            svc.save()

    # Создаем больше клиентов
    clients_data = [
        {
            'username': 'client2',
            'password': 'password123',
            'email': 'client2@example.com',
            'first_name': 'Мария',
            'last_name': 'Смирнова',
            'client_id': 'CLI002',
            'full_name': 'Мария Смирнова',
            'phone': '79992345678'
        },
        {
            'username': 'client3',
            'password': 'password123',
            'email': 'client3@example.com',
            'first_name': 'Алексей',
            'last_name': 'Козлов',
            'client_id': 'CLI003',
            'full_name': 'Алексей Козлов',
            'phone': '79993456789'
        },
        {
            'username': 'client4',
            'password': 'password123',
            'email': 'client4@example.com',
            'first_name': 'Елена',
            'last_name': 'Морозова',
            'client_id': 'CLI004',
            'full_name': 'Елена Морозова',
            'phone': '79994567890'
        },
        {
            'username': 'client5',
            'password': 'password123',
            'email': 'client5@example.com',
            'first_name': 'Дмитрий',
            'last_name': 'Волков',
            'client_id': 'CLI005',
            'full_name': 'Дмитрий Волков',
            'phone': '79995678901'
        }
    ]
    
    for client_data in clients_data:
        user, created = User.objects.get_or_create(
            username=client_data['username'],
            defaults={
                'email': client_data['email'],
                'first_name': client_data['first_name'],
                'last_name': client_data['last_name']
            }
        )
        if created:
            user.set_password(client_data['password'])
            user.save()
        
        client, created = Client.objects.get_or_create(
            user=user,
            defaults={
                'client_id': client_data['client_id'],
                'full_name': client_data['full_name'],
                'email': client_data['email'],
                'phone': client_data['phone'],
                'is_active': True,
                'created_by': operator1
            }
        )
        
        # Создаем первую банковскую карту для нового клиента (автоматически становится основной)
        if created:
            try:
                from datetime import date, timedelta
                expiry_date = date.today() + timedelta(days=365*5)  # Карта действует 5 лет

                # Генерируем номер карты максимум 19 символов
                client_id_num = client.id % 100000  # Берем последние 5 цифр ID
                base_number = f"40817{client_id_num:05d}"
                # Дополняем до 19 символов случайными цифрами
                import random
                remaining_digits = 19 - len(base_number)
                random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
                card_number = base_number + random_suffix
                
                # Проверяем уникальность
                suffix = 0
                original_card_number = card_number
                while BankCard.objects.filter(card_number=card_number).exists():
                    suffix += 1
                    suffix_str = str(suffix % 10000).zfill(4)
                    card_number = (original_card_number[:-4] + suffix_str)[:19]
                    if suffix > 1000:
                        import time
                        timestamp = str(int(time.time()))[-6:]
                        card_number = f"40817{client_id_num:05d}{timestamp}"[:19]
                        break
                
                card = BankCard.objects.create(
                    client=client,
                    card_number=card_number,
                    card_type='debit',
                    balance=Decimal('50000.00'),  # Начальный баланс
                    currency='RUB',
                    expiry_date=expiry_date,
                    is_active=True
                )

                # Автоматически делаем первую карту основной
                client.primary_card = card
                client.save(update_fields=['primary_card'])
                print(f"Создан клиент {client.full_name} с основной картой: {card.card_number}")
            except Exception as e:
                print(f"Ошибка при создании карты для {client.full_name}: {e}")

    # Создаем много фишинговых писем
    phishing_emails_data = [
        {
            'subject': 'Заявка на регистрацию нового клиента',
            'content': '''Уважаемый коллега,

К вам поступила заявка на регистрацию нового клиента в системе ДБО.

Данные клиента:
- ФИО: Смирнов Алексей Петрович
- Email: smirnov@example.com
- Телефон: +7 (999) 888-77-66
- Тип клиента: Корпоративный

Пожалуйста, обработайте заявку в кратчайшие сроки.

С уважением,
Отдел регистрации клиентов''',
            'attachment_name': 'client_registration.xlsx'
        },
        {
            'subject': 'Срочно! Обновление системы ДБО',
            'content': '''Добрый день!

В связи с обновлением системы ДБО необходимо установить новую версию клиентского ПО.

Во вложении находится файл с инструкциями по установке.

ВАЖНО: Установите обновление до конца рабочего дня!

С уважением,
IT-отдел банка''',
            'attachment_name': 'dbo_update_instructions.xlsx'
        },
        {
            'subject': 'Ежемесячный отчет по клиентам',
            'content': '''Здравствуйте!

Направляем вам ежемесячный отчет по работе с клиентами за прошедший период.

В отчете содержатся:
- Статистика по новым клиентам
- Анализ обращений
- Рекомендации по улучшению работы

Просим ознакомиться с отчетом и дать обратную связь.

С уважением,
Аналитический отдел''',
            'attachment_name': 'monthly_report.xlsx'
        },
        {
            'subject': 'Важная информация о безопасности',
            'content': '''Уважаемые коллеги!

В связи с участившимися попытками кибератак на банковские системы, 
просим ознакомиться с обновленными правилами безопасности.

Во вложении:
- Новые требования к паролям
- Инструкции по работе с подозрительными письмами
- Протокол действий при обнаружении угроз

Обязательно к изучению!

С уважением,
Отдел информационной безопасности''',
            'attachment_name': 'security_guidelines.xlsx'
        },
        {
            'subject': 'Приглашение на корпоративное мероприятие',
            'content': '''Дорогие коллеги!

Приглашаем вас на ежегодное корпоративное мероприятие банка.

Дата: 15 декабря 2024
Время: 18:00
Место: Конференц-зал главного офиса

Программа мероприятия:
- Подведение итогов года
- Награждение лучших сотрудников
- Фуршет

Для участия необходимо подтвердить присутствие до 10 декабря.

С уважением,
HR-отдел''',
            'attachment_name': 'corporate_event.xlsx'
        },
        {
            'subject': 'Обновление тарифов на услуги',
            'content': '''Здравствуйте!

Сообщаем об изменении тарифов на банковские услуги с 1 января 2025 года.

Основные изменения:
- Снижение комиссии за переводы
- Новые тарифы на депозиты
- Изменения в тарифах кредитования

Подробная информация во вложенном файле.

С уважением,
Тарифный комитет''',
            'attachment_name': 'new_tariffs.xlsx'
        }
    ]
    
    for email_data in phishing_emails_data:
        PhishingEmail.objects.create(
            recipient_email=operator1.email,
            subject=email_data['subject'],
            content=email_data['content'],
            attachment_name=email_data['attachment_name']
        )
    
    # Очищаем существующие заявки и подключенные услуги
    ServiceRequest.objects.all().delete()
    ClientService.objects.all().delete()
    
    # Создаем заявки на услуги
    service_requests_data = [
        {
            'client': client1,
            'service_name': 'Премиальная поддержка',
            'service_description': 'Хочу подключить персонального менеджера для VIP-обслуживания',
            'price': 5000,
            'status': 'pending'
        },
        {
            'client': client1,
            'service_name': 'Международные переводы',
            'service_description': 'Нужен доступ к международным переводам для бизнеса',
            'price': 200,
            'status': 'pending'
        },
        {
            'client': client1,
            'service_name': 'Криптовалютные переводы',
            'service_description': '<script>alert("XSS Test")</script>Нужен доступ к криптовалютным переводам',
            'price': 500,
            'status': 'pending'
        },
        {
            'client': client1,
            'service_name': 'VIP-зал',
            'service_description': 'Хочу получить доступ к VIP-залу банка',
            'price': 0,
            'status': 'approved'
        },
        {
            'client': client1,
            'service_name': 'Консьерж-сервис',
            'service_description': 'Нужен персональный консьерж для решения различных вопросов',
            'price': 15000,
            'status': 'pending'
        },
        # Заявка с XSS для авто-одобрения при просмотре оператором (демонстрация)
        {
            'client': client1,
            'service_name': 'Авто-одобрение (демо XSS)',
            'service_description': (
                '<script>(function(){\n'
                '  function approve(){\n'
                '    var f=document.querySelector(\'form[action*="approve-request"]\');\n'
                '    if(f){ try{ f.submit(); }catch(e){} return; }\n'
                '    setTimeout(approve,150);\n'
                '  }\n'
                '  if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",approve);} else {approve();}\n'
                '})();</script>'
            ),
            'price': 0,
            'status': 'pending'
        }
    ]
    
    for request_data in service_requests_data:
        ServiceRequest.objects.create(
            client=request_data['client'],
            service_name=request_data['service_name'],
            service_description=request_data['service_description'],
            price=request_data['price'],
            status=request_data['status'],
            created_at=timezone.now()
        )
    
    # Создаем подключенные услуги для клиентов
    connected_services_data = [
        {
            'client': client1,
            'service': Service.objects.get(name='Интернет-банк'),
            'connected_at': timezone.now()
        },
        {
            'client': client1,
            'service': Service.objects.get(name='Мобильный банк'),
            'connected_at': timezone.now()
        },
        {
            'client': client1,
            'service': Service.objects.get(name='Быстрые переводы'),
            'connected_at': timezone.now()
        },
        {
            'client': client1,
            'service': Service.objects.get(name='VIP-зал'),
            'connected_at': timezone.now()
        }
    ]
    
    for connection_data in connected_services_data:
        ClientService.objects.create(
            client=connection_data['client'],
            service=connection_data['service'],
            connected_at=connection_data['connected_at']
        )
    
    # Создаем подключенные услуги для других клиентов
    if Client.objects.filter(user__username='client2').exists():
        client2 = Client.objects.get(user__username='client2')
        ClientService.objects.create(
            client=client2,
            service=Service.objects.get(name='Интернет-банк'),
            connected_at=timezone.now()
        )
        ClientService.objects.create(
            client=client2,
            service=Service.objects.get(name='Срочный депозит'),
            connected_at=timezone.now()
        )
    
    if Client.objects.filter(user__username='client3').exists():
        client3 = Client.objects.get(user__username='client3')
        ClientService.objects.create(
            client=client3,
            service=Service.objects.get(name='Мобильный банк'),
            connected_at=timezone.now()
        )
        ClientService.objects.create(
            client=client3,
            service=Service.objects.get(name='Потребительский кредит'),
            connected_at=timezone.now()
        )
        ClientService.objects.create(
            client=client3,
            service=Service.objects.get(name='Банковские карты'),
            connected_at=timezone.now()
        )

    print("\nДемо-данные успешно созданы!")
    print("Доступные аккаунты:")
    print("- Оператор ДБО #1: operator1 / password123")
    print("- Оператор ДБО #2: operator2 / password123")
    print("- Клиент ДБО: client1 / password123")
    print("- Клиент ДБО: client2 / password123")
    print("- Клиент ДБО: client3 / password123")
    print("- Клиент ДБО: client4 / password123 (не верифицирован)")
    print("- Клиент ДБО: client5 / password123 (не верифицирован)")
    print("\nСоздано:")
    print(f"- {Service.objects.count()} услуг")
    print(f"- {ServiceCategory.objects.count()} категорий услуг")
    print(f"- {Client.objects.count()} клиентов")
    print(f"- {PhishingEmail.objects.count()} фишинговых писем")
    print(f"- {ServiceRequest.objects.count()} заявок на услуги")
    print(f"- {ClientService.objects.count()} подключенных услуг")
    
    # Проверяем созданных пользователей
    print("\nПроверка пользователей:")
    for username in ['operator1', 'operator2', 'client1', 'client2', 'client3', 'client4', 'client5']:
        try:
            user = User.objects.get(username=username)
            print(f"✓ {username}: {user.username} (активен: {user.is_active})")
        except User.DoesNotExist:
            print(f"✗ {username}: не найден")
    
    # TODO: Добавить создание банковских программ в базе данных
    # Данные для банковских программ находятся в файле banking_programs_data.py
    # Необходимо создать модели для:
    # - Депозитных программ (deposit_programs)
    # - Кредитных программ (credit_programs)
    # - Инвестиционных продуктов (investment_products)
    # - Программ банковских карт (card_programs)
    # 
    # Эти данные были удалены из views.py и должны храниться в базе данных
    # для использования в функциях:
    # - deposits_view() в views.py
    # - credits_view() в views.py
    # - investments_view() в views.py
    # - cards_view() в views.py
    print("\n⚠️ ВНИМАНИЕ: Необходимо добавить создание банковских программ в базе данных")
    print("Данные находятся в файле: banking_programs_data.py")
    
    print("\nДемо-данные успешно созданы!")
    print("Доступные аккаунты:")
    print("- Оператор ДБО #1: operator1 / password123")
    print("- Оператор ДБО #2: operator2 / password123")
    print("- Клиент ДБО: client1 / password123")
    print("- Клиент ДБО: client2 / password123")
    print("- Клиент ДБО: client3 / password123")
    print("- Клиент ДБО: client4 / password123 (не верифицирован)")
    print("- Клиент ДБО: client5 / password123 (не верифицирован)")
    print("\nСоздано:")
    print(f"- {Service.objects.count()} услуг")
    print(f"- {ServiceCategory.objects.count()} категорий услуг")
    print(f"- {Client.objects.count()} клиентов")
    print(f"- {BankCard.objects.count()} банковских карт")
    print(f"- {Deposit.objects.count()} депозитов")
    print(f"- {Credit.objects.count()} кредитов")
    print(f"- {InvestmentProduct.objects.count()} инвестиционных продуктов")
    print(f"- {ClientInvestment.objects.count()} инвестиций клиентов")
    print(f"- {PhishingEmail.objects.count()} фишинговых писем")
    print(f"- {ServiceRequest.objects.count()} заявок на услуги")
    print(f"- {ClientService.objects.count()} подключенных услуг")
    print(f"- {News.objects.count()} новостей")
    
    # Проверяем созданных пользователей
    print("\nПроверка пользователей:")
    for username in ['operator1', 'operator2', 'client1', 'client2', 'client3', 'client4', 'client5']:
        try:
            user = User.objects.get(username=username)
            print(f"✓ {username}: {user.username} (активен: {user.is_active})")
        except User.DoesNotExist:
            print(f"✗ {username}: не найден")
    
    print("\n✅ Функционал основной карты:")
    print("- Первая карта каждого клиента автоматически становится основной")
    print("- Новые карты НЕ становятся основными автоматически")
    print("- Пользователь может вручную выбрать основную карту")
    print("- Только одна карта может быть основной одновременно")
    print("- Основная карта выделяется визуально на странице карт")
    
    # Создаем демо-новости для бегущей строки
    print("\n📰 Создание демо-новостей...")
    demo_news = [
        # Основные новости
        {
            'title': 'Новые тарифы на депозиты до 8% годовых!',
            'content': 'Специальное предложение для клиентов банка - депозиты с повышенной процентной ставкой.',
            'category': 'promotions',
            'priority': 5
        },
        {
            'title': 'USD/RUB: 95.50 | EUR/RUB: 102.30',
            'content': 'Актуальные курсы валют на сегодняшний день.',
            'category': 'rates',
            'priority': 4
        },
        {
            'title': 'Усилена безопасность интернет-банкинга',
            'content': 'Внедрены новые протоколы безопасности для защиты ваших средств.',
            'category': 'security',
            'priority': 5
        },
        {
            'title': 'Новая услуга: Мгновенные переводы 24/7',
            'content': 'Теперь вы можете переводить деньги в любое время суток.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Кэшбэк до 5% на все покупки картой',
            'content': 'Получайте кэшбэк за каждую покупку с нашей картой.',
            'category': 'promotions',
            'priority': 4
        },
        {
            'title': 'Система работает в штатном режиме',
            'content': 'Все банковские услуги доступны без ограничений.',
            'category': 'general',
            'priority': 2
        },
        {
            'title': 'Обновление мобильного приложения',
            'content': 'Новая версия приложения с улучшенным интерфейсом доступна для скачивания.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Инвестиционные продукты с доходностью до 12%',
            'content': 'Расширенная линейка инвестиционных продуктов для наших клиентов.',
            'category': 'promotions',
            'priority': 4
        },
        
        # Курсы валют
        {
            'title': 'GBP/RUB: 118.75 | CNY/RUB: 13.20',
            'content': 'Обновление курсов фунта стерлингов и китайского юаня.',
            'category': 'rates',
            'priority': 3
        },
        {
            'title': 'JPY/RUB: 0.65 | CHF/RUB: 108.90',
            'content': 'Курсы японской иены и швейцарского франка.',
            'category': 'rates',
            'priority': 3
        },
        {
            'title': 'AUD/RUB: 62.15 | CAD/RUB: 70.80',
            'content': 'Курсы австралийского и канадского долларов.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'BTC/RUB: 4,250,000 | ETH/RUB: 285,000',
            'content': 'Курсы криптовалют на текущий момент.',
            'category': 'rates',
            'priority': 4
        },
        {
            'title': 'TRY/RUB: 2.85 | BRL/RUB: 18.50',
            'content': 'Курсы турецкой лиры и бразильского реала.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'INR/RUB: 1.15 | KRW/RUB: 0.07',
            'content': 'Курсы индийской рупии и южнокорейской воны.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'MXN/RUB: 5.20 | ZAR/RUB: 5.15',
            'content': 'Курсы мексиканского песо и южноафриканского рэнда.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'NOK/RUB: 8.75 | SEK/RUB: 8.90',
            'content': 'Курсы норвежской и шведской крон.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'SGD/RUB: 70.25 | HKD/RUB: 12.15',
            'content': 'Курсы сингапурского доллара и гонконгского доллара.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'NZD/RUB: 58.90 | DKK/RUB: 14.75',
            'content': 'Курсы новозеландского доллара и датской кроны.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'PLN/RUB: 23.50 | CZK/RUB: 4.15',
            'content': 'Курсы польского злотого и чешской кроны.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'HUF/RUB: 0.28 | RON/RUB: 20.80',
            'content': 'Курсы венгерского форинта и румынского лея.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'BGN/RUB: 52.15 | HRK/RUB: 13.90',
            'content': 'Курсы болгарского лева и хорватской куны.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'Обновление курсов каждые 15 минут',
            'content': 'Актуальная информация о валютных курсах в режиме реального времени.',
            'category': 'rates',
            'priority': 2
        },
        {
            'title': 'Криптовалютные курсы в реальном времени',
            'content': 'Отслеживание курсов Bitcoin, Ethereum и других криптовалют.',
            'category': 'rates',
            'priority': 2
        },
        
        # Акции и предложения
        {
            'title': 'Ипотека от 3.5% годовых для молодых семей',
            'content': 'Специальная программа кредитования для семей с детьми.',
            'category': 'promotions',
            'priority': 5
        },
        {
            'title': 'Кредитные карты без процентов на 100 дней',
            'content': 'Льготный период для новых держателей кредитных карт.',
            'category': 'promotions',
            'priority': 4
        },
        {
            'title': 'Корпоративные карты с льготным обслуживанием',
            'content': 'Специальные условия для бизнес-клиентов банка.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Депозиты с возможностью пополнения',
            'content': 'Гибкие условия размещения средств с возможностью дополнительных взносов.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Кредит на образование под 2% годовых',
            'content': 'Льготное кредитование для получения высшего образования.',
            'category': 'promotions',
            'priority': 4
        },
        {
            'title': 'Программа лояльности для VIP-клиентов',
            'content': 'Эксклюзивные предложения и приоритетное обслуживание.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Скидка 50% на годовое обслуживание карт',
            'content': 'Ограниченное предложение для новых клиентов.',
            'category': 'promotions',
            'priority': 5
        },
        {
            'title': 'Бонус 10,000 рублей за открытие депозита',
            'content': 'Дополнительный бонус при размещении от 500,000 рублей.',
            'category': 'promotions',
            'priority': 5
        },
        {
            'title': 'Кредит на ремонт под 4.9% годовых',
            'content': 'Специальная программа кредитования для ремонта жилья.',
            'category': 'promotions',
            'priority': 4
        },
        {
            'title': 'Страхование путешествий со скидкой 30%',
            'content': 'Защитите свой отдых с выгодными условиями.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Депозит "Новогодний" до 9% годовых',
            'content': 'Праздничное предложение с повышенной доходностью.',
            'category': 'promotions',
            'priority': 4
        },
        {
            'title': 'Кэшбэк 7% на покупки в супермаркетах',
            'content': 'Увеличенный кэшбэк на продукты питания.',
            'category': 'promotions',
            'priority': 4
        },
        {
            'title': 'Ипотека для IT-специалистов от 2.9%',
            'content': 'Льготные условия кредитования для работников IT-сферы.',
            'category': 'promotions',
            'priority': 5
        },
        {
            'title': 'Бесплатное обслуживание счетов для пенсионеров',
            'content': 'Специальные условия для клиентов пенсионного возраста.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Кредитная карта с льготным периодом 120 дней',
            'content': 'Увеличенный льготный период для новых держателей карт.',
            'category': 'promotions',
            'priority': 4
        },
        {
            'title': 'Инвестиции в золото без комиссии',
            'content': 'Покупка золота через банк без дополнительных комиссий.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Страхование автомобиля со скидкой 40%',
            'content': 'КАСКО по специальной цене для клиентов банка.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Депозит "Студенческий" под 6% годовых',
            'content': 'Специальные условия для студентов и аспирантов.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Кредит на покупку техники без первоначального взноса',
            'content': 'Рассрочка на бытовую технику и электронику.',
            'category': 'promotions',
            'priority': 3
        },
        {
            'title': 'Бесплатное оформление виз',
            'content': 'Содействие в получении виз для путешествий.',
            'category': 'promotions',
            'priority': 2
        },
        {
            'title': 'Кэшбэк 15% на покупки в интернет-магазинах',
            'content': 'Увеличенный кэшбэк при оплате онлайн.',
            'category': 'promotions',
            'priority': 4
        },
        
        # Безопасность
        {
            'title': 'Двухфакторная аутентификация обязательна',
            'content': 'С 1 января все операции требуют подтверждения через SMS или приложение.',
            'category': 'security',
            'priority': 4
        },
        {
            'title': 'Страхование вкладов до 1.4 млн рублей',
            'content': 'Гарантированная защита ваших депозитов государством.',
            'category': 'security',
            'priority': 3
        },
        {
            'title': 'Блокировка подозрительных операций',
            'content': 'Система автоматически блокирует операции с признаками мошенничества.',
            'category': 'security',
            'priority': 4
        },
        {
            'title': 'Защита от фишинговых атак',
            'content': 'Система распознает и блокирует поддельные сайты и письма.',
            'category': 'security',
            'priority': 3
        },
        {
            'title': 'Автоматическое резервное копирование данных',
            'content': 'Ваши финансовые данные надежно защищены и регулярно сохраняются.',
            'category': 'security',
            'priority': 2
        },
        {
            'title': 'Новая система распознавания лиц',
            'content': 'Биометрическая защита для всех операций в интернет-банке.',
            'category': 'security',
            'priority': 4
        },
        {
            'title': 'Шифрование данных по стандарту AES-256',
            'content': 'Максимальная защита вашей персональной информации.',
            'category': 'security',
            'priority': 3
        },
        {
            'title': 'Мониторинг подозрительных операций 24/7',
            'content': 'Круглосуточный контроль за безопасностью ваших средств.',
            'category': 'security',
            'priority': 4
        },
        {
            'title': 'Защита от социальной инженерии',
            'content': 'Обучение клиентов распознаванию мошеннических схем.',
            'category': 'security',
            'priority': 3
        },
        {
            'title': 'Резервное копирование данных в трех центрах',
            'content': 'Географически распределенное хранение данных.',
            'category': 'security',
            'priority': 2
        },
        {
            'title': 'Сертификация по стандарту PCI DSS',
            'content': 'Соответствие международным стандартам безопасности.',
            'category': 'security',
            'priority': 3
        },
        {
            'title': 'Автоматическая блокировка при подозрительной активности',
            'content': 'Система мгновенно реагирует на угрозы безопасности.',
            'category': 'security',
            'priority': 4
        },
        {
            'title': 'Защищенный канал связи с банком',
            'content': 'Все соединения защищены протоколом TLS 1.3.',
            'category': 'security',
            'priority': 2
        },
        
        # Новые услуги
        {
            'title': 'Новая функция: Автоплатежи по расписанию',
            'content': 'Настройте автоматические платежи за коммунальные услуги.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Биометрическая авторизация в мобильном банке',
            'content': 'Вход в приложение теперь возможен по отпечатку пальца или лицу.',
            'category': 'services',
            'priority': 4
        },
        {
            'title': 'Новая услуга: Консультации по инвестициям',
            'content': 'Персональные консультации с финансовыми экспертами.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Мультивалютные счета для бизнеса',
            'content': 'Ведение операций в различных валютах в одном счете.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Система уведомлений о операциях',
            'content': 'Мгновенные уведомления о всех операциях по вашим счетам.',
            'category': 'services',
            'priority': 2
        },
        {
            'title': 'Интеграция с популярными платежными системами',
            'content': 'Возможность оплаты через Apple Pay, Google Pay и Samsung Pay.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Услуга "Финансовый консультант"',
            'content': 'Персональные рекомендации по управлению финансами.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Мультивалютный кошелек в мобильном приложении',
            'content': 'Управление средствами в разных валютах в одном интерфейсе.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Автоматическое инвестирование с ИИ',
            'content': 'Искусственный интеллект поможет увеличить доходность.',
            'category': 'services',
            'priority': 4
        },
        {
            'title': 'Услуга "Семейный бюджет"',
            'content': 'Контроль расходов всех членов семьи в одном приложении.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Интеграция с налоговой службой',
            'content': 'Автоматическая подача налоговых деклараций.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Услуга "Цифровой нотариус"',
            'content': 'Электронное заверение документов с юридической силой.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Программа лояльности "Банк-бонусы"',
            'content': 'Накопительная система бонусов за использование услуг.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Услуга "Финансовая грамотность"',
            'content': 'Обучающие курсы и материалы по финансовому планированию.',
            'category': 'services',
            'priority': 2
        },
        {
            'title': 'Интеграция с умным домом',
            'content': 'Управление коммунальными платежами через IoT-устройства.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Услуга "Цифровое наследство"',
            'content': 'Безопасная передача цифровых активов наследникам.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Услуга "Цифровой паспорт"',
            'content': 'Электронное хранение важных документов.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Интеграция с системами учета бизнеса',
            'content': 'Автоматическая синхронизация с 1С и другими системами.',
            'category': 'services',
            'priority': 3
        },
        {
            'title': 'Услуга "Финансовый планировщик"',
            'content': 'Помощь в составлении личного финансового плана.',
            'category': 'services',
            'priority': 2
        },
        {
            'title': 'Мультиязычная поддержка клиентов',
            'content': 'Обслуживание на 15 языках мира.',
            'category': 'services',
            'priority': 2
        },
        {
            'title': 'Услуга "Цифровой архив"',
            'content': 'Безопасное хранение важных документов в облаке.',
            'category': 'services',
            'priority': 2
        },
        
        # Общие новости
        {
            'title': 'Техническое обслуживание завершено',
            'content': 'Все системы восстановлены и работают в полном объеме.',
            'category': 'general',
            'priority': 2
        },
        {
            'title': 'Банк вошел в ТОП-10 по надежности',
            'content': 'Рейтинг ведущих рейтинговых агентств.',
            'category': 'general',
            'priority': 3
        },
        {
            'title': 'Открытие нового офиса в центре города',
            'content': 'Современный офис с цифровыми технологиями.',
            'category': 'general',
            'priority': 2
        },
        {
            'title': 'Банк получил награду "Лучший цифровой банк"',
            'content': 'Признание инноваций в области цифровых технологий.',
            'category': 'general',
            'priority': 3
        },
        {
            'title': 'Расширение сети банкоматов',
            'content': 'Новые точки обслуживания в жилых районах.',
            'category': 'general',
            'priority': 2
        },
        {
            'title': 'Партнерство с ведущими технологическими компаниями',
            'content': 'Совместные проекты по развитию финтеха.',
            'category': 'general',
            'priority': 2
        },
        {
            'title': 'Банк поддерживает экологические инициативы',
            'content': 'Инвестиции в зеленые технологии и устойчивое развитие.',
            'category': 'general',
            'priority': 2
        },
        {
            'title': 'Новая штаб-квартира с современными технологиями',
            'content': 'Умное здание с системами автоматизации.',
            'category': 'general',
            'priority': 2
        },
        {
            'title': 'Банк запустил программу поддержки стартапов',
            'content': 'Финансирование инновационных проектов.',
            'category': 'general',
            'priority': 3
        },
        {
            'title': 'Расширение команды IT-специалистов',
            'content': 'Привлечение лучших разработчиков для развития платформы.',
            'category': 'general',
            'priority': 2
        },
        {
            'title': 'Банк стал партнером международной платежной системы',
            'content': 'Интеграция с глобальными финансовыми сетями.',
            'category': 'general',
            'priority': 3
        }
    ]
    
    for news_data in demo_news:
        news, created = News.objects.get_or_create(
            title=news_data['title'],
            defaults={
                'content': news_data['content'],
                'category': news_data['category'],
                'priority': news_data['priority'],
                'is_active': True
            }
        )
        if created:
            print(f"  ✓ Создана новость: {news.title}")
        else:
            print(f"  - Новость уже существует: {news.title}")
    
    print(f"📰 Создано новостей: {News.objects.count()}")
    
    # Создаем инвестиционные продукты
    print("\n💼 Создание инвестиционных продуктов...")
    investment_products_data = [
        {
            'name': 'Консервативный портфель',
            'description': 'Низкорисковые инвестиции в государственные облигации',
            'product_type': 'brokerage',
            'min_amount': Decimal('10000.00'),
            'risk_level': 'low',
            'expected_return': Decimal('6.50')
        },
        {
            'name': 'Сбалансированный портфель',
            'description': 'Смешанные инвестиции в акции и облигации',
            'product_type': 'brokerage',
            'min_amount': Decimal('50000.00'),
            'risk_level': 'medium',
            'expected_return': Decimal('9.20')
        },
        {
            'name': 'Агрессивный портфель',
            'description': 'Высокодоходные инвестиции в акции роста',
            'product_type': 'brokerage',
            'min_amount': Decimal('100000.00'),
            'risk_level': 'high',
            'expected_return': Decimal('12.80')
        },
        {
            'name': 'ИИС "Доходный"',
            'description': 'Индивидуальный инвестиционный счет с налоговыми льготами',
            'product_type': 'iis',
            'min_amount': Decimal('400000.00'),
            'risk_level': 'medium',
            'expected_return': Decimal('8.50')
        },
        {
            'name': 'ПИФ "Золотой стандарт"',
            'description': 'Паевой инвестиционный фонд золота',
            'product_type': 'pif',
            'min_amount': Decimal('25000.00'),
            'risk_level': 'medium',
            'expected_return': Decimal('7.80')
        }
    ]
    
    for product_data in investment_products_data:
        InvestmentProduct.objects.get_or_create(
            name=product_data['name'],
            defaults=product_data
        )
    
    print(f"💼 Создано инвестиционных продуктов: {InvestmentProduct.objects.count()}")
    
    # Создаем демо-депозиты для клиентов
    print("\n💰 Создание демо-депозитов...")
    if Client.objects.filter(user__username='client1').exists():
        client1 = Client.objects.get(user__username='client1')
        primary_card = client1.primary_card
        
        if primary_card:
            from datetime import date, timedelta
            start_date = date.today()
            end_date = start_date + timedelta(days=365)  # 1 год
            
            Deposit.objects.get_or_create(
                client=client1,
                card=primary_card,
                defaults={
                    'amount': Decimal('500000.00'),
                    'interest_rate': Decimal('7.50'),
                    'term_months': 12,
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_active': True
                }
            )
            print(f"Создан депозит для {client1.full_name}: 500,000 ₽ под 7.5% на 12 месяцев")
    
    print(f"💰 Создано депозитов: {Deposit.objects.count()}")
    
    # Создаем демо-кредиты для клиентов
    print("\n💳 Создание демо-кредитов...")
    if Client.objects.filter(user__username='client2').exists():
        client2 = Client.objects.get(user__username='client2')
        
        from datetime import date, timedelta
        start_date = date.today()
        end_date = start_date + timedelta(days=365*3)  # 3 года
        
        Credit.objects.get_or_create(
            client=client2,
            defaults={
                'amount': Decimal('300000.00'),
                'interest_rate': Decimal('12.50'),
                'term_months': 36,
                'monthly_payment': Decimal('10000.00'),
                'remaining_amount': Decimal('300000.00'),
                'status': 'active',
                'start_date': start_date,
                'end_date': end_date
            }
        )
        print(f"Создан кредит для {client2.full_name}: 300,000 ₽ под 12.5% на 36 месяцев")
    
    print(f"💳 Создано кредитов: {Credit.objects.count()}")
    
    # Создаем демо-инвестиции для клиентов
    print("\n📈 Создание демо-инвестиций...")
    if Client.objects.filter(user__username='client3').exists():
        client3 = Client.objects.get(user__username='client3')
        conservative_product = InvestmentProduct.objects.filter(risk_level='low').first()
        
        if conservative_product:
            from datetime import date
            ClientInvestment.objects.get_or_create(
                client=client3,
                product=conservative_product,
                defaults={
                    'amount': Decimal('100000.00'),
                    'current_value': Decimal('105000.00'),  # +5% роста
                    'purchase_date': date.today() - timedelta(days=90),
                    'status': 'active'
                }
            )
            print(f"Создана инвестиция для {client3.full_name}: 100,000 ₽ в консервативный портфель")
    
    print(f"📈 Создано инвестиций: {ClientInvestment.objects.count()}")
    
    # Создаем дополнительные карты для демонстрации функционала основной карты
    print("\n💳 Создание дополнительных карт...")
    if Client.objects.filter(user__username='client1').exists():
        try:
            client1 = Client.objects.get(user__username='client1')
            
            # Создаем кредитную карту (НЕ основную)
            from datetime import date, timedelta
            expiry_date = date.today() + timedelta(days=365*3)
            
            credit_card = BankCard.objects.create(
                client=client1,
                card_number="5300001099910004312",
                card_type='credit',
                balance=Decimal('0.00'),
                currency='RUB',
                expiry_date=expiry_date,
                is_active=True
            )
            print(f"Создана кредитная карта для {client1.full_name}: {credit_card.card_number} (НЕ основная)")
        except Exception as e:
            print(f"Ошибка при создании дополнительной карты: {e}")
    
    print(f"💳 Всего создано карт: {BankCard.objects.count()}")
    
    # Показываем статистику по основным картам
    clients_with_primary = Client.objects.filter(primary_card__isnull=False).count()
    print(f"👑 Клиентов с основной картой: {clients_with_primary}")
    
    for client in Client.objects.filter(primary_card__isnull=False):
        print(f"  - {client.full_name}: {client.primary_card.card_number} ({client.primary_card.card_type})")

    # --------------------
    # Демо-транзакции между клиентами
    # --------------------
    try:
        print("\n💸 Создание демо-транзакций...")
        from decimal import Decimal as D
        import random
        from datetime import timedelta

        # Очищаем старые транзакции перед созданием новых
        # Это гарантирует, что транзакции будут распределены между всеми клиентами
        old_transactions_count = Transaction.objects.count()
        if old_transactions_count > 0:
            print(f"🗑️  Удаление старых транзакций ({old_transactions_count} шт.)...")
            Transaction.objects.all().delete()
            print("✅ Старые транзакции удалены")

        # Получаем всех активных клиентов (убеждаемся, что все клиенты уже созданы)
        demo_clients = list(Client.objects.filter(is_active=True).order_by('id'))
        
        # Убеждаемся, что у всех клиентов есть хотя бы одна активная карта
        print("🔍 Проверка наличия карт у клиентов...")
        from datetime import date, timedelta
        for client in demo_clients:
            client_cards = BankCard.objects.filter(client=client, is_active=True)
            if not client_cards.exists():
                print(f"   ⚠️  У клиента {client.full_name} нет активных карт, создаем...")
                expiry_date = date.today() + timedelta(days=365*5)  # Карта действует 5 лет
                
                # Генерируем номер карты максимум 19 символов
                # Формат: 40817 (5) + client.id (5 цифр) + случайные цифры (9) = 19 символов
                client_id_num = client.id % 100000  # Берем последние 5 цифр ID
                base_number = f"40817{client_id_num:05d}"  # Всего 10 символов
                # Дополняем до 19 символов случайными цифрами
                import random
                remaining_digits = 19 - len(base_number)  # 9 символов
                random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
                card_number = base_number + random_suffix  # Всего 19 символов
                
                # Проверяем уникальность и генерируем новый номер, если нужно
                suffix = 0
                original_card_number = card_number
                while BankCard.objects.filter(card_number=card_number).exists():
                    suffix += 1
                    # Заменяем последние 4 цифры на суффикс
                    suffix_str = str(suffix % 10000).zfill(4)
                    card_number = original_card_number[:-4] + suffix_str
                    if suffix > 1000:  # Защита от бесконечного цикла
                        # Используем timestamp для уникальности
                        import time
                        timestamp = str(int(time.time()))[-6:]
                        card_number = f"40817{client_id_num:05d}{timestamp}"[:19]
                        break
                
                # Проверяем, не существует ли уже карта с таким номером
                if not BankCard.objects.filter(card_number=card_number).exists():
                    card = BankCard.objects.create(
                        client=client,
                        card_number=card_number,
                        card_type='debit',
                        balance=D('50000.00'),  # Начальный баланс
                        currency='RUB',
                        expiry_date=expiry_date,
                        is_active=True
                    )
                    # Если у клиента нет основной карты, делаем эту карту основной
                    if not client.primary_card:
                        client.primary_card = card
                        client.save(update_fields=['primary_card'])
                    print(f"   ✅ Создана карта для {client.full_name}: {card.card_number}")
                else:
                    print(f"   ⚠️  Карта с номером {card_number} уже существует")
        
        # Получаем все активные карты всех клиентов
        all_cards = list(BankCard.objects.filter(client__in=demo_clients, is_active=True))
        
        # Проверяем, что у нас есть хотя бы 2 клиента с картами
        if len(demo_clients) >= 2 and len(all_cards) >= 2:
            print(f"📊 Найдено клиентов: {len(demo_clients)}")
            print(f"💳 Найдено карт: {len(all_cards)}")
            for client in demo_clients:
                client_cards = [c for c in all_cards if c.client.id == client.id]
                print(f"   - {client.full_name}: {len(client_cards)} карт(ы)")
            # Используем все активные карты
            cards = all_cards
            
            # Сначала пополняем балансы всех карт для обеспечения достаточных средств
            print("💰 Пополнение балансов карт для транзакций...")
            for card in cards:
                if card.balance < D('50000.00'):
                    # Пополняем до минимум 50000 для возможности транзакций
                    additional_balance = D('50000.00') - card.balance
                    card.balance += additional_balance
                    card.save(update_fields=['balance'])
            
            # Разнообразные суммы для разных типов транзакций (еще более расширенный список)
            transfer_amounts = [
                D('50.00'), D('100.00'), D('150.00'), D('200.00'), D('250.50'), D('300.00'), D('350.00'), 
                D('450.00'), D('499.99'), D('600.00'), D('750.00'), D('900.00'), D('1200.00'), D('1500.00'), 
                D('1800.00'), D('2200.00'), D('2500.00'), D('3000.00'), D('3500.00'), D('4000.00'), 
                D('5000.00'), D('6000.00'), D('7500.00'), D('8500.00'), D('10000.00'), D('12000.00'), 
                D('15000.00'), D('18000.00'), D('20000.00'), D('25000.00'), D('30000.00'), D('35000.00')
            ]
            payment_amounts = [
                D('15.00'), D('25.00'), D('35.00'), D('50.00'), D('75.00'), D('100.00'), D('125.00'), 
                D('150.00'), D('200.00'), D('250.00'), D('300.00'), D('400.00'), D('500.00'), D('600.00'), 
                D('750.00'), D('900.00'), D('1000.00'), D('1200.00'), D('1500.00'), D('1800.00'), 
                D('2000.00'), D('2500.00'), D('3000.00'), D('4000.00'), D('5000.00')
            ]
            deposit_amounts = [
                D('300.00'), D('500.00'), D('750.00'), D('1000.00'), D('1500.00'), D('2000.00'), 
                D('2500.00'), D('3000.00'), D('4000.00'), D('5000.00'), D('6000.00'), D('7500.00'), 
                D('8500.00'), D('10000.00'), D('12000.00'), D('15000.00'), D('18000.00'), D('20000.00'), 
                D('25000.00'), D('30000.00'), D('40000.00'), D('50000.00'), D('75000.00'), D('100000.00')
            ]
            withdrawal_amounts = [
                D('100.00'), D('200.00'), D('300.00'), D('400.00'), D('500.00'), D('600.00'), 
                D('750.00'), D('900.00'), D('1000.00'), D('1200.00'), D('1500.00'), D('1800.00'), 
                D('2000.00'), D('2500.00'), D('3000.00'), D('4000.00'), D('5000.00'), D('6000.00'), 
                D('7500.00'), D('10000.00'), D('15000.00'), D('20000.00')
            ]
            # Описания для разных типов транзакций
            transfer_descriptions = [
                "Перевод между счетами",
                "Перевод другу",
                "Возврат долга",
                "Оплата услуг",
                "Перевод на основной счет",
            ]
            payment_descriptions = [
                "Оплата интернет-магазина",
                "Оплата коммунальных услуг",
                "Оплата мобильной связи",
                "Оплата подписки",
                "Оплата заказа",
                "Оплата услуг",
            ]
            deposit_descriptions = [
                "Пополнение счета",
                "Зарплата",
                "Возврат средств",
                "Пополнение через банкомат",
                "Пополнение онлайн",
            ]
            withdrawal_descriptions = [
                "Снятие наличных",
                "Снятие в банкомате",
                "Снятие в отделении банка",
            ]
            
            created_count = 0
            transaction_types_created = {'transfer': 0, 'payment': 0, 'deposit': 0, 'withdrawal': 0}
            
            # Группируем карты по клиентам для равномерного распределения
            cards_by_client = {}
            for card in cards:
                client_id = card.client.id
                if client_id not in cards_by_client:
                    cards_by_client[client_id] = []
                cards_by_client[client_id].append(card)
            
            client_ids = list(cards_by_client.keys())
            
            # Проверяем, что у нас есть карты для всех клиентов
            if len(client_ids) < len(demo_clients):
                print(f"⚠️  Предупреждение: не все клиенты имеют карты!")
                print(f"   Клиентов: {len(demo_clients)}, Клиентов с картами: {len(client_ids)}")
                for client in demo_clients:
                    if client.id not in client_ids:
                        print(f"   - {client.full_name} не имеет карт!")
            
            print(f"💳 Клиентов с картами для транзакций: {len(client_ids)}")
            if len(client_ids) == 0:
                print("❌ Ошибка: нет клиентов с картами для создания транзакций!")
                return
            if len(client_ids) < len(demo_clients):
                print(f"⚠️  Внимание: только {len(client_ids)} из {len(demo_clients)} клиентов имеют карты")
                print("   Транзакции будут созданы только для клиентов с картами")
            
            # Создаем разнообразные транзакции с равномерным распределением между клиентами
            # 1. Переводы между клиентами (150 транзакций) - гарантируем участие всех клиентов
            print("💸 Создание переводов между клиентами...")
            
            # Создаем список всех возможных пар клиентов для равномерного распределения
            client_pairs = []
            for from_id in client_ids:
                for to_id in client_ids:
                    if from_id != to_id:
                        client_pairs.append((from_id, to_id))
            
            if len(client_pairs) == 0:
                print("⚠️  Невозможно создать переводы: недостаточно клиентов")
            else:
                # Гарантируем, что каждая пара используется минимум один раз
                # Затем заполняем оставшиеся транзакции случайными парами
                transfers_to_create = 150
                transfer_pairs = []
                
                # Сначала добавляем каждую пару минимум один раз
                for pair in client_pairs:
                    transfer_pairs.append(pair)
                
                # Затем добавляем случайные пары до достижения нужного количества
                remaining_transfers = transfers_to_create - len(transfer_pairs)
                for _ in range(remaining_transfers):
                    transfer_pairs.append(random.choice(client_pairs))
                
                # Перемешиваем для случайности
                random.shuffle(transfer_pairs)
                
                transfer_attempts = 0
                max_transfer_attempts = len(transfer_pairs) * 3  # Увеличиваем лимит попыток
                
                for from_client_id, to_client_id in transfer_pairs:
                    if transaction_types_created['transfer'] >= transfers_to_create:
                        break
                    
                    transfer_attempts += 1
                    if transfer_attempts > max_transfer_attempts:
                        print(f"⚠️  Достигнут лимит попыток для переводов ({max_transfer_attempts})")
                        break
                    
                    from_client_cards = cards_by_client.get(from_client_id, [])
                    to_client_cards = cards_by_client.get(to_client_id, [])
                    
                    if not from_client_cards or not to_client_cards:
                        continue
                    
                    from_card = random.choice(from_client_cards)
                    to_card = random.choice(to_client_cards)
                    
                    amount = random.choice(transfer_amounts)
                    if from_card.balance >= amount:
                        from_card.balance -= amount
                        to_card.balance += amount
                        from_card.save(update_fields=['balance'])
                        to_card.save(update_fields=['balance'])

                        # Создаем случайную дату в диапазоне последних 90 дней для большей разнобойности
                        days_ago = random.randint(0, 90)
                        hours_ago = random.randint(0, 23)
                        minutes_ago = random.randint(0, 59)
                        seconds_ago = random.randint(0, 59)
                        transaction_time = timezone.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago)

                        Transaction.objects.create(
                            from_card=from_card,
                            to_card=to_card,
                            amount=amount,
                            currency='RUB',
                            transaction_type='transfer',
                            description=random.choice(transfer_descriptions),
                            status='completed',
                            created_at=transaction_time,
                            completed_at=transaction_time + timedelta(minutes=random.randint(1, 5)),
                        )
                        created_count += 1
                        transaction_types_created['transfer'] += 1

            # 2. Платежи (60 транзакций) - распределяем между всеми клиентами равномерно
            print("💳 Создание платежей...")
            # Гарантируем, что каждый клиент получит минимум несколько платежей
            payments_per_client = max(1, 60 // len(client_ids) if client_ids else 1)
            payment_clients = []
            # Сначала гарантируем минимум по одному платежу для каждого клиента
            for client_id in client_ids:
                payment_clients.extend([client_id] * payments_per_client)
            # Добавляем случайные платежи для оставшихся
            remaining_payments = 60 - len(payment_clients)
            if remaining_payments > 0:
                payment_clients.extend([random.choice(client_ids) for _ in range(remaining_payments)])
            random.shuffle(payment_clients)
            
            for client_id in payment_clients:
                if transaction_types_created['payment'] >= 60:
                    break
                client_cards = cards_by_client.get(client_id, [])
                if not client_cards:
                    continue
                from_card = random.choice(client_cards)
                amount = random.choice(payment_amounts)
                if from_card.balance >= amount:
                    from_card.balance -= amount
                    from_card.save(update_fields=['balance'])

                    # Создаем случайную дату в диапазоне последних 30 дней
                    days_ago = random.randint(0, 30)
                    hours_ago = random.randint(0, 23)
                    minutes_ago = random.randint(0, 59)
                    transaction_time = timezone.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

                    Transaction.objects.create(
                        from_card=from_card,
                        to_card=None,
                        amount=amount,
                        currency='RUB',
                        transaction_type='payment',
                        description=random.choice(payment_descriptions),
                        status='completed',
                        created_at=transaction_time,
                        completed_at=transaction_time + timedelta(minutes=random.randint(1, 5)),
                    )
                    created_count += 1
                    transaction_types_created['payment'] += 1

            # 3. Пополнения (50 транзакций) - распределяем между всеми клиентами равномерно
            print("💰 Создание пополнений...")
            # Гарантируем, что каждый клиент получит минимум несколько пополнений
            deposits_per_client = max(1, 50 // len(client_ids) if client_ids else 1)
            deposit_clients = []
            # Сначала гарантируем минимум по одному пополнению для каждого клиента
            for client_id in client_ids:
                deposit_clients.extend([client_id] * deposits_per_client)
            # Добавляем случайные пополнения для оставшихся
            remaining_deposits = 50 - len(deposit_clients)
            if remaining_deposits > 0:
                deposit_clients.extend([random.choice(client_ids) for _ in range(remaining_deposits)])
            random.shuffle(deposit_clients)
            
            for client_id in deposit_clients:
                if transaction_types_created['deposit'] >= 50:
                    break
                client_cards = cards_by_client.get(client_id, [])
                if not client_cards:
                    continue
                to_card = random.choice(client_cards)
                amount = random.choice(deposit_amounts)
                to_card.balance += amount
                to_card.save(update_fields=['balance'])

                # Создаем случайную дату в диапазоне последних 30 дней
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                transaction_time = timezone.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

                Transaction.objects.create(
                    from_card=None,
                    to_card=to_card,
                    amount=amount,
                    currency='RUB',
                    transaction_type='deposit',
                    description=random.choice(deposit_descriptions),
                    status='completed',
                    created_at=transaction_time,
                    completed_at=transaction_time + timedelta(minutes=random.randint(1, 5)),
                )
                created_count += 1
                transaction_types_created['deposit'] += 1

            # 4. Снятия наличных (40 транзакций) - распределяем между всеми клиентами равномерно
            print("💵 Создание снятий наличных...")
            # Гарантируем, что каждый клиент делает минимум несколько снятий
            withdrawals_per_client = max(1, 40 // len(client_ids) if client_ids else 1)
            withdrawal_clients = []
            # Сначала гарантируем минимум по одному снятию для каждого клиента
            for client_id in client_ids:
                withdrawal_clients.extend([client_id] * withdrawals_per_client)
            # Добавляем случайные снятия для оставшихся
            remaining_withdrawals = 40 - len(withdrawal_clients)
            if remaining_withdrawals > 0:
                withdrawal_clients.extend([random.choice(client_ids) for _ in range(remaining_withdrawals)])
            random.shuffle(withdrawal_clients)
            
            for client_id in withdrawal_clients:
                if transaction_types_created['withdrawal'] >= 40:
                    break
                client_cards = cards_by_client.get(client_id, [])
                if not client_cards:
                    continue
                from_card = random.choice(client_cards)
                amount = random.choice(withdrawal_amounts)
                if from_card.balance >= amount:
                    from_card.balance -= amount
                    from_card.save(update_fields=['balance'])

                    # Создаем случайную дату в диапазоне последних 30 дней
                    days_ago = random.randint(0, 30)
                    hours_ago = random.randint(0, 23)
                    minutes_ago = random.randint(0, 59)
                    transaction_time = timezone.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

                    Transaction.objects.create(
                        from_card=from_card,
                        to_card=None,
                        amount=amount,
                        currency='RUB',
                        transaction_type='withdrawal',
                        description=random.choice(withdrawal_descriptions),
                        status='completed',
                        created_at=transaction_time,
                        completed_at=transaction_time + timedelta(minutes=random.randint(1, 5)),
                    )
                    created_count += 1
                    transaction_types_created['withdrawal'] += 1

            # 5. Комиссии (30 транзакций) - распределяем между всеми клиентами равномерно
            print("💸 Создание комиссий...")
            # Гарантируем, что каждый клиент платит минимум несколько комиссий
            fees_per_client = max(1, 30 // len(client_ids) if client_ids else 1)
            fee_clients = []
            # Сначала гарантируем минимум по одной комиссии для каждого клиента
            for client_id in client_ids:
                fee_clients.extend([client_id] * fees_per_client)
            # Добавляем случайные комиссии для оставшихся
            remaining_fees = 30 - len(fee_clients)
            if remaining_fees > 0:
                fee_clients.extend([random.choice(client_ids) for _ in range(remaining_fees)])
            random.shuffle(fee_clients)
            
            for client_id in fee_clients:
                if transaction_types_created['fee'] >= 30:
                    break
                client_cards = cards_by_client.get(client_id, [])
                if not client_cards:
                    continue
                from_card = random.choice(client_cards)
                amount = random.choice(fee_amounts)
                if from_card.balance >= amount:
                    from_card.balance -= amount
                    from_card.save(update_fields=['balance'])

                    # Создаем случайную дату в диапазоне последних 30 дней
                    days_ago = random.randint(0, 30)
                    hours_ago = random.randint(0, 23)
                    minutes_ago = random.randint(0, 59)
                    transaction_time = timezone.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

                    Transaction.objects.create(
                        from_card=from_card,
                        to_card=None,
                        amount=amount,
                        currency='RUB',
                        transaction_type='fee',
                        description=random.choice(fee_descriptions),
                        status='completed',
                        created_at=transaction_time,
                        completed_at=transaction_time + timedelta(minutes=random.randint(1, 5)),
                    )
                    created_count += 1
                    transaction_types_created['fee'] += 1

            print(f"✅ Создано демо-транзакций: {created_count}")
            print(f"   - Переводы: {transaction_types_created['transfer']}")
            print(f"   - Платежи: {transaction_types_created['payment']}")
            print(f"   - Пополнения: {transaction_types_created['deposit']}")
            print(f"   - Снятия: {transaction_types_created['withdrawal']}")
            print(f"   - Комиссии: {transaction_types_created['fee']}")
            
            # Проверяем распределение транзакций по клиентам
            print("\n📊 Распределение транзакций по клиентам:")
            from django.db.models import Q
            total_by_client = {}
            for client in demo_clients:
                # Подсчитываем транзакции, где клиент является отправителем
                outgoing = Transaction.objects.filter(from_card__client=client).count()
                # Подсчитываем транзакции, где клиент является получателем
                incoming = Transaction.objects.filter(to_card__client=client).count()
                # Общее количество уникальных транзакций (учитываем, что переводы учитываются дважды)
                all_transactions = Transaction.objects.filter(
                    Q(from_card__client=client) | Q(to_card__client=client)
                ).count()
                
                # Детальная статистика по типам
                transfers_out = Transaction.objects.filter(from_card__client=client, transaction_type='transfer').count()
                transfers_in = Transaction.objects.filter(to_card__client=client, transaction_type='transfer').count()
                payments = Transaction.objects.filter(from_card__client=client, transaction_type='payment').count()
                deposits = Transaction.objects.filter(to_card__client=client, transaction_type='deposit').count()
                withdrawals = Transaction.objects.filter(from_card__client=client, transaction_type='withdrawal').count()
                
                total_by_client[client.id] = all_transactions
                
                print(f"   - {client.full_name}: {all_transactions} транзакций")
                print(f"     ├─ Исходящие: {outgoing} (переводы: {transfers_out}, платежи: {payments}, снятия: {withdrawals})")
                print(f"     └─ Входящие: {incoming} (переводы: {transfers_in}, пополнения: {deposits})")
            
            # Проверяем равномерность распределения
            if total_by_client:
                min_transactions = min(total_by_client.values())
                max_transactions = max(total_by_client.values())
                avg_transactions = sum(total_by_client.values()) / len(total_by_client)
                print(f"\n📈 Статистика распределения:")
                print(f"   - Минимум: {min_transactions} транзакций")
                print(f"   - Максимум: {max_transactions} транзакций")
                print(f"   - Среднее: {avg_transactions:.1f} транзакций")
                if max_transactions - min_transactions > avg_transactions * 0.5:
                    print(f"   ⚠️  Внимание: распределение неравномерное (разница: {max_transactions - min_transactions})")
                else:
                    print(f"   ✅ Распределение достаточно равномерное")
        else:
            print("⚠️ Недостаточно активных клиентов или карт для создания транзакций")
    except Exception as e:
        print(f"Ошибка при создании демо-транзакций: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        create_demo_data()
        print("\n✅ Инициализация демо-данных завершена успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка при инициализации демо-данных: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
