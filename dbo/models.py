from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_by = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.client_id})"

class ServiceCategory(models.Model):
    """Категории услуг"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)  # Публичные или скрытые услуги

    def __str__(self):
        return self.name

class Service(models.Model):
    """Услуги ДБО"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)  # Публичные или скрытые услуги
    is_privileged = models.BooleanField(default=False)  # Привилегированные услуги
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

class PhishingEmail(models.Model):
    """Фишинговые письма для симуляции"""
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    content = models.TextField()
    attachment_name = models.CharField(max_length=100)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Фишинг: {self.subject} -> {self.recipient_email}"

class AttackLog(models.Model):
    """Лог атак для демонстрации"""
    ATTACK_TYPE_CHOICES = [
        ('phishing', 'Фишинг'),
        ('xss', 'XSS атака'),
        ('sqli', 'SQL инъекция'),
        ('privilege_escalation', 'Повышение привилегий'),
    ]
    
    attack_type = models.CharField(max_length=50, choices=ATTACK_TYPE_CHOICES)
    description = models.TextField()
    attacker_ip = models.GenericIPAddressField()
    target_user = models.CharField(max_length=100)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_attack_type_display()} - {self.target_user} ({self.timestamp})"

class BankAccount(models.Model):
    """Банковский счет клиента"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=20, choices=[
        ('checking', 'Текущий'),
        ('savings', 'Сберегательный'),
        ('deposit', 'Депозитный'),
        ('credit', 'Кредитный'),
    ])
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='RUB')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account_number} - {self.client.full_name}"

class BankCard(models.Model):
    """Банковская карта"""
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=19)  # Маскированный номер
    card_type = models.CharField(max_length=20, choices=[
        ('debit', 'Дебетовая'),
        ('credit', 'Кредитная'),
        ('prepaid', 'Предоплаченная'),
    ])
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2, default=100000)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.card_number} - {self.account.client.full_name}"

class Transaction(models.Model):
    """Банковская транзакция"""
    from_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='outgoing_transactions', null=True, blank=True)
    to_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='incoming_transactions', null=True, blank=True)
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
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='deposits')
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


