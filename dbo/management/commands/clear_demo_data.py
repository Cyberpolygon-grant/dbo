from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dbo.models import (
    Operator, Client, ServiceCategory, Service, ServiceRequest, News, PhishingEmail,
    ClientService, BankAccount, BankCard, Transaction,
    Deposit, Credit, InvestmentProduct, ClientInvestment
)

class Command(BaseCommand):
    help = 'Удаляет все демо-данные из системы ДБО'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтвердить удаление всех данных',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING('ВНИМАНИЕ: Эта команда удалит ВСЕ демо-данные!')
            )
            self.stdout.write('Для подтверждения используйте флаг --confirm')
            return

        self.stdout.write('Удаление всех демо-данных...')
        
        # Подсчитываем количество записей перед удалением
        counts_before = {
            'users': User.objects.count(),
            'operators': Operator.objects.count(),
            'clients': Client.objects.count(),
            'service_categories': ServiceCategory.objects.count(),
            'services': Service.objects.count(),
            'service_requests': ServiceRequest.objects.count(),
            'news': News.objects.count(),
            'phishing_emails': PhishingEmail.objects.count(),
            'client_services': ClientService.objects.count(),
            # attack_logs отключены
            'attack_logs': 0,
            'bank_accounts': BankAccount.objects.count(),
            'bank_cards': BankCard.objects.count(),
            'transactions': Transaction.objects.count(),
            'deposits': Deposit.objects.count(),
            'credits': Credit.objects.count(),
            'investment_products': InvestmentProduct.objects.count(),
            'client_investments': ClientInvestment.objects.count(),
        }

        # Удаляем все данные в правильном порядке (с учетом внешних ключей)
        self.stdout.write('Удаление банковских данных...')
        ClientInvestment.objects.all().delete()
        InvestmentProduct.objects.all().delete()
        Credit.objects.all().delete()
        Deposit.objects.all().delete()
        Transaction.objects.all().delete()
        BankCard.objects.all().delete()
        BankAccount.objects.all().delete()
        
        # Логи атак отключены
        
        self.stdout.write('Удаление подключенных услуг...')
        ClientService.objects.all().delete()
        
        self.stdout.write('Удаление заявок на услуги...')
        ServiceRequest.objects.all().delete()

        self.stdout.write('Удаление фишинговых писем...')
        PhishingEmail.objects.all().delete()
        
        self.stdout.write('Удаление новостей...')
        News.objects.all().delete()

        self.stdout.write('Удаление услуг...')
        Service.objects.all().delete()
        
        self.stdout.write('Удаление категорий услуг...')
        ServiceCategory.objects.all().delete()
        
        self.stdout.write('Удаление клиентов...')
        Client.objects.all().delete()
        
        self.stdout.write('Удаление операторов...')
        Operator.objects.all().delete()
        
        self.stdout.write('Удаление пользователей...')
        User.objects.all().delete()

        # Подсчитываем количество записей после удаления
        counts_after = {
            'users': User.objects.count(),
            'operators': Operator.objects.count(),
            'clients': Client.objects.count(),
            'service_categories': ServiceCategory.objects.count(),
            'services': Service.objects.count(),
            'service_requests': ServiceRequest.objects.count(),
            'news': News.objects.count(),
            'phishing_emails': PhishingEmail.objects.count(),
            'client_services': ClientService.objects.count(),
            'attack_logs': 0,
            'bank_accounts': BankAccount.objects.count(),
            'bank_cards': BankCard.objects.count(),
            'transactions': Transaction.objects.count(),
            'deposits': Deposit.objects.count(),
            'credits': Credit.objects.count(),
            'investment_products': InvestmentProduct.objects.count(),
            'client_investments': ClientInvestment.objects.count(),
        }

        self.stdout.write(
            self.style.SUCCESS('Все демо-данные успешно удалены!')
        )
        
        self.stdout.write('\nСтатистика удаления:')
        for model_name, count_before in counts_before.items():
            count_after = counts_after[model_name]
            deleted = count_before - count_after
            self.stdout.write(f'- {model_name}: {count_before} → {count_after} (удалено: {deleted})')
        
        self.stdout.write('\nСистема очищена от всех демо-данных.')
        self.stdout.write('Для создания новых демо-данных используйте команды:')
        self.stdout.write('- python manage.py init_demo_data')
        self.stdout.write('- python manage.py init_banking_services')
