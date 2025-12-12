from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dbo.models import Operator, Client

class Command(BaseCommand):
    help = 'Проверка и создание пользователей системы ДБО'

    def handle(self, *args, **options):
        self.stdout.write('Проверка пользователей системы ДБО...')
        
        # Список пользователей для создания
        users_data = [
            {
                'username': 'operator1',
                'password': 'password123',
                'email': 'operator1@financepro.ru',
                'first_name': 'Анна',
                'last_name': 'Петрова',
                'type': 'operator',
                'operator_type': 'client_service'
            },
            {
                'username': 'operator2',
                'password': 'password123',
                'email': 'operator2@financepro.ru',
                'first_name': 'Иван',
                'last_name': 'Сидоров',
                'type': 'operator',
                'operator_type': 'security'
            },
            {
                'username': 'client1',
                'password': 'password123',
                'email': 'client1@financepro.ru',
                'first_name': 'Петр',
                'last_name': 'Иванов',
                'type': 'client'
            }
        ]
        
        for user_data in users_data:
            username = user_data['username']
            
            # Проверяем существование пользователя
            try:
                user = User.objects.get(username=username)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Пользователь {username} уже существует')
                )
            except User.DoesNotExist:
                # Создаем пользователя
                user = User.objects.create_user(
                    username=username,
                    password=user_data['password'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Создан пользователь {username}')
                )
            
            # Проверяем связанные объекты
            if user_data['type'] == 'operator':
                try:
                    operator = Operator.objects.get(user=user)
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Оператор {username} уже существует')
                    )
                except Operator.DoesNotExist:
                    operator = Operator.objects.create(
                        user=user,
                        operator_type=user_data['operator_type'],
                        email=user_data['email'],
                        is_active=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Создан оператор {username}')
                    )
            
            elif user_data['type'] == 'client':
                try:
                    client = Client.objects.get(user=user)
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Клиент {username} уже существует')
                    )
                except Client.DoesNotExist:
                    # Получаем оператора для создания клиента
                    try:
                        operator1 = Operator.objects.get(operator_type='client_service')
                    except Operator.DoesNotExist:
                        operator1 = None
                    
                    client = Client.objects.create(
                        user=user,
                        client_id=f'CLI{user.id:03d}',
                        full_name=f"{user_data['first_name']} {user_data['last_name']}",
                        email=user_data['email'],
                        phone='+7 (999) 123-45-67',
                        is_active=True,
                        created_by=operator1
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Создан клиент {username}')
                    )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Проверка завершена!'))
        self.stdout.write('\nДоступные аккаунты:')
        self.stdout.write('• Оператор ДБО #1: operator1 / password123')
        self.stdout.write('• Оператор ДБО #2: operator2 / password123')
        self.stdout.write('• Клиент ДБО: client1 / password123')
        self.stdout.write('\nТеперь вы можете войти в систему!')
