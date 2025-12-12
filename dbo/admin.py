from django.contrib import admin
from .models import (
    News,
    Operator,
    Client,
    ServiceCategory,
    Service,
    ServiceRequest,
    ClientService,
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
    list_display = ('full_name', 'client_id', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'client_id', 'email', 'phone', 'user__username')


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active', 'rating', 'rating_count', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description')
    fields = ('name', 'description', 'category', 'price', 'is_active', 'rating', 'rating_count', 'created_at')
    readonly_fields = ('created_at',)


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


@admin.register(BankCard)
class BankCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'client', 'card_type', 'balance', 'currency', 'expiry_date', 'is_active', 'daily_limit', 'created_at')
    list_filter = ('card_type', 'is_active')
    search_fields = ('card_number', 'client__full_name')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_card', 'to_card', 'amount', 'currency', 'transaction_type', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'currency')
    search_fields = ('from_card__card_number', 'to_card__card_number', 'description')


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('client', 'card', 'amount', 'interest_rate', 'term_months', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'term_months')
    search_fields = ('client__full_name', 'card__card_number')


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
