from django.db import models
from django.contrib.auth.models import User
import uuid

class Operator(models.Model):
    """Операторы ДБО"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    operator_type = models.CharField(max_length=50, choices=[
        ('client_service', 'Оператор ДБО #1 (Отдел клиентского обслуживания)'),
        ('security', 'Оператор ДБО #2 (Отдел безопасности/валидации)'),
    ])
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_operator_type_display()})"

class Client(models.Model):
    """Клиенты ДБО"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    primary_card = models.ForeignKey('BankCard', on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_for_client')
    created_by = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True)
    is_privileged = models.BooleanField(default=False, verbose_name='Служебный клиент', help_text='Может подключать служебные услуги')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.client_id})"

class ServiceCategory(models.Model):
    """Категории услуг"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    """Услуги ДБО"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)  # Средняя оценка 0-5
    rating_count = models.PositiveIntegerField(default=0)  # Количество голосов
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ServiceRequest(models.Model):
    """Заявки на создание новых услуг"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает рассмотрения'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=200)
    service_description = models.TextField()  # Здесь будет XSS
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Заявка на услугу '{self.service_name}' от {self.client.full_name}"

class ClientService(models.Model):
    """Подключенные услуги клиентов"""
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('suspended', 'Приостановлена'),
        ('cancelled', 'Отменена'),
        ('expired', 'Истекла'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    connected_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Ежемесячная плата за услугу")
    next_payment_date = models.DateField(null=True, blank=True, help_text="Дата следующего платежа")
    auto_renewal = models.BooleanField(default=True, help_text="Автоматическое продление")
    notes = models.TextField(blank=True, help_text="Дополнительные заметки")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_services')

    class Meta:
        unique_together = ['client', 'service']

    def __str__(self):
        return f"{self.client.full_name} - {self.service.name} ({self.get_status_display()})"

class BankCard(models.Model):
    """Банковская карта"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=19)  # Маскированный номер
    card_type = models.CharField(max_length=20, choices=[
        ('debit', 'Дебетовая'),
        ('credit', 'Кредитная'),
        ('prepaid', 'Предоплаченная'),
    ])
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='RUB')
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2, default=100000)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.card_number} - {self.client.full_name}"

class Transaction(models.Model):
    """Банковская транзакция"""
    from_card = models.ForeignKey(BankCard, on_delete=models.CASCADE, related_name='outgoing_transactions', null=True, blank=True)
    to_card = models.ForeignKey(BankCard, on_delete=models.CASCADE, related_name='incoming_transactions', null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='RUB')
    transaction_type = models.CharField(max_length=20, choices=[
        ('transfer', 'Перевод'),
        ('payment', 'Платеж'),
        ('deposit', 'Пополнение'),
        ('withdrawal', 'Снятие'),
        ('fee', 'Комиссия'),
    ])
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Ожидает'),
        ('completed', 'Завершена'),
        ('failed', 'Отклонена'),
        ('cancelled', 'Отменена'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency}"

class Deposit(models.Model):
    """Депозит"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='deposits')
    card = models.ForeignKey(BankCard, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Депозит {self.client.full_name} - {self.amount} руб."

class Credit(models.Model):
    """Кредит"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='credits')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=15, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Активный'),
        ('paid', 'Погашен'),
        ('overdue', 'Просрочен'),
    ], default='active')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
class InvestmentProduct(models.Model):
    """Инвестиционные продукты"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    product_type = models.CharField(max_length=50, choices=[
        ('iis', 'Индивидуальный инвестиционный счет'),
        ('pif', 'Паевой инвестиционный фонд'),
        ('brokerage', 'Брокерский счет'),
        ('trust', 'Доверительное управление'),
    ])
    min_amount = models.DecimalField(max_digits=15, decimal_places=2)
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ])
    expected_return = models.DecimalField(max_digits=5, decimal_places=2, help_text="Ожидаемая доходность в %")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ClientInvestment(models.Model):
    """Инвестиции клиентов"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='investments')
    product = models.ForeignKey(InvestmentProduct, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    purchase_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('active', 'Активная'),
        ('sold', 'Проданная'),
        ('closed', 'Закрытая'),
    ], default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.full_name} - {self.product.name}"


class News(models.Model):
    """Новости банка для бегущей строки"""
    title = models.CharField(max_length=200, verbose_name="Заголовок новости")
    content = models.TextField(verbose_name="Содержание новости")
    category = models.CharField(max_length=50, choices=[
        ('general', 'Общие новости'),
        ('rates', 'Курсы валют'),
        ('promotions', 'Акции и предложения'),
        ('security', 'Безопасность'),
        ('services', 'Новые услуги'),
    ], default='general', verbose_name="Категория")
    priority = models.IntegerField(default=1, verbose_name="Приоритет (1-5)")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return self.title


class DBOLog(models.Model):
    """Логи высокоуровневых событий ДБО"""
    EVENT_TYPES = [
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
        ('client_created', 'Создание клиента'),
        ('client_updated', 'Обновление данных клиента'),
        ('transaction_created', 'Создание транзакции'),
        ('transaction_completed', 'Завершение транзакции'),
        ('service_connected', 'Подключение услуги'),
        ('service_disconnected', 'Отключение услуги'),
        ('service_request_created', 'Создание заявки на услугу'),
        ('service_request_approved', 'Одобрение заявки на услугу'),
        ('service_request_rejected', 'Отклонение заявки на услугу'),
        ('card_created', 'Создание карты'),
        ('card_pin_changed', 'Изменение PIN карты'),
        ('deposit_created', 'Создание депозита'),
        ('credit_created', 'Создание кредита'),
        ('investment_created', 'Создание инвестиции'),
        ('page_viewed', 'Просмотр страницы'),
        ('data_exported', 'Экспорт данных'),
        ('other', 'Прочее'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Информация'),
        ('warning', 'Предупреждение'),
        ('error', 'Ошибка'),
        ('critical', 'Критическая ошибка'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, verbose_name='Тип события')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info', verbose_name='Уровень важности')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Клиент')
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Оператор')
    description = models.TextField(verbose_name='Описание события')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адрес')
    user_agent = models.CharField(max_length=500, blank=True, verbose_name='User Agent')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Дополнительные данные')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время события')
    
    class Meta:
        verbose_name = 'Лог ДБО'
        verbose_name_plural = 'Логи ДБО'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['event_type']),
            models.Index(fields=['user']),
            models.Index(fields=['client']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.created_at.strftime('%d.%m.%Y %H:%M:%S')}"


