from django.contrib import admin
from .models import (
    News,
    Operator,
    Client,
    ServiceCategory,
    Service,
    ServiceRequest,
    ClientService,
    PhishingEmail,
    BankAccount,
    BankCard,
    Transaction,
    Deposit,
    Credit,
    InvestmentProduct,
    ClientInvestment,
)

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'priority', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'priority')
    search_fields = ('title', 'content')
    ordering = ('-priority', '-created_at')
    list_editable = ('is_active', 'priority')


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('user', 'operator_type', 'email', 'is_active', 'created_at')
    list_filter = ('operator_type', 'is_active')
    search_fields = ('user__username', 'email')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'client_id', 'email', 'phone', 'is_active', 'is_verified', 'created_at')
    list_filter = ('is_active', 'is_verified')
    search_fields = ('full_name', 'client_id', 'email', 'phone', 'user__username')


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_public')
    list_filter = ('is_public',)
    search_fields = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_public', 'is_active', 'is_privileged', 'created_at')
    list_filter = ('is_public', 'is_active', 'is_privileged', 'category')
    search_fields = ('name', 'description')


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'client', 'price', 'status', 'reviewed_by', 'created_at', 'reviewed_at')
    list_filter = ('status', 'reviewed_by')
    search_fields = ('service_name', 'client__full_name', 'client__client_id')


@admin.register(ClientService)
class ClientServiceAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'status', 'is_active', 'connected_at')
    list_filter = ('status', 'is_active', 'service__category')
    search_fields = ('client__full_name', 'service__name')


@admin.register(PhishingEmail)
class PhishingEmailAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'subject', 'sent_at', 'is_opened')
    list_filter = ('is_opened',)
    search_fields = ('recipient_email', 'subject')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'client', 'account_type', 'balance', 'currency', 'is_active', 'created_at')
    list_filter = ('account_type', 'is_active')
    search_fields = ('account_number', 'client__full_name')


@admin.register(BankCard)
class BankCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'account', 'card_type', 'expiry_date', 'is_active', 'daily_limit', 'created_at')
    list_filter = ('card_type', 'is_active')
    search_fields = ('card_number', 'account__account_number')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_account', 'to_account', 'amount', 'currency', 'transaction_type', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'currency')
    search_fields = ('from_account__account_number', 'to_account__account_number', 'description')


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('client', 'account', 'amount', 'interest_rate', 'term_months', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'term_months')
    search_fields = ('client__full_name', 'account__account_number')


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = ('client', 'amount', 'interest_rate', 'term_months', 'monthly_payment', 'remaining_amount', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'term_months')
    search_fields = ('client__full_name',)


@admin.register(InvestmentProduct)
class InvestmentProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_type', 'min_amount', 'risk_level', 'expected_return', 'is_active', 'created_at')
    list_filter = ('product_type', 'risk_level', 'is_active')
    search_fields = ('name',)


@admin.register(ClientInvestment)
class ClientInvestmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'product', 'amount', 'current_value', 'status', 'purchase_date', 'created_at')
    list_filter = ('status', 'product__product_type')
    search_fields = ('client__full_name', 'product__name')
