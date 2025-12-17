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
from django.db import connection
from dbo.models import Operator, Client, ServiceCategory, Service, ServiceRequest, ClientService, News, BankCard, Transaction, Deposit, Credit, InvestmentProduct, ClientInvestment

def check_tables_exist():
    """Проверяет, что необходимые таблицы существуют"""
    try:
        # Простая проверка - пытаемся выполнить запрос к таблице auth_user
        from django.contrib.auth.models import User
        User.objects.count()  # Если таблица не существует, будет ошибка
        return True
    except Exception as e:
        error_msg = str(e)
        if 'does not exist' in error_msg or 'relation' in error_msg.lower():
            # Проверяем, что это действительно ошибка отсутствия таблицы, а не записи
            if 'matching query does not exist' not in error_msg.lower():
                print(f"⚠️  Таблицы не существуют: {error_msg}")
                print("💡 Убедитесь, что миграции применены: python manage.py migrate")
                return False
        # Другие ошибки пропускаем (например, проблемы с подключением)
        return True

def create_demo_data():
    print("Создание демо-данных...")
    
    # Проверяем наличие необходимых таблиц
    if not check_tables_exist():
        print("❌ Ошибка: таблицы не существуют. Применяем миграции...")
        import subprocess
        import sys
        try:
            result = subprocess.run(
                ['python', 'manage.py', 'migrate', '--noinput'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                print(f"❌ Ошибка применения миграций: {result.stderr}")
                raise Exception("Не удалось применить миграции")
            print("✅ Миграции применены успешно!")
            # Повторная проверка
            if not check_tables_exist():
                raise Exception("Таблицы все еще не существуют после применения миграций")
        except subprocess.TimeoutExpired:
            raise Exception("Таймаут при применении миграций")
        except Exception as e:
            raise Exception(f"Не удалось применить миграции: {e}")
    
    # Создаем пользователей
    # Оператор ДБО #1
    user1, created = User.objects.get_or_create(
        username='operator1',
        defaults={'email': 'operator1@financepro.ru', 'first_name': 'Анна', 'last_name': 'Петрова'}
    )
    if created:
        user1.set_password('1q2w#E$R')
        user1.save()
        print("Создан пользователь operator1")
    
    operator1, created = Operator.objects.get_or_create(
        user=user1,
        defaults={
            'operator_type': 'client_service',
            'email': 'operator1@financepro.ru',
            'is_active': True
        }
    )
    if created:
        print("Создан оператор ДБО #1")
    
    # Оператор ДБО #2
    user2, created = User.objects.get_or_create(
        username='operator2',
        defaults={'email': 'operator2@financepro.ru', 'first_name': 'Иван', 'last_name': 'Сидоров'}
    )
    if created:
        user2.set_password('1q2w#E$R%T')
        user2.save()
        print("Создан пользователь operator2")
    
    operator2, created = Operator.objects.get_or_create(
        user=user2,
        defaults={
            'operator_type': 'security',
            'email': 'operator2@financepro',
            'is_active': True
        }
    )
    if created:
        print("Создан оператор ДБО #2")
    
    # Клиент ДБО
    user3, created = User.objects.get_or_create(
        username='client1',
        defaults={'email': 'client1@financepro.ru', 'first_name': 'Петр', 'last_name': 'Иванов'}
    )
    if created:
        user3.set_password('1q2w#E$R%T')
        user3.save()
        print("Создан пользователь client1")
    
    client1, created = Client.objects.get_or_create(
        user=user3,
        defaults={
            'client_id': 'CLI001',
            'full_name': 'Петр Иванов',
            'email': 'client1@financepro',
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
        defaults={'description': 'Основные банковские услуги'}
    )
    
    category2, created = ServiceCategory.objects.get_or_create(
        name='Премиум услуги',
        defaults={'description': 'Премиальные банковские услуги'}
    )
    
    category3, created = ServiceCategory.objects.get_or_create(
        name='Служебные услуги',
        defaults={'description': 'Внутренние услуги банка'}
    )
    
    # Создаем услуги
    # Все услуги создаются с ненулевым рейтингом
    services_data = [
        # Базовые услуги - цифровые каналы обслуживания
        {'name': 'Интернет-банк', 'description': 'Полнофункциональный доступ к интернет-банку через веб-интерфейс', 'category': category1, 'price': 0, 'rating': Decimal('4.6'), 'rating_count': 145},
        {'name': 'Мобильный банк', 'description': 'Мобильное приложение для iOS и Android с биометрией', 'category': category1, 'price': 0, 'rating': Decimal('4.7'), 'rating_count': 132},
        {'name': 'SMS-уведомления', 'description': 'Информирование о всех операциях по счету через SMS', 'category': category1, 'price': 150, 'rating': Decimal('4.3'), 'rating_count': 98},
        {'name': 'Email-уведомления', 'description': 'Ежедневные и еженедельные отчеты о движении средств на email', 'category': category1, 'price': 0, 'rating': Decimal('4.2'), 'rating_count': 87},
        {'name': 'Push-уведомления', 'description': 'Мгновенные уведомления о транзакциях в мобильном приложении', 'category': category1, 'price': 0, 'rating': Decimal('4.5'), 'rating_count': 112},
        {'name': 'Телефонный банкинг', 'description': 'Круглосуточная служба поддержки и обслуживания по телефону', 'category': category1, 'price': 300, 'rating': Decimal('4.4'), 'rating_count': 105},
        {'name': 'Веб-версия для бизнеса', 'description': 'Расширенный интернет-банк с функциями для корпоративных клиентов', 'category': category1, 'price': 5000, 'rating': Decimal('4.5'), 'rating_count': 67},
        
        # Премиум услуги
        {'name': 'Персональный менеджер', 'description': 'Выделенный менеджер для решения всех банковских вопросов', 'category': category2, 'price': 12000, 'rating': Decimal('4.8'), 'rating_count': 52},
        {'name': 'Приоритетное обслуживание', 'description': 'Приоритетная очередь и ускоренное рассмотрение заявок', 'category': category2, 'price': 5000, 'rating': Decimal('4.7'), 'rating_count': 48},
        {'name': 'VIP-зал обслуживания', 'description': 'Обслуживание в комфортабельном VIP-зале банка', 'category': category2, 'price': 3000, 'rating': Decimal('4.7'), 'rating_count': 41},
        {'name': 'Консьерж-сервис', 'description': 'Персональный консьерж для решения любых вопросов 24/7', 'category': category2, 'price': 25000, 'rating': Decimal('4.9'), 'rating_count': 28},
        {'name': 'Эксклюзивные предложения', 'description': 'Доступ к эксклюзивным банковским продуктам и акциям', 'category': category2, 'price': 8000, 'rating': Decimal('4.6'), 'rating_count': 35},
        {'name': 'Кэшбэк повышенный', 'description': 'Увеличенный процент кэшбэка на все покупки', 'category': category2, 'price': 3500, 'rating': Decimal('4.6'), 'rating_count': 42},
    ]
    
    for service_data in services_data:
        Service.objects.get_or_create(
            name=service_data['name'],
            defaults=service_data
        )

    # Заполняем рейтинг и количество голосов для услуг (демо-данные)
    # Рейтинг можно задать при создании услуги в services_data, добавив поля 'rating' и 'rating_count'
    # Если рейтинг не задан, устанавливается случайный
    print("Установка рейтингов услуг...")
    import random
    for svc in Service.objects.all():
        # Устанавливаем рейтинг только если он не был задан при создании (равен 0)
        if svc.rating == 0 and svc.rating_count == 0:
            svc.rating_count = random.randint(5, 150)
            rating_value = Decimal(str(round(random.uniform(3.5, 5.0), 2)))
            svc.rating = rating_value
            svc.save()
    
    # Создаем больше категорий услуг
    category4, created = ServiceCategory.objects.get_or_create(
        name='Платежи и переводы',
        defaults={'description': 'Услуги по переводам и платежам'}
    )
    
    category7, created = ServiceCategory.objects.get_or_create(
        name='Инвестиции',
        defaults={'description': 'Инвестиционные продукты'}
    )
    
    category8, created = ServiceCategory.objects.get_or_create(
        name='Страхование',
        defaults={'description': 'Страховые продукты'}
    )

    # Создаем расширенный список услуг
    # Все услуги создаются с ненулевым рейтингом
    # Убраны все услуги, которые дублируют реализованный функционал:
    # - Карты (есть service/cards/)
    # - Депозиты (есть service/deposits/)
    # - Переводы (есть service/transfers/)
    # - Инвестиции (есть service/investments/)
    services_data = [
        # Платежи и переводы - дополнительные сервисы (не дублируют основной функционал)
        {'name': 'Автоплатежи', 'description': 'Автоматическая оплата коммунальных услуг, интернета, телефона по расписанию', 'category': category4, 'price': 200, 'rating': Decimal('4.6'), 'rating_count': 112},
        {'name': 'Шаблоны платежей', 'description': 'Сохранение и использование шаблонов для регулярных платежей', 'category': category4, 'price': 0, 'rating': Decimal('4.5'), 'rating_count': 98},
        {'name': 'Международные переводы SWIFT', 'description': 'Переводы в другие страны через систему SWIFT с полным сопровождением', 'category': category4, 'price': 1500, 'rating': Decimal('4.3'), 'rating_count': 76},
        {'name': 'Переводы по номеру телефона', 'description': 'Мгновенные переводы по номеру мобильного телефона без реквизитов', 'category': category4, 'price': 50, 'rating': Decimal('4.7'), 'rating_count': 134},
        {'name': 'QR-платежи в магазинах', 'description': 'Оплата покупок по QR-коду в торговых точках через мобильное приложение', 'category': category4, 'price': 0, 'rating': Decimal('4.4'), 'rating_count': 94},
        {'name': 'NFC-платежи', 'description': 'Бесконтактная оплата через NFC в мобильном приложении без ввода PIN', 'category': category4, 'price': 0, 'rating': Decimal('4.6'), 'rating_count': 108},
        {'name': 'Переводы в криптовалютах', 'description': 'Переводы и конвертация в криптовалюты через банковскую платформу', 'category': category4, 'price': 2000, 'rating': Decimal('3.9'), 'rating_count': 43},
        {'name': 'Мультивалютные переводы', 'description': 'Переводы в различных валютах с автоматической конвертацией по выгодному курсу', 'category': category4, 'price': 300, 'rating': Decimal('4.4'), 'rating_count': 82},
        {'name': 'Платежи через голосового ассистента', 'description': 'Оплата счетов через голосовые команды в мобильном приложении', 'category': category4, 'price': 800, 'rating': Decimal('4.2'), 'rating_count': 56},
        {'name': 'Регулярные переводы', 'description': 'Настройка автоматических регулярных переводов на указанные даты', 'category': category4, 'price': 100, 'rating': Decimal('4.5'), 'rating_count': 89},
        {'name': 'Платежи по биометрии', 'description': 'Оплата покупок с использованием биометрических данных (отпечаток, Face ID)', 'category': category4, 'price': 0, 'rating': Decimal('4.6'), 'rating_count': 95},
        
        # Инвестиции - дополнительные программы (не дублируют основной функционал)
        {'name': 'ИИС типа А', 'description': 'Индивидуальный инвестиционный счет с налоговым вычетом типа А', 'category': category7, 'price': 500, 'rating': Decimal('4.6'), 'rating_count': 79},
        {'name': 'ИИС типа Б', 'description': 'Индивидуальный инвестиционный счет с освобождением от налога типа Б', 'category': category7, 'price': 500, 'rating': Decimal('4.5'), 'rating_count': 72},
        {'name': 'ПИФ акций', 'description': 'Паевой инвестиционный фонд, инвестирующий в акции', 'category': category7, 'price': 1000, 'rating': Decimal('4.3'), 'rating_count': 71},
        {'name': 'ПИФ облигаций', 'description': 'Консервативный ПИФ, инвестирующий в облигации', 'category': category7, 'price': 1000, 'rating': Decimal('4.4'), 'rating_count': 68},
        {'name': 'ПИФ смешанный', 'description': 'Сбалансированный ПИФ с инвестициями в акции и облигации', 'category': category7, 'price': 1200, 'rating': Decimal('4.4'), 'rating_count': 65},
        {'name': 'ОФЗ', 'description': 'Облигации федерального займа с гарантированным доходом', 'category': category7, 'price': 0, 'rating': Decimal('4.5'), 'rating_count': 96},
        {'name': 'Корпоративные облигации', 'description': 'Облигации крупных российских компаний', 'category': category7, 'price': 800, 'rating': Decimal('4.3'), 'rating_count': 84},
        {'name': 'Доверительное управление', 'description': 'Профессиональное управление инвестиционным портфелем', 'category': category7, 'price': 15000, 'rating': Decimal('4.5'), 'rating_count': 58},
        {'name': 'Робот-советник', 'description': 'Автоматизированное управление портфелем на основе алгоритмов', 'category': category7, 'price': 2000, 'rating': Decimal('4.2'), 'rating_count': 47},
        {'name': 'Инвестиции в золото', 'description': 'Покупка и хранение золота в обезличенном виде', 'category': category7, 'price': 1500, 'rating': Decimal('4.4'), 'rating_count': 61},
        {'name': 'Структурированные продукты', 'description': 'Инвестиционные продукты с защитой капитала', 'category': category7, 'price': 3000, 'rating': Decimal('4.1'), 'rating_count': 39},
        {'name': 'Криптовалютные инвестиции', 'description': 'Инвестиции в криптовалюты через банковскую платформу', 'category': category7, 'price': 2500, 'rating': Decimal('3.8'), 'rating_count': 34},
        {'name': 'Инвестиции в недвижимость', 'description': 'Коллективные инвестиции в коммерческую недвижимость', 'category': category7, 'price': 5000, 'rating': Decimal('4.3'), 'rating_count': 52},
        
        # Страхование - расширенный список
        {'name': 'Страхование жизни и здоровья', 'description': 'Комплексное страхование жизни и здоровья с накопительной частью', 'category': category8, 'price': 2500, 'rating': Decimal('4.3'), 'rating_count': 88},
        {'name': 'Страхование от несчастных случаев', 'description': 'Страхование от несчастных случаев и травм', 'category': category8, 'price': 1200, 'rating': Decimal('4.2'), 'rating_count': 76},
        {'name': 'КАСКО', 'description': 'Комплексное страхование автомобиля от ущерба и угона', 'category': category8, 'price': 0, 'rating': Decimal('4.4'), 'rating_count': 102},
        {'name': 'ОСАГО', 'description': 'Обязательное страхование автогражданской ответственности', 'category': category8, 'price': 0, 'rating': Decimal('4.1'), 'rating_count': 125},
        {'name': 'Страхование квартиры', 'description': 'Страхование квартиры от пожара, затопления и других рисков', 'category': category8, 'price': 1800, 'rating': Decimal('4.2'), 'rating_count': 74},
        {'name': 'Страхование дома', 'description': 'Комплексное страхование частного дома и имущества', 'category': category8, 'price': 3500, 'rating': Decimal('4.3'), 'rating_count': 58},
        {'name': 'ДМС', 'description': 'Добровольное медицинское страхование с расширенным покрытием', 'category': category8, 'price': 4500, 'rating': Decimal('4.5'), 'rating_count': 91},
        {'name': 'Страхование путешествий', 'description': 'Страхование выезжающих за рубеж от медицинских расходов', 'category': category8, 'price': 800, 'rating': Decimal('4.4'), 'rating_count': 82},
        {'name': 'Страхование ипотеки', 'description': 'Страхование жизни и здоровья заемщика по ипотеке', 'category': category8, 'price': 2000, 'rating': Decimal('4.2'), 'rating_count': 69},
        {'name': 'Страхование ответственности', 'description': 'Страхование гражданской ответственности перед третьими лицами', 'category': category8, 'price': 1500, 'rating': Decimal('4.1'), 'rating_count': 54},
        {'name': 'Страхование животных', 'description': 'Страхование домашних животных от болезней и несчастных случаев', 'category': category8, 'price': 1000, 'rating': Decimal('4.2'), 'rating_count': 45},
        {'name': 'Страхование техники', 'description': 'Страхование бытовой техники и электроники от поломок', 'category': category8, 'price': 600, 'rating': Decimal('4.0'), 'rating_count': 38},
        
        # Скрытые служебные услуги
        {'name': 'Бесплатные промокоды', 'description': 'Промокоды для сотрудников банка на различные услуги', 'category': category3, 'price': 0, 'rating': Decimal('5.0'), 'rating_count': 18},
        {'name': 'Снятие комиссии 0%', 'description': 'Бесплатные переводы и операции для сотрудников', 'category': category3, 'price': 0, 'rating': Decimal('4.9'), 'rating_count': 15},
        {'name': 'Повышенные лимиты', 'description': 'Увеличенные лимиты операций для сотрудников банка', 'category': category3, 'price': 0, 'rating': Decimal('4.8'), 'rating_count': 12},
        {'name': 'Доступ к админ-панели', 'description': 'Административный доступ к внутренним системам банка', 'category': category3, 'price': 0, 'rating': Decimal('5.0'), 'rating_count': 9},
        {'name': 'Служебные кредиты', 'description': 'Кредиты для сотрудников под 0% годовых', 'category': category3, 'price': 0, 'rating': Decimal('4.9'), 'rating_count': 11},
        {'name': 'Корпоративные бонусы', 'description': 'Бонусы и премии для сотрудников банка', 'category': category3, 'price': 0, 'rating': Decimal('4.8'), 'rating_count': 14},
        {'name': 'VIP-обслуживание сотрудников', 'description': 'Особые условия обслуживания для сотрудников банка', 'category': category3, 'price': 0, 'rating': Decimal('4.9'), 'rating_count': 10},
        {'name': 'Доступ к внутренним системам', 'description': 'Полный доступ к внутренним банковским системам и базам данных', 'category': category3, 'price': 0, 'rating': Decimal('5.0'), 'rating_count': 7},
    ]
    
    for service_data in services_data:
        Service.objects.get_or_create(
            name=service_data['name'],
            defaults=service_data
        )

    # Устанавливаем рейтинг только для услуг, которые были созданы без рейтинга (например, из других источников)
    # Все услуги из init_data.py уже имеют заданный рейтинг, поэтому этот блок обрабатывает только исключительные случаи
    for svc in Service.objects.all():
        if svc.rating == 0 and svc.rating_count == 0:
            # Устанавливаем случайный рейтинг только для услуг без заданного рейтинга
            import random
            svc.rating_count = random.randint(5, 150)
            rating_value = Decimal(str(round(random.uniform(3.5, 5.0), 2)))
            svc.rating = rating_value
            svc.save()

    # Создаем больше клиентов
    clients_data = [
        {
            'username': 'client2',
            'password': '1q2w#E$R%T',
            'email': 'client2@financepro.ru',
            'first_name': 'Мария',
            'last_name': 'Смирнова',
            'client_id': 'CLI002',
            'full_name': 'Мария Смирнова',
            'phone': '79992345678'
        },
        {
            'username': 'client3',
            'password': '1q2w#E$R%T',
            'email': 'client3@financepro.ru',
            'first_name': 'Алексей',
            'last_name': 'Козлов',
            'client_id': 'CLI003',
            'full_name': 'Алексей Козлов',
            'phone': '79993456789'
        },
        {
            'username': 'client4',
            'password': '1q2w#E$R%T',
            'email': 'client4@financepro.ru',
            'first_name': 'Елена',
            'last_name': 'Морозова',
            'client_id': 'CLI004',
            'full_name': 'Елена Морозова',
            'phone': '79994567890'
        },
        {
            'username': 'client5',
            'password': '1q2w#E$R%T',
            'email': 'client5@financepro.ru',
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

    # Очищаем существующие заявки и подключенные услуги
    ServiceRequest.objects.all().delete()
    ClientService.objects.all().delete()
    
    # Создаем заявки на услуги (только одобренные, без pending заявок для оператора 2)
    service_requests_data = [
        {
            'client': client1,
            'service_name': 'VIP-зал',
            'service_description': 'Хочу получить доступ к VIP-залу банка',
            'price': 0,
            'status': 'approved'
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
        {'name': 'Интернет-банк', 'client': client1},
        {'name': 'Мобильный банк', 'client': client1},
        {'name': 'Быстрые переводы', 'client': client1},
        {'name': 'VIP-зал', 'client': client1},
    ]
    
    for service_info in connected_services_data:
        try:
            service = Service.objects.get(name=service_info['name'])
            ClientService.objects.get_or_create(
                client=service_info['client'],
                service=service,
                defaults={'connected_at': timezone.now()}
            )
        except Service.DoesNotExist:
            print(f"⚠️  Услуга '{service_info['name']}' не найдена, пропускаем...")
    
    # Создаем подключенные услуги для других клиентов
    if Client.objects.filter(user__username='client2').exists():
        client2 = Client.objects.get(user__username='client2')
        for service_name in ['Интернет-банк', 'Срочный депозит']:
            try:
                service = Service.objects.get(name=service_name)
                ClientService.objects.get_or_create(
                    client=client2,
                    service=service,
                    defaults={'connected_at': timezone.now()}
                )
            except Service.DoesNotExist:
                print(f"⚠️  Услуга '{service_name}' не найдена, пропускаем...")
    
    if Client.objects.filter(user__username='client3').exists():
        client3 = Client.objects.get(user__username='client3')
        for service_name in ['Мобильный банк', 'Потребительский кредит', 'Банковские карты']:
            try:
                service = Service.objects.get(name=service_name)
                ClientService.objects.get_or_create(
                    client=client3,
                    service=service,
                    defaults={'connected_at': timezone.now()}
                )
            except Service.DoesNotExist:
                print(f"⚠️  Услуга '{service_name}' не найдена, пропускаем...")

    print("\nДемо-данные успешно созданы!")
    print("Доступные аккаунты:")
    print("- Оператор ДБО #1: operator1 / 1q2w#E$R")
    print("- Оператор ДБО #2: operator2 / 1q2w#E$R%T")
    print("- Клиент ДБО: client1 / 1q2w#E$R%T")
    print("- Клиент ДБО: client2 / 1q2w#E$R%T")
    print("- Клиент ДБО: client3 / 1q2w#E$R%T")
    print("- Клиент ДБО: client4 / 1q2w#E$R%T (не верифицирован)")
    print("- Клиент ДБО: client5 / 1q2w#E$R%T (не верифицирован)")
    print("\nСоздано:")
    print(f"- {Service.objects.count()} услуг")
    print(f"- {ServiceCategory.objects.count()} категорий услуг")
    print(f"- {Client.objects.count()} клиентов")
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
    print("- Оператор ДБО #1: operator1 / 1q2w#E$R")
    print("- Оператор ДБО #2: operator2 / 1q2w#E$R%T")
    print("- Клиент ДБО: client1 / 1q2w#E$R%T")
    print("- Клиент ДБО: client2 / 1q2w#E$R%T")
    print("- Клиент ДБО: client3 / 1q2w#E$R%T")
    print("- Клиент ДБО: client4 / 1q2w#E$R%T (не верифицирован)")
    print("- Клиент ДБО: client5 / 1q2w#E$R%T (не верифицирован)")
    print("\nСоздано:")
    print(f"- {Service.objects.count()} услуг")
    print(f"- {ServiceCategory.objects.count()} категорий услуг")
    print(f"- {Client.objects.count()} клиентов")
    print(f"- {BankCard.objects.count()} банковских карт")
    print(f"- {Deposit.objects.count()} депозитов")
    print(f"- {Credit.objects.count()} кредитов")
    print(f"- {InvestmentProduct.objects.count()} инвестиционных продуктов")
    print(f"- {ClientInvestment.objects.count()} инвестиций клиентов")
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


if __name__ == '__main__':
    try:
        # Проверяем, что Django настроен правильно
        from django.db import connection
        connection.ensure_connection()
        
        create_demo_data()
        print("\n✅ Инициализация демо-данных завершена успешно!")
    except Exception as e:
        error_msg = str(e)
        if 'does not exist' in error_msg or 'relation' in error_msg.lower():
            print(f"\n❌ Ошибка: таблицы не существуют: {e}")
            print("💡 Попробуйте применить миграции вручную:")
            print("   docker compose exec app python manage.py migrate --noinput")
            print("   docker compose exec app python manage.py migrate auth --noinput")
        else:
            print(f"\n❌ Ошибка при инициализации демо-данных: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
