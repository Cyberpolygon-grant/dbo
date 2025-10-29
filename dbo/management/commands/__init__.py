from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dbo.models import Operator, Client, ServiceCategory, Service, PhishingEmail

class Command(BaseCommand):
    help = 'Инициализация демо-данных для системы ДБО'

    def handle(self, *args, **options):
        self.stdout.write('Создание демо-данных...')
        
        # Создаем пользователей
        # Оператор ДБО #1
        user1, created = User.objects.get_or_create(
            username='operator1',
            defaults={'email': 'operator1@bank.ru', 'first_name': 'Анна', 'last_name': 'Петрова'}
        )
        if created:
            user1.set_password('password123')
            user1.save()
        
        operator1, created = Operator.objects.get_or_create(
            user=user1,
            defaults={
                'operator_type': 'client_service',
                'email': 'operator1@bank.ru',
                'is_active': True
            }
        )
        
        # Оператор ДБО #2
        user2, created = User.objects.get_or_create(
            username='operator2',
            defaults={'email': 'operator2@bank.ru', 'first_name': 'Иван', 'last_name': 'Сидоров'}
        )
        if created:
            user2.set_password('password123')
            user2.save()
        
        operator2, created = Operator.objects.get_or_create(
            user=user2,
            defaults={
                'operator_type': 'security',
                'email': 'operator2@bank.ru',
                'is_active': True
            }
        )
        
        # Клиент ДБО
        user3, created = User.objects.get_or_create(
            username='client1',
            defaults={'email': 'client1@example.com', 'first_name': 'Петр', 'last_name': 'Иванов'}
        )
        if created:
            user3.set_password('password123')
            user3.save()
        
        client1, created = Client.objects.get_or_create(
            user=user3,
            defaults={
                'client_id': 'CLI001',
                'full_name': 'Петр Иванов',
                'email': 'client1@example.com',
                'phone': '+7 (999) 123-45-67',
                'is_active': True,
                'created_by': operator1
            }
        )
        
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
        
        # Создаем фишинговое письмо
        PhishingEmail.objects.get_or_create(
            recipient_email=operator1.email,
            defaults={
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
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Демо-данные успешно созданы!')
        )
        self.stdout.write('Доступные аккаунты:')
        self.stdout.write('- Оператор ДБО #1: operator1 / password123')
        self.stdout.write('- Оператор ДБО #2: operator2 / password123')
        self.stdout.write('- Клиент ДБО: client1 / password123')
