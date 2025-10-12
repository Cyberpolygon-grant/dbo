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
from dbo.models import Operator, Client, ServiceCategory, Service, PhishingEmail, ServiceRequest, ClientService, News

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
            'phone': '+7 (999) 123-45-67',
            'is_active': True,
            'is_verified': True,
            'created_by': operator1
        }
    )
    if created:
        print("Создан клиент ДБО")
    
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
            'phone': '+7 (999) 234-56-78',
            'is_verified': True
        },
        {
            'username': 'client3',
            'password': 'password123',
            'email': 'client3@example.com',
            'first_name': 'Алексей',
            'last_name': 'Козлов',
            'client_id': 'CLI003',
            'full_name': 'Алексей Козлов',
            'phone': '+7 (999) 345-67-89',
            'is_verified': True
        },
        {
            'username': 'client4',
            'password': 'password123',
            'email': 'client4@example.com',
            'first_name': 'Елена',
            'last_name': 'Морозова',
            'client_id': 'CLI004',
            'full_name': 'Елена Морозова',
            'phone': '+7 (999) 456-78-90',
            'is_verified': False
        },
        {
            'username': 'client5',
            'password': 'password123',
            'email': 'client5@example.com',
            'first_name': 'Дмитрий',
            'last_name': 'Волков',
            'client_id': 'CLI005',
            'full_name': 'Дмитрий Волков',
            'phone': '+7 (999) 567-89-01',
            'is_verified': False
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
        
        Client.objects.get_or_create(
            user=user,
            defaults={
                'client_id': client_data['client_id'],
                'full_name': client_data['full_name'],
                'email': client_data['email'],
                'phone': client_data['phone'],
                'is_active': True,
                'is_verified': client_data['is_verified'],
                'created_by': operator1
            }
        )

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
    
    # Создаем демо-новости для бегущей строки
    print("\n📰 Создание демо-новостей...")
    from dbo.models import News
    
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

if __name__ == '__main__':
    create_demo_data()
