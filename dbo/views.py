from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import connection, models
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme
from decimal import Decimal
import json
import logging

from .models import Operator, Client, Service, ClientService, ServiceCategory, PhishingEmail, BankAccount, BankCard, Transaction, Deposit, Credit, InvestmentProduct, ClientInvestment, ServiceRequest, News
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def is_admin(user):
    """Проверяет, является ли пользователь администратором"""
    return user.is_superuser or user.is_staff

@login_required
def attack_dashboard(request):
    messages.info(request, 'Модуль логирования атак отключен администратором.')
    return redirect('home')

def home(request):
    """Главная страница системы ДБО"""
    return render(request, 'index.html')

def banking_services(request):
    """Каталог банковских услуг"""
    # Получаем все категории услуг
    categories = ServiceCategory.objects.filter(is_public=True).prefetch_related('service_set')
    
    # Получаем все публичные услуги
    services = Service.objects.filter(is_public=True, is_active=True).select_related('category')
    
    # Получаем подключенные услуги клиента (если он авторизован)
    connected_services = set()
    if request.user.is_authenticated:
        try:
            client = Client.objects.get(user=request.user)
            connected_services = set(ClientService.objects.filter(
                client=client, 
                status='active'
            ).values_list('service_id', flat=True))
        except Client.DoesNotExist:
            pass
    
    # Группируем услуги по категориям
    services_by_category = {}
    for service in services:
        category_name = service.category.name
        if category_name not in services_by_category:
            services_by_category[category_name] = []
        services_by_category[category_name].append(service)
    
    # Статистика
    total_services = services.count()
    free_services = services.filter(price=0).count()
    
    context = {
        'categories': categories,
        'services_by_category': services_by_category,
        'connected_services': connected_services,
        'total_services': total_services,
        'free_services': free_services,
    }
    
    return render(request, 'banking_services.html', context)

@login_required
def search_services(request):
    """Поиск услуг с SQL-инъекцией уязвимостью"""
    query = request.GET.get('query', '')
    services = []
    
    if query:
        # УЯЗВИМОСТЬ: SQL-инъекция - прямое использование пользовательского ввода
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT s.id, s.name, s.description, s.price, c.name as category_name, s.is_public, s.is_privileged
                FROM dbo_service s
                JOIN dbo_servicecategory c ON s.category_id = c.id
                WHERE s.name LIKE '%{query}%' OR s.description LIKE '%{query}%'
                ORDER BY s.name
            """)
            columns = [col[0] for col in cursor.description]
            services = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Логируем атаку
    if query and any(keyword in query.lower() for keyword in ['union', 'select', 'drop', 'insert', 'update', 'delete', 'or', 'and']):
        AttackLog.objects.create(
            attack_type='sqli',
            target_user=request.user.username,
            details=f"SQL injection attempt in search_services: {query}",
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    context = {
        'query': query,
        'services': services,
    }
    
    return render(request, 'search_services.html', context)

@login_required
def service_detail(request, service_id):
    """Детальная информация об услуге"""
    try:
        service = Service.objects.get(id=service_id, is_public=True, is_active=True)
    except Service.DoesNotExist:
        messages.error(request, 'Услуга не найдена')
        return redirect('banking_services')
    
    try:
        client = Client.objects.get(user=request.user)
        is_connected = ClientService.objects.filter(client=client, service=service, is_active=True).exists()
    except Client.DoesNotExist:
        is_connected = False
    
    context = {
        'service': service,
        'is_connected': is_connected,
    }
    
    return render(request, 'services/detail.html', context)

@login_required
def get_service_details(request, service_id):
    """Получение детальной информации об услуге для модального окна"""
    try:
        service = Service.objects.get(id=service_id, is_active=True)
    except Service.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Услуга не найдена'})
    
    # Проверяем, подключена ли услуга у клиента
    client_service = None
    is_connected = False
    if request.user.is_authenticated:
        try:
            client = Client.objects.get(user=request.user)
            client_service = ClientService.objects.filter(
                client=client, 
                service=service
            ).first()
            is_connected = client_service and client_service.status == 'active' and client_service.is_active
        except Client.DoesNotExist:
            pass
    
    # Получаем статистику по услуге
    total_connections = ClientService.objects.filter(service=service, status='active').count()
    active_connections = ClientService.objects.filter(service=service, status='active', is_active=True).count()
    
    service_data = {
        'id': service.id,
        'name': service.name,
        'description': service.description,
        'price': float(service.price),
        'category': service.category.name if service.category else 'Без категории',
        'category_description': service.category.description if service.category else '',
        'is_connected': is_connected,
        'is_public': service.is_public,
        'is_privileged': service.is_privileged,
        'created_at': service.created_at.strftime('%d.%m.%Y'),
        'total_connections': total_connections,
        'active_connections': active_connections,
    }
    
    # Добавляем информацию о подключенной услуге, если она подключена
    if client_service and is_connected:
        service_data['client_service'] = {
            'connected_at': client_service.connected_at.strftime('%d.%m.%Y %H:%M'),
            'monthly_fee': float(client_service.monthly_fee),
            'next_payment_date': client_service.next_payment_date.strftime('%d.%m.%Y') if client_service.next_payment_date else None,
            'auto_renewal': client_service.auto_renewal,
            'notes': client_service.notes,
            'status': client_service.get_status_display(),
        }
    elif client_service:
        # Услуга была подключена, но отключена
        service_data['client_service'] = {
            'connected_at': client_service.connected_at.strftime('%d.%m.%Y %H:%M'),
            'cancelled_at': client_service.cancelled_at.strftime('%d.%m.%Y %H:%M') if client_service.cancelled_at else None,
            'status': client_service.get_status_display(),
        }
    
    return JsonResponse({'success': True, 'service': service_data})

@login_required
@require_http_methods(["POST", "GET"]) 
def connect_service(request, service_id):
    """Подключение услуги и возврат на предыдущую страницу с уведомлением."""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('banking_services')

    try:
        service = Service.objects.get(id=service_id, is_active=True)
    except Service.DoesNotExist:
        messages.error(request, 'Услуга не найдена')
        return redirect('banking_services')

    # Создаем/активируем подключение (идемпотентно)
    cs, created = ClientService.objects.get_or_create(client=client, service=service)
    cs.status = 'active'
    cs.is_active = True
    cs.save()

    messages.success(request, f'Услуга "{service.name}" успешно подключена')

    # Возврат на предыдущее место
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('banking_services')

@login_required
@require_http_methods(["POST", "GET"]) 
def disconnect_service(request, service_id):
    """Отключение услуги и возврат на предыдущую страницу с уведомлением."""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('banking_services')

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        messages.error(request, 'Услуга не найдена')
        return redirect('banking_services')

    cs = ClientService.objects.filter(client=client, service=service).first()
    if cs:
        cs.status = 'cancelled'
        cs.is_active = False
        cs.cancelled_at = timezone.now()
        cs.cancelled_by = request.user
        cs.save()
        messages.success(request, f'Услуга "{service.name}" отключена')
    else:
        messages.info(request, 'Услуга не была подключена')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('banking_services')

@login_required
def create_service_request(request):
    """Страница и обработчик создания заявки на услугу (реальный POST из формы и JSON)."""
    # Показ формы
    if request.method == 'GET':
        return render(request, 'create_service_request.html')

    # Обработка создания (поддержка form POST и JSON)
    try:
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Клиент не найден'})
            messages.error(request, 'Клиент не найден')
            return redirect('client_dashboard')

        # Данные из формы или JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body or '{}')
            service_name = (data.get('service_name') or '').strip()
            service_description = (data.get('description') or '').strip()
            price = data.get('price') or 0
        else:
            service_name = (request.POST.get('service_name') or '').strip()
            service_description = (request.POST.get('service_description') or '').strip()
            price = request.POST.get('price') or 0

        # Валидация
        if not service_name or service_description is None:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Заполните название и описание'})
            messages.error(request, 'Заполните название и описание')
            return redirect('create_service_request')

        try:
            price = float(price)
        except Exception:
            price = 0

        # Создаем заявку
        service_request = ServiceRequest.objects.create(
            client=client,
            service_name=service_name,
            service_description=service_description,
            price=price
        )

        # Ответ
        if request.content_type == 'application/json':
            return JsonResponse({'success': True, 'request_id': service_request.id})
        messages.success(request, 'Заявка успешно создана и отправлена на проверку')
        return redirect('client_dashboard')

    except Exception as e:
        logger.error(f"Error creating service request: {e}")
        if request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f'Ошибка при создании заявки: {str(e)}')
        return redirect('create_service_request')

@login_required
@require_http_methods(["POST"])
def connect_service(request, service_id):
    """Подключение услуги: JSON для AJAX, redirect с message для обычного запроса"""
    try:
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Клиент не найден'})
        
        # Получаем услугу
        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Услуга не найдена'})
        
        # Проверяем, не подключена ли уже услуга (только активные)
        if ClientService.objects.filter(client=client, service=service, status='active', is_active=True).exists():
            # Уже подключена — ведём себя как успех
            message = f'Услуга "{service.name}" уже подключена'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': message, 'service_id': service_id})
            messages.info(request, message)
            next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('banking_services')
        
        # Проверяем, была ли услуга ранее отключена
        existing_service = ClientService.objects.filter(client=client, service=service).first()
        
        if existing_service:
            # Если услуга была отключена, обновляем её статус
            from datetime import date, timedelta
            next_payment = date.today() + timedelta(days=30) if service.price > 0 else None
            
            existing_service.status = 'active'
            existing_service.is_active = True
            existing_service.monthly_fee = service.price
            existing_service.next_payment_date = next_payment
            existing_service.connected_at = timezone.now()
            existing_service.cancelled_at = None
            existing_service.cancelled_by = None
            existing_service.save()
            
            client_service = existing_service
            message = f'Услуга "{service.name}" успешно переподключена'
        else:
            # Создаем новую запись об услуге
            from datetime import date, timedelta
            next_payment = date.today() + timedelta(days=30) if service.price > 0 else None
            
            client_service = ClientService.objects.create(
                client=client,
                service=service,
                monthly_fee=service.price,
                next_payment_date=next_payment,
                status='active'
            )
            message = f'Услуга "{service.name}" успешно подключена'
        
        # Ответ в зависимости от типа запроса
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': message, 'service_id': service_id})
        messages.success(request, message)
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('banking_services')
        
    except Exception as e:
        logger.error(f"Error connecting service: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def disconnect_service(request, service_id):
    """Отключение услуги от учетной записи клиента"""
    try:
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Клиент не найден'})
        
        # Получаем подключенную услугу
        try:
            client_service = ClientService.objects.get(
                client=client, 
                service_id=service_id,
                status='active'
            )
        except ClientService.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Услуга не найдена или не подключена'})
        
        # Отключаем услугу
        from django.utils import timezone
        client_service.status = 'cancelled'
        client_service.cancelled_at = timezone.now()
        client_service.cancelled_by = request.user
        client_service.is_active = False
        client_service.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Услуга "{client_service.service.name}" успешно отключена',
            'service_id': service_id
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting service: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def my_services(request):
    """Страница управления подключенными услугами клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('login')
    
    # Получаем только активные подключенные услуги
    connected_services = ClientService.objects.filter(
        client=client,
        status='active',
        is_active=True
    ).select_related('service', 'service__category').order_by('-connected_at')
    
    # Статистика
    active_services = connected_services.count()
    total_monthly_fee = connected_services.aggregate(
        total=models.Sum('monthly_fee')
    )['total'] or 0
    
    context = {
        'client': client,
        'connected_services': connected_services,
        'active_services': active_services,
        'total_monthly_fee': total_monthly_fee,
    }
    
    return render(request, 'my_services.html', context)

@login_required
def deposits_view(request):
    """Страница депозитных программ"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем депозиты клиента
    deposits = Deposit.objects.filter(client=client).order_by('-created_at')
    
    # Получаем доступные депозитные программы из базы данных
    # Эти данные создаются при первом запуске через init_data.py
    deposit_programs = []  # TODO: Получить из базы данных
    
    context = {
        'deposits': deposits,
        'deposit_programs': deposit_programs,
        'client': client
    }
    
    return render(request, 'deposits.html', context)

@login_required
@require_http_methods(["POST"])
def create_deposit(request):
    """Создание нового депозита"""
    try:
        data = json.loads(request.body)
        
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Клиент не найден'})
        
        # Получаем или создаем депозитный счет
        deposit_account, created = BankAccount.objects.get_or_create(
            client=client,
            account_type='deposit',
            defaults={
                'account_number': f'DEP{client.client_id}{timezone.now().strftime("%Y%m%d%H%M%S")}',
                'balance': 0,
                'currency': 'RUB'
            }
        )
        
        # Создаем депозит
        amount = float(data.get('amount', 0))
        interest_rate = float(data.get('interest_rate', 0))
        term_months = int(data.get('term_months', 12))
        
        from datetime import date, timedelta
        start_date = date.today()
        end_date = start_date + timedelta(days=term_months * 30)
        
        deposit = Deposit.objects.create(
            client=client,
            account=deposit_account,
            amount=amount,
            interest_rate=interest_rate,
            term_months=term_months,
            start_date=start_date,
            end_date=end_date
        )
        
        # Пополняем счет
        deposit_account.balance += amount
        deposit_account.save()
        
        # Создаем транзакцию
        Transaction.objects.create(
            to_account=deposit_account,
            amount=amount,
            transaction_type='deposit',
            description=f'Открытие депозита "{data.get("program_name", "")}"',
            status='completed',
            completed_at=timezone.now()
        )
        
        return JsonResponse({'success': True, 'deposit_id': deposit.id})
        
    except Exception as e:
        logger.error(f"Error creating deposit: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def credits_view(request):
    """Страница кредитных продуктов"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем кредиты клиента
    credits = Credit.objects.filter(client=client).order_by('-created_at')
    
    # Получаем доступные кредитные программы из базы данных
    # Эти данные создаются при первом запуске через init_data.py
    credit_programs = []  # TODO: Получить из базы данных
    
    context = {
        'credits': credits,
        'credit_programs': credit_programs,
        'client': client
    }
    
    return render(request, 'credits.html', context)

@login_required
@require_http_methods(["POST"])
def create_credit_request(request):
    """Создание заявки на кредит"""
    try:
        data = json.loads(request.body)
        
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Клиент не найден'})
        
        # Создаем заявку на кредит (используем существующую модель ServiceRequest)
        credit_request = ServiceRequest.objects.create(
            client=client,
            service_name=f"Заявка на кредит: {data.get('program_name', '')}",
            service_description=f"""
Программа: {data.get('program_name', '')}
Сумма: {data.get('amount', 0)} ₽
Срок: {data.get('term_months', 0)} месяцев
Цель кредита: {data.get('purpose', '')}
Доход: {data.get('income', 0)} ₽
Стаж работы: {data.get('work_experience', 0)} месяцев
            """.strip(),
            price=data.get('amount', 0)
        )
        
        return JsonResponse({'success': True, 'request_id': credit_request.id})
        
    except Exception as e:
        logger.error(f"Error creating credit request: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def investments_view(request):
    """Страница инвестиционных продуктов"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем инвестиции клиента
    investments = ClientInvestment.objects.filter(client=client).order_by('-created_at')
    
    # Получаем доступные инвестиционные продукты из базы данных
    # Эти данные создаются при первом запуске через init_data.py
    investment_products = []  # TODO: Получить из базы данных
    
    context = {
        'investments': investments,
        'investment_products': investment_products,
        'client': client
    }
    
    return render(request, 'investments.html', context)

@login_required
@require_http_methods(["POST"])
def create_investment_request(request):
    """Создание заявки на инвестиционный продукт"""
    try:
        data = json.loads(request.body)
        
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Клиент не найден'})
        
        # Создаем заявку на инвестиционный продукт
        investment_request = ServiceRequest.objects.create(
            client=client,
            service_name=f"Заявка на инвестиционный продукт: {data.get('product_name', '')}",
            service_description=f"""
Продукт: {data.get('product_name', '')}
Сумма инвестиции: {data.get('amount', 0)} ₽
Уровень риска: {data.get('risk_level', '')}
Ожидаемая доходность: {data.get('expected_return', 0)}%
Опыт инвестирования: {data.get('investment_experience', '')}
Финансовые цели: {data.get('financial_goals', '')}
            """.strip(),
            price=data.get('amount', 0)
        )
        
        return JsonResponse({'success': True, 'request_id': investment_request.id})
        
    except Exception as e:
        logger.error(f"Error creating investment request: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def cards_view(request):
    """Страница банковских карт"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем карты клиента
    cards = BankCard.objects.filter(account__client=client).select_related('account').order_by('-created_at')
    
    # Получаем доступные типы карт из базы данных
    # Эти данные создаются при первом запуске через init_data.py
    card_programs = []  # TODO: Получить из базы данных
    
    context = {
        'cards': cards,
        'card_programs': card_programs,
        'client': client
    }
    
    return render(request, 'cards.html', context)

@login_required
@require_http_methods(["POST"])
def create_card_request(request):
    """Создание заявки на банковскую карту"""
    try:
        data = json.loads(request.body)
        
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Клиент не найден'})
        
        # Создаем заявку на карту
        card_request = ServiceRequest.objects.create(
            client=client,
            service_name=f"Заявка на карту: {data.get('card_name', '')}",
            service_description=f"""
Тип карты: {data.get('card_name', '')}
Доставка: {data.get('delivery_method', '')}
Дополнительные услуги: {data.get('additional_services', '')}
Доход: {data.get('income', 0)} ₽
Цель использования: {data.get('usage_purpose', '')}
            """.strip(),
            price=data.get('annual_fee', 0)
        )
        
        return JsonResponse({'success': True, 'request_id': card_request.id})
        
    except Exception as e:
        logger.error(f"Error creating card request: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def services_management(request):
    """Страница управления услугами клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем подключенные услуги
    connected_services = ClientService.objects.filter(
        client=client, 
        is_active=True,
        status='active'
    ).select_related('service')
    
    # Получаем заявки клиента
    service_requests = ServiceRequest.objects.filter(client=client).order_by('-created_at')
    
    # Получаем все доступные услуги для подключения
    available_services = Service.objects.filter(is_active=True, is_public=True).exclude(
        id__in=connected_services.values_list('service_id', flat=True)
    ).select_related('category')
    
    # Группируем услуги по категориям
    services_by_category = {}
    for service in available_services:
        category_name = service.category.name
        if category_name not in services_by_category:
            services_by_category[category_name] = []
        services_by_category[category_name].append(service)
    
    context = {
        'connected_services': connected_services,
        'service_requests': service_requests,
        'services_by_category': services_by_category,
        'client': client
    }
    
    return render(request, 'services_management.html', context)

def login_page(request):
    """Страница входа в систему (вход по email и паролю)"""
    if request.method == 'POST':
        email_input = request.POST.get('email')
        password = request.POST.get('password')
        
        print(f"Попытка входа (email): {email_input}")  # Отладочная информация
        
        # Ищем пользователя по email; для совместимости пробуем как username
        user_obj = None
        if email_input:
            user_obj = User.objects.filter(email=email_input).first()
            if not user_obj:
                user_obj = User.objects.filter(username=email_input).first()
        
        user = None
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            print(f"Пользователь аутентифицирован: {user.username}")  # Отладочная информация
            login(request, user)
            
            # Автоматическое определение роли и перенаправление
            if user.is_superuser or user.is_staff:
                return redirect('admin_dashboard')
            
            try:
                operator = Operator.objects.get(user=user)
                print(f"Найден оператор: {operator.operator_type}")
                if operator.operator_type == 'client_service':
                    return redirect('operator1_dashboard')
                if operator.operator_type == 'security':
                    return redirect('operator2_dashboard')
            except Operator.DoesNotExist:
                pass

            try:
                client = Client.objects.get(user=user)
                print(f"Найден клиент: {client.full_name}")
                return redirect('client_dashboard')
            except Client.DoesNotExist:
                pass

            # Если роль не сопоставлена
            messages.error(request, 'Для учетной записи не назначена роль')
            return redirect('login')
        else:
            print("Неверные учетные данные")  # Отладочная информация
            messages.error(request, 'Неверные email или пароль')
    
    return render(request, 'login.html')

def logout_view(request):
    """Выход из системы"""
    logout(request)
    return redirect('home')

@login_required
def client_dashboard(request):
    """Дашборд клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем счета клиента
    accounts = BankAccount.objects.filter(client=client)
    
    # Получаем карты клиента
    cards = BankCard.objects.filter(account__client=client).select_related('account')
    
    # Получаем подключенные услуги
    connected_services = ClientService.objects.filter(client=client, status='active', is_active=True).select_related('service', 'service__category')
    
    # Получаем заявки клиента
    service_requests = ServiceRequest.objects.filter(client=client).order_by('-created_at')
    
    # Получаем последние транзакции
    transactions = Transaction.objects.filter(
        models.Q(from_account__client=client) | models.Q(to_account__client=client)
    ).order_by('-created_at')[:10]
    
    # Получаем депозиты клиента
    deposits = Deposit.objects.filter(client=client, is_active=True)
    
    # Получаем кредиты клиента
    credits = Credit.objects.filter(client=client, status='active')
    
    # Общий баланс
    total_balance = accounts.aggregate(total=models.Sum('balance'))['total'] or 0
    
    context = {
        'client': client,
        'accounts': accounts,
        'cards': cards,
        'connected_services': connected_services,
        'service_requests': service_requests,
        'transactions': transactions,
        'deposits': deposits,
        'credits': credits,
        'total_balance': total_balance,
    }
    
    return render(request, 'client_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Админ-дашборд с полной статистикой"""
    if not is_admin(request.user):
        messages.error(request, 'Доступ запрещен. Требуются права администратора.')
        return redirect('home')
    
    # Статистика пользователей
    total_users = User.objects.count()
    total_clients = Client.objects.count()
    total_services = Service.objects.count()
    total_transactions = Transaction.objects.count()
    
    # Статистика атак
    recent_attacks = []
    attack_counts = {}
    
    # Статистика транзакций за неделю
    from datetime import datetime, timedelta
    week_ago = timezone.now() - timedelta(days=7)
    weekly_transactions = Transaction.objects.filter(completed_at__gte=week_ago).count()
    
    # Статистика по категориям услуг
    categories_stats = []
    for category in ServiceCategory.objects.all():
        count = Service.objects.filter(category=category).count()
        categories_stats.append({'name': category.name, 'count': count})
    
    context = {
        'total_users': total_users,
        'total_clients': total_clients,
        'total_services': total_services,
        'total_transactions': total_transactions,
        'recent_attacks': recent_attacks,
        'attack_counts': attack_counts,
        'weekly_transactions': weekly_transactions,
        'categories_stats': categories_stats,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def client_dashboard(request):
    """Дашборд клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем счета клиента
    accounts = BankAccount.objects.filter(client=client)
    
    # Получаем карты клиента
    cards = BankCard.objects.filter(account__client=client).select_related('account')
    
    # Получаем подключенные услуги
    connected_services = ClientService.objects.filter(client=client, status='active', is_active=True).select_related('service', 'service__category')
    
    # Получаем заявки клиента
    service_requests = ServiceRequest.objects.filter(client=client).order_by('-created_at')
    
    # Получаем последние транзакции
    transactions = Transaction.objects.filter(
        models.Q(from_account__client=client) | models.Q(to_account__client=client)
    ).order_by('-created_at')[:10]
    
    # Получаем депозиты клиента
    deposits = Deposit.objects.filter(client=client, is_active=True)
    
    # Получаем кредиты клиента
    credits = Credit.objects.filter(client=client, status='active')
    
    # Общий баланс
    total_balance = accounts.aggregate(total=models.Sum('balance'))['total'] or 0
    
    context = {
        'client': client,
        'accounts': accounts,
        'cards': cards,
        'connected_services': connected_services,
        'service_requests': service_requests,
        'transactions': transactions,
        'deposits': deposits,
        'credits': credits,
        'total_balance': total_balance,
    }
    
    return render(request, 'client_dashboard.html', context)



@login_required
def operator1_dashboard(request):
    """Дашборд оператора ДБО #1 (Отдел клиентского обслуживания)"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='client_service')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен. Требуются права оператора ДБО #1.')
        return redirect('home')
    
    # Получаем фишинговые письма для демонстрации атаки
    phishing_emails = PhishingEmail.objects.all().order_by('-sent_at')
    
    # Получаем заявки на создание клиентов
    client_requests = ServiceRequest.objects.filter(
        service_name__icontains='регистрация'
    ).order_by('-created_at')
    
    # Статистика
    total_emails = phishing_emails.count()
    unread_emails = phishing_emails.filter(is_opened=False).count()
    pending_requests = client_requests.filter(status='pending').count()
    
    context = {
        'operator': operator,
        'phishing_emails': phishing_emails[:10],  # Последние 10 писем
        'client_requests': client_requests[:10],  # Последние 10 заявок
        'total_emails': total_emails,
        'unread_emails': unread_emails,
        'pending_requests': pending_requests,
    }
    
    return render(request, 'operator1_dashboard.html', context)

@login_required
def operator2_dashboard(request):
    """Дашборд оператора ДБО #2 (Отдел безопасности/валидации)"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='security')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен. Требуются права оператора ДБО #2.')
        return redirect('home')
    
    # Получаем заявки на создание услуг для валидации
    service_requests = ServiceRequest.objects.filter(
        status='pending'
    ).exclude(
        service_name__icontains='регистрация'
    ).order_by('-created_at')
    
    # Получаем недавно одобренные заявки
    approved_requests = ServiceRequest.objects.filter(
        status='approved'
    ).order_by('-reviewed_at')[:10]
    
    # Статистика
    pending_requests = service_requests.count()
    approved_today = ServiceRequest.objects.filter(
        status='approved',
        reviewed_at__date=timezone.now().date()
    ).count()
    
    context = {
        'operator': operator,
        'service_requests': service_requests,
        'approved_requests': approved_requests,
        'pending_requests': pending_requests,
        'approved_today': approved_today,
    }
    
    return render(request, 'operator2_dashboard.html', context)

@login_required
def create_client(request):
    """Создание нового клиента (функционал оператора ДБО #1)"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='client_service')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен. Требуются права оператора ДБО #1.')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            # Получаем данные из формы (в шаблоне нет username/password, генерируем при необходимости)
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()

            if not full_name or not email or not phone:
                messages.error(request, 'Пожалуйста, заполните обязательные поля: имя, email, телефон')
                return redirect('create_client')

            # Username = email, проверяем уникальность
            if User.objects.filter(username=email).exists():
                messages.error(request, 'Пользователь с таким email уже существует')
                return redirect('create_client')

            # Создаем пользователя Django без пароля (попросим установить при первом входе)
            user = User.objects.create(
                username=email,
                email=email
            )
            user.set_unusable_password()
            user.save()

            # Генерируем client_id
            client_id = f"CLI{timezone.now().strftime('%Y%m%d%H%M%S')}"

            # Создаем клиента
            client = Client.objects.create(
                user=user,
                client_id=client_id,
                full_name=full_name,
                email=email,
                phone=phone,
                is_active=True,
                is_verified=False,
                created_by=operator
            )

            # Создаем основной банковский счет
            BankAccount.objects.create(
                client=client,
                account_number=f"ACC{client.client_id}{timezone.now().strftime('%Y%m%d%H%M%S')}",
                account_type='current',
                balance=0,
                currency='RUB'
            )

            messages.success(request, f"Клиент {full_name} создан. Логин для входа: {email}. Пароль будет установлен при первом входе.")
            
            # Логирование атак отключено
            
            return redirect('operator1_dashboard')
            
        except Exception as e:
            messages.error(request, f'Ошибка при создании клиента: {str(e)}')
    
    return render(request, 'create_client.html')

@login_required
def phishing_email_view(request, email_id):
    """Просмотр фишингового письма (уязвимость для демонстрации атаки)"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='client_service')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен. Требуются права оператора ДБО #1.')
        return redirect('home')
    
    try:
        email = PhishingEmail.objects.get(id=email_id)
    except PhishingEmail.DoesNotExist:
        messages.error(request, 'Письмо не найдено')
        return redirect('operator1_dashboard')
    
    # Отмечаем письмо как прочитанное
    email.is_opened = True
    email.opened_at = timezone.now()
    email.save()
    
    # Логирование атак отключено
    
    context = {
        'email': email,
        'operator': operator,
    }
    
    return render(request, 'phishing_email.html', context)

@login_required
def review_service_request(request, request_id):
    """Просмотр заявки на услугу (функционал оператора ДБО #2)"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='security')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен. Требуются права оператора ДБО #2.')
        return redirect('home')
    
    try:
        service_request = ServiceRequest.objects.get(id=request_id)
    except ServiceRequest.DoesNotExist:
        messages.error(request, 'Заявка не найдена')
        return redirect('operator2_dashboard')
    
    # УЯЗВИМОСТЬ: XSS в описании услуги - не санитизированный пользовательский ввод
    # Это позволяет злоумышленнику внедрить JavaScript код
    
    context = {
        'service_request': service_request,
        'operator': operator,
    }
    
    return render(request, 'review_service_request.html', context)

@login_required
@require_http_methods(["POST"])
def approve_service_request(request, request_id):
    """Одобрение заявки на услугу (функционал оператора ДБО #2)"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='security')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен')
        return redirect('operator2_dashboard')
    
    try:
        service_request = ServiceRequest.objects.get(id=request_id)
    except ServiceRequest.DoesNotExist:
        messages.error(request, 'Заявка не найдена')
        return redirect('operator2_dashboard')
    
    # Одобряем заявку
    service_request.status = 'approved'
    service_request.reviewed_by = operator
    service_request.reviewed_at = timezone.now()
    service_request.save()
    
    # Создаем услугу в каталоге
    # Гарантируем наличие категории
    category, _ = ServiceCategory.objects.get_or_create(
        name='Дополнительные услуги', defaults={'description': 'Пользовательские услуги', 'is_public': True}
    )
    Service.objects.create(
        name=service_request.service_name,
        description=service_request.service_description,
        price=service_request.price,
        category=category,
        is_public=True,
        is_active=True,
    )
    
    # Логирование атак отключено
    
    messages.success(request, 'Заявка одобрена, услуга добавлена в каталог')
    return redirect('operator2_dashboard')

@login_required
def accounts_view(request):
    """Страница счетов клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем счета клиента
    accounts = BankAccount.objects.filter(client=client).order_by('-created_at')
    
    # Статистика
    total_balance = accounts.aggregate(total=models.Sum('balance'))['total'] or 0
    active_accounts = accounts.filter(is_active=True).count()
    
    context = {
        'client': client,
        'accounts': accounts,
        'total_balance': total_balance,
        'active_accounts': active_accounts,
    }
    
    return render(request, 'accounts.html', context)

@login_required
@require_http_methods(["POST"]) 
def create_bank_account(request):
    """Создает банковский счет для текущего клиента и возвращает назад с уведомлением."""
    # Получаем клиента
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('accounts')

    account_type = (request.POST.get('account_type') or '').strip()
    initial_deposit_raw = request.POST.get('initial_deposit') or '0'
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')

    # Валидируем тип счета (разрешаем только безопасные значения)
    allowed_types = {'checking', 'savings'}
    if account_type not in allowed_types:
        messages.error(request, 'Неверный тип счета')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('accounts')

    # Парсим сумму
    try:
        initial_deposit = Decimal(str(initial_deposit_raw))
        if initial_deposit < 0:
            raise ValueError
    except Exception:
        messages.error(request, 'Неверная сумма начального взноса')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('accounts')

    # Генерируем уникальный номер счета
    base = f"40817{timezone.now().strftime('%m%d%H%M%S')}{client.id:02d}"
    account_number = base[:20] if len(base) > 20 else base.ljust(20, '0')
    # Разрешаем потенциальные коллизии
    suffix = 0
    while BankAccount.objects.filter(account_number=account_number).exists():
        suffix += 1
        tail = f"{suffix:02d}"
        account_number = (base + tail)[:20]

    # Создаем счет
    BankAccount.objects.create(
        client=client,
        account_number=account_number,
        account_type=account_type,
        balance=initial_deposit,
        currency='RUB',
        is_active=True,
    )

    messages.success(request, f'Счет успешно открыт. Номер: {account_number}')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('accounts')

@login_required
def transfers_view(request):
    """Страница переводов"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем счета клиента для переводов
    accounts = BankAccount.objects.filter(client=client, is_active=True)
    
    # Получаем последние переводы
    recent_transfers = Transaction.objects.filter(
        models.Q(from_account__client=client) | models.Q(to_account__client=client)
    ).order_by('-created_at')[:10]
    
    context = {
        'client': client,
        'accounts': accounts,
        'recent_transfers': recent_transfers,
    }
    
    return render(request, 'transfers.html', context)

@login_required
def history_view(request):
    """Страница истории операций"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем все транзакции клиента
    transactions = Transaction.objects.filter(
        models.Q(from_account__client=client) | models.Q(to_account__client=client)
    ).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    total_transactions = transactions.count()
    completed_transactions = transactions.filter(status='completed').count()
    total_amount = transactions.filter(status='completed').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    context = {
        'client': client,
        'page_obj': page_obj,
        'total_transactions': total_transactions,
        'completed_transactions': completed_transactions,
        'total_amount': total_amount,
    }
    
    return render(request, 'history.html', context)

@login_required
def settings_view(request):
    """Страница настроек клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    if request.method == 'POST':
        # Обновляем данные клиента
        client.full_name = request.POST.get('full_name', client.full_name)
        client.email = request.POST.get('email', client.email)
        client.phone = request.POST.get('phone', client.phone)
        client.save()
        
        # Обновляем данные пользователя Django
        user = request.user
        user.email = client.email
        user.save()
        
        messages.success(request, 'Настройки успешно сохранены')
        return redirect('settings')
    
    context = {
        'client': client,
    }
    
    return render(request, 'settings.html', context)

# Старые маршруты для совместимости
@login_required
def accounts(request):
    """Старый маршрут для счетов"""
    return accounts_view(request)

@login_required
def transfers(request):
    """Старый маршрут для переводов"""
    return transfers_view(request)

@login_required
def history(request):
    """Старый маршрут для истории"""
    return history_view(request)

@login_required
def settings(request):
    """Старый маршрут для настроек"""
    return settings_view(request)

@login_required
def dashboard(request):
    """Старый маршрут для дашборда"""
    return client_dashboard(request)

# Новые банковские сервисы
@login_required
def accounts_service(request):
    """Страница расчетно-кассового обслуживания"""
    try:
        client = Client.objects.get(user=request.user)
        accounts = BankAccount.objects.filter(client=client, is_active=True)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'accounts': accounts,
    }
    
    return render(request, 'accounts.html', context)

@login_required
def credits_service(request):
    """Страница кредитных продуктов"""
    try:
        client = Client.objects.get(user=request.user)
        credits = Credit.objects.filter(client=client)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'credits': credits,
    }
    
    return render(request, 'credits.html', context)

@login_required
def deposits_service(request):
    """Страница депозитных программ"""
    try:
        client = Client.objects.get(user=request.user)
        accounts = BankAccount.objects.filter(client=client, is_active=True)
        deposits = Deposit.objects.filter(client=client)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'accounts': accounts,
        'deposits': deposits,
    }
    
    return render(request, 'deposits.html', context)

@login_required
def transfers_service(request):
    """Страница переводов и платежей"""
    try:
        client = Client.objects.get(user=request.user)
        accounts = BankAccount.objects.filter(client=client, is_active=True)
        transactions = Transaction.objects.filter(
            models.Q(from_account__client=client) | models.Q(to_account__client=client)
        ).order_by('-created_at')[:20]
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'accounts': accounts,
        'transactions': transactions,
    }
    
    return render(request, 'transfers.html', context)

@login_required
def cards_service(request):
    """Страница банковских карт"""
    try:
        client = Client.objects.get(user=request.user)
        accounts = BankAccount.objects.filter(client=client, is_active=True)
        cards = BankCard.objects.filter(account__client=client, is_active=True)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'accounts': accounts,
        'cards': cards,
    }
    
    return render(request, 'cards.html', context)

@login_required
def investments_service(request):
    """Страница инвестиционных продуктов"""
    try:
        client = Client.objects.get(user=request.user)
        accounts = BankAccount.objects.filter(client=client, is_active=True)
        investments = ClientInvestment.objects.filter(client=client)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'accounts': accounts,
        'investments': investments,
    }
    
    return render(request, 'investments.html', context)

@login_required
def client_dashboard(request):
    """Личный кабинет клиента с отображением всех банковских сервисов"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем все банковские данные клиента
    accounts = BankAccount.objects.filter(client=client, is_active=True)
    cards = BankCard.objects.filter(account__client=client, is_active=True)
    credits = Credit.objects.filter(client=client)
    deposits = Deposit.objects.filter(client=client)
    investments = ClientInvestment.objects.filter(client=client)
    transactions = Transaction.objects.filter(
        models.Q(from_account__client=client) | models.Q(to_account__client=client)
    ).order_by('-created_at')[:5]
    
    # Подключенные услуги
    connected_services = ClientService.objects.filter(client=client, status='active')
    
    # Общая стоимость услуг
    total_cost = sum(service.monthly_fee for service in connected_services)
    
    # Статистика
    total_balance = sum(account.balance for account in accounts)
    total_credit_debt = sum(credit.remaining_amount for credit in credits if credit.status == 'active')
    total_deposit_amount = sum(deposit.amount for deposit in deposits)
    total_investment_value = sum(investment.current_value for investment in investments if investment.status == 'active')
    
    context = {
        'client': client,
        'accounts': accounts,
        'cards': cards,
        'credits': credits,
        'deposits': deposits,
        'investments': investments,
        'transactions': transactions,
        'connected_services': connected_services,
        'total_cost': total_cost,
        'total_balance': total_balance,
        'total_credit_debt': total_credit_debt,
        'total_deposit_amount': total_deposit_amount,
        'total_investment_value': total_investment_value,
    }
    
    return render(request, 'client_dashboard.html', context)


