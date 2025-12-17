from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import connection, models
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from decimal import Decimal
import json
import logging
import secrets
import string

from .models import (
    Operator,
    Client,
    Service,
    ClientService,
    ServiceCategory,
    BankCard,
    Transaction,
    Deposit,
    Credit,
    InvestmentProduct,
    ClientInvestment,
    ServiceRequest,
    News,
    DBOLog,
)
from django.contrib.auth.models import User
from .logging_helper import log_from_request

logger = logging.getLogger(__name__)

def home(request):
    """Главная страница системы ДБО"""
    return render(request, 'index.html')
def banking_services(request):
    q = request.GET.get('q', '')
    price_filter = request.GET.get('price', 'all').strip()
    sort_by = request.GET.get('sort', 'name').strip()
    category_name = request.GET.get('category', '').strip()

    categories = ServiceCategory.objects.exclude(name__icontains='Служебные').prefetch_related('service_set')
    if not category_name and categories.exists():
        category_name = categories.first().name

    where_clauses = ["s.is_active = true"]
    if category_name:
        where_clauses.append(f"c.name = '{category_name}'")
    if q:
        # УЯЗВИМОСТЬ: SQL-инъекция - прямая подстановка пользовательского ввода
        where_clauses.append(f"(s.name LIKE '%{q}%' OR s.description LIKE '%{q}%')")
    if price_filter == 'free':
        where_clauses.append("s.price = 0")
    elif price_filter == 'low':
        where_clauses.append("s.price > 0 AND s.price <= 1000")
    elif price_filter == 'medium':
        where_clauses.append("s.price > 1000 AND s.price <= 5000")
    elif price_filter == 'high':
        where_clauses.append("s.price > 5000")

    order_map = {'name': 's.name', 'price-low': 's.price ASC', 'price-high': 's.price DESC', 'popular': 's.rating_count DESC'}
    order_by = order_map.get(sort_by, 's.name')

    sql = f"""SELECT s.id, s.uuid, s.name, s.description, s.price, s.is_active, s.rating, s.rating_count, c.name as category_name
              FROM dbo_service s JOIN dbo_servicecategory c ON s.category_id = c.id
              WHERE {' AND '.join(where_clauses)} ORDER BY {order_by}"""

    services_rows = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            services_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except:
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.id, s.uuid, s.name, s.description, s.price, s.is_active, s.rating, s.rating_count, c.name as category_name FROM dbo_service s JOIN dbo_servicecategory c ON s.category_id = c.id WHERE s.is_active = true ORDER BY s.name")
            columns = [col[0] for col in cursor.description]
            services_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    connected_services = set()
    if request.user.is_authenticated:
        try:
            client = Client.objects.get(user=request.user)
            connected_services = set(ClientService.objects.filter(client=client, status='active').values_list('service_id', flat=True))
        except Client.DoesNotExist:
            pass

    services_by_category = {}
    for service in services_rows:
        # UUID уже есть из SQL-запроса, конвертируем в строку
        if service.get('uuid'):
            service['uuid'] = str(service['uuid'])
        services_by_category.setdefault(service.get('category_name', 'Без категории'), []).append(service)

    return render(request, 'banking_services.html', {
        'categories': categories,
        'services_by_category': services_by_category,
        'connected_services': connected_services,
        'total_services': len(services_rows),
        'free_services': sum(1 for s in services_rows if float(s.get('price', 0)) == 0),
        'q': q, 'price': price_filter, 'sort': sort_by, 'category_active': category_name,
    })

@login_required
def service_detail(request, service_uuid):
    """Детальная информация об услуге"""
    service = get_object_or_404(Service, uuid=service_uuid, is_active=True)
    is_connected = False
    try:
        client = Client.objects.get(user=request.user)
        is_connected = ClientService.objects.filter(client=client, service=service, is_active=True).exists()
    except Client.DoesNotExist:
        pass
    return render(request, 'services/detail.html', {'service': service, 'is_connected': is_connected})

@login_required
@require_http_methods(["POST", "GET"]) 
def connect_service(request, service_uuid):
    """Подключение услуги и возврат на предыдущую страницу с уведомлением."""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('banking_services')

    try:
        service = Service.objects.get(uuid=service_uuid, is_active=True)
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
def connect_service(request, service_uuid):
    """Подключение услуги: JSON для AJAX, redirect с message для обычного запроса"""
    try:
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Клиент не найден'})
        
        # Получаем услугу
        try:
            service = Service.objects.get(uuid=service_uuid, is_active=True)
        except Service.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Услуга не найдена'})
        
        # Проверяем, не подключена ли уже услуга (только активные)
        if ClientService.objects.filter(client=client, service=service, status='active', is_active=True).exists():
            # Уже подключена — ведём себя как успех
            message = f'Услуга "{service.name}" уже подключена'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': message, 'service_uuid': str(service.uuid)})
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
        
        # Сразу списываем стоимость услуги (первый платеж), если услуга платная
        if service.price and service.price > 0:
            # Ищем карту списания: основная или первая активная
            from_card = None
            if hasattr(client, 'primary_card') and client.primary_card and client.primary_card.is_active:
                from_card = client.primary_card
            if not from_card:
                from_card = BankCard.objects.filter(client=client, is_active=True).first()

            if not from_card:
                # Нет активных карт — откатывать не будем, просто уведомим пользователя
                warn_msg = 'У клиента нет активных карт для списания оплаты услуги'
                logger.warning(warn_msg)
                messages.warning(request, warn_msg)
            else:
                # Проверяем баланс
                price_amount = Decimal(service.price)
                if from_card.balance < price_amount:
                    # Недостаточно средств — отключаем обратно и сообщаем
                    client_service.status = 'cancelled'
                    client_service.is_active = False
                    client_service.cancelled_at = timezone.now()
                    client_service.save(update_fields=['status','is_active','cancelled_at'])
                    err_msg = f'Недостаточно средств для оплаты услуги "{service.name}"'
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                        return JsonResponse({'success': False, 'error': err_msg}, status=400)
                    messages.error(request, err_msg)
                    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
                    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                        return redirect(next_url)
                    return redirect('banking_services')

                # Списываем и создаем транзакцию
                from_card.balance -= price_amount
                from_card.save(update_fields=['balance'])

                Transaction.objects.create(
                    from_card=from_card,
                    to_card=None,
                    amount=price_amount,
                    currency='RUB',
                    transaction_type='payment',
                    description=f'Оплата подключения услуги "{service.name}"',
                    status='completed',
                    completed_at=timezone.now()
                )

        # Ответ в зависимости от типа запроса
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': message, 'service_uuid': str(service.uuid)})
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
def disconnect_service(request, service_uuid):
    """Отключение услуги"""
    try:
        client = Client.objects.get(user=request.user)
        service = Service.objects.get(uuid=service_uuid)
        client_service = ClientService.objects.get(client=client, service=service, status='active')
        client_service.status = 'cancelled'
        client_service.cancelled_at = timezone.now()
        client_service.cancelled_by = request.user
        client_service.is_active = False
        client_service.save()
        return JsonResponse({'success': True, 'message': f'Услуга "{client_service.service.name}" отключена', 'service_uuid': str(service.uuid)})
    except (Client.DoesNotExist, ClientService.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Услуга не найдена или не подключена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def my_services(request):
    """Подключенные услуги клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('login')
    services = ClientService.objects.filter(client=client, status='active', is_active=True).select_related('service', 'service__category').order_by('-connected_at')
    return render(request, 'my_services.html', {'client': client, 'connected_services': services, 'active_services': services.count(), 'total_monthly_fee': services.aggregate(total=models.Sum('monthly_fee'))['total'] or 0})

@login_required
def my_requests(request):
    """Заявки клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('login')
    requests_qs = ServiceRequest.objects.filter(client=client).order_by('-created_at')
    return render(request, 'my_requests.html', {'client': client, 'service_requests': requests_qs, 'total_requests': requests_qs.count(), 'pending_requests': requests_qs.filter(status='pending').count()})

@login_required
def deposits_view(request):
    """Депозитные программы"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    return render(request, 'deposits.html', {'client': client, 'deposits': Deposit.objects.filter(client=client).order_by('-created_at'), 'cards': BankCard.objects.filter(client=client, is_active=True), 'deposit_programs': []})

@login_required
@require_http_methods(["POST"])
def create_deposit(request):
    """Создание заявки на депозит (фикция - объект не создается)"""
    try:
        # Поддержка как JSON, так и form-data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Клиент не найден'})
            messages.error(request, 'Клиент не найден')
            return redirect('deposits_service')
        
        # Извлекаем данные
        amount = data.get('amount', 0) or data.get('uAmount', 0)
        interest_rate = data.get('interest_rate', 0) or data.get('rate', 0)
        term_months = data.get('term_months', 12) or data.get('term', 12)
        program_name = data.get('program_name', 'Стандартный депозит')
        
        # Создаем заявку на депозит (используем существующую модель ServiceRequest)
        deposit_request = ServiceRequest.objects.create(
            client=client,
            service_name=f"Заявка на депозит: {program_name}",
            service_description=f"""
Программа: {program_name}
Сумма: {amount} ₽
Срок: {term_months} месяцев
Процентная ставка: {interest_rate}%
            """.strip(),
            price=float(amount) if amount else 0
        )
        
        if request.content_type == 'application/json':
            return JsonResponse({'success': True, 'request_id': deposit_request.id, 'message': 'Заявка успешно оставлена'})
        
        messages.success(request, 'Спасибо! Наш менеджер свяжется с вами для подтверждения заявки на депозит.')
        return redirect('deposits_service')
        
    except Exception as e:
        logger.error(f"Error creating deposit request: {e}")
        if request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f'Ошибка при создании заявки: {str(e)}')
        return redirect('deposits_service')

@login_required
@require_http_methods(["POST"])
def create_deposit_request(request):
    """Создание заявки на депозит"""
    try:
        # Поддержка как JSON, так и form-data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # Получаем клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Клиент не найден'})
            messages.error(request, 'Клиент не найден')
            return redirect('deposits_service')
        
        # Извлекаем данные
        tariff = data.get('tariff', '')
        amount = data.get('amount', 0) or data.get('uAmount', 0)
        
        # Парсим тариф (например, t6_70 означает 6 месяцев, 7.0%)
        tariff_parts = tariff.split('_')
        term_months = 6
        interest_rate = 7.0
        
        if len(tariff_parts) >= 2:
            term_str = tariff_parts[0].replace('t', '').replace('r', '')
            rate_str = tariff_parts[1]
            try:
                term_months = int(term_str)
                interest_rate = float(rate_str) / 10.0
            except:
                pass
        
        # Создаем заявку на депозит (используем существующую модель ServiceRequest)
        deposit_request = ServiceRequest.objects.create(
            client=client,
            service_name=f"Заявка на депозит: Тариф {tariff}",
            service_description=f"""
Тариф: {tariff}
Сумма: {amount} ₽
Срок: {term_months} месяцев
Процентная ставка: {interest_rate}%
            """.strip(),
            price=float(amount) if amount else 0
        )
        
        messages.success(request, 'Спасибо! Наш менеджер свяжется с вами для подтверждения заявки на депозит.')
        
        if request.content_type == 'application/json':
            return JsonResponse({'success': True, 'request_id': deposit_request.id, 'redirect': '/client/deposits/'})
        
        return redirect('deposits')
        
    except Exception as e:
        logger.error(f"Error creating deposit request: {e}")
        if request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f'Ошибка при создании заявки: {str(e)}')
        return redirect('deposits_service')

@login_required
def credits_view(request):
    """Кредитные продукты"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    return render(request, 'credits.html', {'client': client, 'credits': Credit.objects.filter(client=client).order_by('-created_at'), 'credit_programs': []})

@login_required
@require_http_methods(["POST"])
def create_credit_request(request):
    """Заявка на кредит"""
    try:
        data = json.loads(request.body)
        client = Client.objects.get(user=request.user)
        req = ServiceRequest.objects.create(client=client, service_name=f"Заявка на кредит: {data.get('program_name', '')}", service_description=f"Программа: {data.get('program_name', '')}\nСумма: {data.get('amount', 0)} ₽\nСрок: {data.get('term_months', 0)} мес", price=data.get('amount', 0))
        return JsonResponse({'success': True, 'request_id': req.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def investments_view(request):
    """Инвестиционные продукты"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    return render(request, 'investments.html', {'client': client, 'investments': ClientInvestment.objects.filter(client=client).order_by('-created_at'), 'investment_products': []})

@login_required
@require_http_methods(["POST"])
def create_investment_request(request):
    """Заявка на инвестиции"""
    try:
        data = json.loads(request.body)
        client = Client.objects.get(user=request.user)
        req = ServiceRequest.objects.create(client=client, service_name=f"Заявка на инвестиции: {data.get('product_name', '')}", service_description=f"Продукт: {data.get('product_name', '')}\nСумма: {data.get('amount', 0)} ₽\nРиск: {data.get('risk_level', '')}", price=data.get('amount', 0))
        return JsonResponse({'success': True, 'request_id': req.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def cards_view(request):
    """Банковские карты"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    return render(request, 'cards.html', {'client': client, 'cards': BankCard.objects.filter(client=client, is_active=True), 'card_programs': []})

@login_required
@require_http_methods(["POST"])
def create_card_request(request):
    """Заявка на карту"""
    try:
        data = json.loads(request.body)
        client = Client.objects.get(user=request.user)
        req = ServiceRequest.objects.create(client=client, service_name=f"Заявка на карту: {data.get('card_name', '')}", service_description=f"Тип: {data.get('card_name', '')}\nДоставка: {data.get('delivery_method', '')}", price=data.get('annual_fee', 0))
        return JsonResponse({'success': True, 'request_id': req.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def create_card(request):
    """Создание реальной банковской карты, привязанной к счету клиента."""
    try:
        # Поддержка form-urlencoded и JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body or '{}')
            card_type = (data.get('card_type') or '').strip()
            initial_amount_raw = data.get('initial_amount')
            credit_initial_raw = data.get('credit_initial')
        else:
            card_type = (request.POST.get('card_type') or '').strip()
            initial_amount_raw = request.POST.get('initial_amount')
            credit_initial_raw = request.POST.get('credit_initial')

        # Валидация клиента
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Клиент не найден'}, status=400)

        # Валидация типа карты
        if card_type not in {'debit', 'credit'}:
            return JsonResponse({'success': False, 'error': 'Неверный тип карты'}, status=400)

        # Определяем счет для карты
        if card_type == 'credit':
            # Начальный баланс кредитного счета (неотрицательный)
            try:
                initial_balance = Decimal(str(credit_initial_raw or '0'))
                if initial_balance < 0:
                    raise ValueError
            except Exception:
                return JsonResponse({'success': False, 'error': 'Неверная начальная сумма для кредитного счета'}, status=400)

            # Для кредитной карты открываем отдельный кредитный счет с "нормальным" (цифровым) номером
            # Формируем 19-значный номер: префикс + MMddHHmmss + client_id (2 знака) + добивка нулями
            base = f"42307{timezone.now().strftime('%m%d%H%M%S')}{client.id:02d}"
            card_number = base[:19] if len(base) > 19 else base.ljust(19, '0')
            suffix = 0
            while BankCard.objects.filter(card_number=card_number).exists():
                suffix += 1
                tail = f"{suffix:02d}"
                card_number = (base + tail)[:19]

            from datetime import date, timedelta
            expiry_date = date.today() + timedelta(days=365*5)  # Карта действует 5 лет

            card = BankCard.objects.create(
                client=client,
                card_number=card_number,
                card_type='credit',
                balance=initial_balance,
                currency='RUB',
                expiry_date=expiry_date,
                is_active=True,
            )
        else:
            # Для дебетовой карты: создаем новую карту с начальной суммой
            try:
                initial_balance = Decimal(str(initial_amount_raw or '0'))
                if initial_balance < 0:
                    raise ValueError
            except Exception:
                return JsonResponse({'success': False, 'error': 'Неверная начальная сумма для дебетовой карты'}, status=400)

            base = f"40817{timezone.now().strftime('%m%d%H%M%S')}{client.id:02d}"
            card_number = base[:19] if len(base) > 19 else base.ljust(19, '0')
            suffix = 0
            while BankCard.objects.filter(card_number=card_number).exists():
                suffix += 1
                tail = f"{suffix:02d}"
                card_number = (base + tail)[:19]

            from datetime import date, timedelta
            expiry_date = date.today() + timedelta(days=365*5)  # Карта действует 5 лет

            card = BankCard.objects.create(
                client=client,
                card_number=card_number,
                card_type='debit',
                balance=initial_balance,
                currency='RUB',
                expiry_date=expiry_date,
                is_active=True,
            )

        # Генерация номера карты (маскированного вида #### #### #### ####)
        # Используем псевдогенерацию: BIN по типу + timestamp + client id; храним как маску
        ts = timezone.now().strftime('%m%d%H%M%S')
        bin_prefix = '5100' if card_type == 'debit' else '5300'
        raw = f"{bin_prefix}{client.id:02d}{ts}"
        # Берем последние 16 символов и форматируем 4-4-4-4
        digits = (raw[-16:]).ljust(16, '0')
        masked_number = f"{digits[0:4]} {digits[4:8]} {digits[8:12]} {digits[12:16]}"

        # Срок действия: 3 года от текущей даты, день = 1 для упрощения
        from datetime import date
        expiry_year = date.today().year + 3
        expiry_month = date.today().month
        expiry_date = date(expiry_year, expiry_month, 1)

        # Дневной лимит по умолчанию (можно кастомизировать в будущем)
        daily_limit = Decimal('100000.00')

        # Обновляем созданную карту с маскированным номером
        card.card_number = masked_number
        card.expiry_date = expiry_date
        card.daily_limit = daily_limit
        card.save()

        # Если это первая карта клиента, автоматически делаем её основной
        if not client.primary_card:
            client.primary_card = card
            client.save(update_fields=['primary_card'])

        return JsonResponse({
            'success': True,
            'card_id': card.id,
            'card_number': card.card_number,
            'expiry': f"{expiry_month:02d}/{expiry_year}",
        })

    except Exception as e:
        logger.error(f"Error creating card: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def block_card(request, card_id):
    """Блокировка карты"""
    try:
        card = BankCard.objects.get(id=card_id, client__user=request.user)
        if not card.is_active:
            return JsonResponse({'success': True, 'message': 'Карта уже заблокирована'})
        card.is_active = False
        card.save(update_fields=['is_active'])
        return JsonResponse({'success': True, 'message': 'Карта заблокирована'})
    except BankCard.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Карта не найдена'}, status=404)

@login_required
@require_http_methods(["POST"])
def unblock_card(request, card_id):
    """Разблокировка карты"""
    try:
        card = BankCard.objects.get(id=card_id, client__user=request.user)
        if card.is_active:
            return JsonResponse({'success': True, 'message': 'Карта уже активна'})
        card.is_active = True
        card.save(update_fields=['is_active'])
        return JsonResponse({'success': True})
    except BankCard.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Карта не найдена'}, status=404)

@login_required
@require_http_methods(["POST"])
def change_card_pin(request, card_id):
    """Смена PIN-кода"""
    try:
        BankCard.objects.get(id=card_id, client__user=request.user)
        data = json.loads(request.body or '{}')
        new_pin = (data.get('new_pin') or '').strip()
        if not (len(new_pin) == 4 and new_pin.isdigit()):
            return JsonResponse({'success': False, 'error': 'PIN должен состоять из 4 цифр'}, status=400)
        return JsonResponse({'success': True})
    except BankCard.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Карта не найдена'}, status=404)

def login_page(request):
    """Вход в систему"""
    if request.method == 'POST':
        email_input = request.POST.get('email')
        password = request.POST.get('password')

        user_obj = (
            User.objects.filter(email=email_input).first()
            or User.objects.filter(username=email_input).first()
            if email_input
            else None
        )
        user = authenticate(request, username=user_obj.username, password=password) if user_obj else None

        if user:
            login(request, user)

            # Отладочное логирование IP заголовков
            ip_debug = {
                'HTTP_X_FORWARDED_FOR': request.META.get('HTTP_X_FORWARDED_FOR'),
                'HTTP_X_REAL_IP': request.META.get('HTTP_X_REAL_IP'),
                'HTTP_X_FORWARDED': request.META.get('HTTP_X_FORWARDED'),
                'HTTP_CF_CONNECTING_IP': request.META.get('HTTP_CF_CONNECTING_IP'),
                'HTTP_TRUE_CLIENT_IP': request.META.get('HTTP_TRUE_CLIENT_IP'),
                'REMOTE_ADDR': request.META.get('REMOTE_ADDR'),
            }
            logger.info(f"Login IP debug for {user.username}: {ip_debug}")

            # Логируем успешный вход
            log_from_request(
                'login',
                f'Вход в систему: {user.username}',
                request,
                severity='info',
            )

            if user.is_superuser or user.is_staff:
                return redirect('home')
            try:
                op = Operator.objects.get(user=user)
                return redirect('operator1_dashboard' if op.operator_type == 'client_service' else 'operator2_dashboard')
            except Operator.DoesNotExist:
                pass
            try:
                Client.objects.get(user=user)
                return redirect('client_dashboard')
            except Client.DoesNotExist:
                pass
            messages.error(request, 'Для учетной записи не назначена роль')
            return redirect('login')
        else:
            # Логируем неудачную попытку входа
            log_from_request(
                'login',
                f'Неудачная попытка входа: {email_input}',
                request,
                severity='warning',
            )
        messages.error(request, 'Неверные email или пароль')
    return render(request, 'login.html')

def logout_view(request):
    # Логируем выход до завершения сессии
    if request.user.is_authenticated:
        log_from_request(
            'logout',
            f'Выход из системы: {request.user.username}',
            request,
            severity='info',
        )
    logout(request)
    return redirect('home')

@login_required
def client_dashboard(request):
    """Дашборд клиента"""
    try:
        client = Client.objects.select_related('user').get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    cards = BankCard.objects.filter(client=client, is_active=True)
    credits = Credit.objects.filter(client=client, status='active')[:10]
    return render(request, 'client_dashboard.html', {
        'client': client, 'cards': cards,
        'connected_services': ClientService.objects.filter(client=client, status='active', is_active=True).select_related('service', 'service__category')[:20],
        'service_requests': ServiceRequest.objects.filter(client=client).order_by('-created_at')[:10],
        'transactions': Transaction.objects.filter(models.Q(from_card__client=client) | models.Q(to_card__client=client)).select_related('from_card', 'to_card').order_by('-created_at')[:10],
        'deposits': Deposit.objects.filter(client=client, is_active=True)[:10],
        'credits': credits,
        'total_balance': cards.aggregate(total=models.Sum('balance'))['total'] or 0,
        'total_credit_amount': sum(c.remaining_amount for c in credits) or 0,
    })

@login_required
def operator1_dashboard(request):
    """Дашборд оператора ДБО #1"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='client_service')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')
    
    # Обработка создания клиента (POST запрос)
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()

            if not full_name or not email or not phone:
                messages.error(request, 'Пожалуйста, заполните обязательные поля: имя, email, телефон')
                return redirect('operator1_dashboard')

            # Username = часть email до @
            username = email.split('@')[0] if '@' in email else email
            
            # Проверяем уникальность username и email
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Пользователь с таким логином ({username}) уже существует')
                return redirect('operator1_dashboard')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Пользователь с таким email уже существует')
                return redirect('operator1_dashboard')

            # Создаем пользователя Django и назначаем пароль по умолчанию
            # Используем стандартный пароль для всех новых клиентов
            default_password = '1q2w#E$R'
            
            user = User.objects.create(
                username=username,
                email=email
            )
            user.set_password(default_password)
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
                created_by=operator
            )

            # Логируем создание клиента
            log_from_request(
                'client_created',
                f'Создан новый клиент: {full_name} (ID: {client_id}, Email: {email})',
                request,
                client=client,
                operator=operator,
                severity='info',
                metadata={
                    'client_id': client_id,
                    'email': email,
                    'phone': phone,
                },
            )

            messages.success(request, f"Клиент {full_name} создан. Логин: {username}. Email: {email}. Пароль по умолчанию: {default_password}. Рекомендуется сменить при первом входе.")
            return redirect('operator1_dashboard')
            
        except Exception as e:
            messages.error(request, f'Ошибка при создании клиента: {str(e)}')
            return redirect('operator1_dashboard')
    
    return render(request, 'operator1_dashboard.html', {'operator': operator})

@login_required
def operator1_logs(request):
    """Просмотр логов действий оператора ДБО #1"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='client_service')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')
    
    # Получаем логи, связанные с этим оператором
    logs = DBOLog.objects.filter(operator=operator).order_by('-created_at')
    
    # Фильтрация по типу события
    event_type = request.GET.get('event_type', '')
    if event_type:
        logs = logs.filter(event_type=event_type)
    
    # Фильтрация по дате
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(created_at__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__lte=date_to)
    
    # Пагинация
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    total_logs = logs.count()
    client_created_count = logs.filter(event_type='client_created').count()
    
    context = {
        'operator': operator,
        'page_obj': page_obj,
        'logs': page_obj,
        'total_logs': total_logs,
        'client_created_count': client_created_count,
        'event_type': event_type,
        'date_from': date_from,
        'date_to': date_to,
        'event_types': [
            ('', 'Все события'),
            ('login', 'Вход в систему'),
            ('logout', 'Выход из системы'),
            ('client_created', 'Создание клиента'),
        ]
    }
    
    return render(request, 'operator1_logs.html', context)

@login_required
def operator2_dashboard(request):
    """Дашборд оператора ДБО #2"""
    try:
        operator = Operator.objects.get(user=request.user, operator_type='security')
    except Operator.DoesNotExist:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')
    # Исключаем заявки на регистрацию и служебные заявки (начинаются с "Тест")
    reqs = ServiceRequest.objects.filter(
        status='pending'
    ).exclude(
        service_name__icontains='регистрация'
    ).exclude(
        service_name__istartswith='тест'  # Скрываем служебную заявку
    ).order_by('-created_at')
    
    return render(request, 'operator2_dashboard.html', {
        'operator': operator, 'service_requests': reqs,
        'approved_requests': ServiceRequest.objects.filter(status='approved').order_by('-reviewed_at')[:10],
        'pending_requests': reqs.count(),
        'approved_today': ServiceRequest.objects.filter(status='approved', reviewed_at__date=timezone.now().date()).count(),
    })

@login_required
def create_client(request):
    """Создание нового клиента - редирект на дашборд"""
    return redirect('operator1_dashboard')


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
    # Для защиты игрок должен вручную заменить |safe на |escape в шаблоне
    
    context = {
        'service_request': service_request,
        'operator': operator,
    }
    
    return render(request, 'review_service_request.html', context)

@login_required
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
        name='Дополнительные услуги', defaults={'description': 'Пользовательские услуги'}
    )
    Service.objects.create(
        name=service_request.service_name,
        description=service_request.service_description,
        price=service_request.price,
        category=category,
        is_active=True,
        rating=Decimal('0.00'),  # Начальный рейтинг при создании
        rating_count=0,  # Начальное количество оценок
    )
    
    # Логирование атак отключено
    
    messages.success(request, 'Заявка одобрена, услуга добавлена в каталог')
    return redirect('operator2_dashboard')

@login_required
@require_http_methods(["POST"])
def reject_service_request(request, request_id):
    """Отклонение заявки на услугу (функционал оператора ДБО #2)"""
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

    service_request.status = 'rejected'
    service_request.reviewed_by = operator
    service_request.reviewed_at = timezone.now()
    service_request.save()

    messages.success(request, 'Заявка отклонена')
    return redirect('operator2_dashboard')

@login_required
@require_http_methods(["POST"]) 
def create_bank_card(request):
    """Создает банковский счет для текущего клиента и возвращает назад с уведомлением."""
    # Получаем клиента
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('cards')

    card_type = (request.POST.get('card_type') or '').strip()
    initial_deposit_raw = request.POST.get('initial_deposit') or '0'
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')

    # Валидируем тип счета: теперь разрешен только один тип (текущий)
    allowed_types = {'checking'}
    if card_type not in allowed_types:
        card_type = 'checking'

    # Парсим сумму
    try:
        initial_deposit = Decimal(str(initial_deposit_raw))
        if initial_deposit < 0:
            raise ValueError
    except Exception:
        messages.error(request, 'Неверная сумма начального взноса')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('cards')

    # Генерируем уникальный номер счета (максимум 19 символов)
    base = f"40817{timezone.now().strftime('%m%d%H%M%S')}{client.id:02d}"
    card_number = base[:19] if len(base) > 19 else base.ljust(19, '0')
    # Разрешаем потенциальные коллизии
    suffix = 0
    while BankCard.objects.filter(card_number=card_number).exists():
        suffix += 1
        tail = f"{suffix:02d}"
        card_number = (base + tail)[:19]

    # Создаем счет
    BankCard.objects.create(
        client=client,
        card_number=card_number,
        card_type=card_type,
        balance=initial_deposit,
        currency='RUB',
        is_active=True,
    )

    messages.success(request, f'Счет успешно открыт. Номер: {card_number}')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('cards')

@login_required
def transfers_view(request):
    """Переводы"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    cards = BankCard.objects.filter(client=client, is_active=True)
    main_card = client.primary_card if hasattr(client, 'primary_card') and client.primary_card else cards.first()
    return render(request, 'transfers.html', {
        'client': client, 'cards': cards, 'accounts': cards, 'main_card': main_card, 'main_account': main_card,
        'recent_transfers': Transaction.objects.filter(models.Q(from_card__client=client) | models.Q(to_card__client=client), transaction_type='transfer').select_related('from_card', 'to_card', 'from_card__client', 'to_card__client').order_by('-created_at')[:10],
    })

@login_required
def transactions_view(request):
    """Страница истории операций"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем все операции клиента (входящие и исходящие) - транзакции, переводы и т.д.
    transactions = Transaction.objects.filter(
        models.Q(from_card__client=client) | models.Q(to_card__client=client)
    ).select_related('from_card', 'to_card', 'from_card__client', 'to_card__client').order_by('-created_at')
    
    # Фильтрация по типу транзакции
    transaction_type = request.GET.get('type', '')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    # Поиск по описанию
    search_query = request.GET.get('search', '')
    if search_query:
        transactions = transactions.filter(description__icontains=search_query)
    
    # Пагинация
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    all_transactions = Transaction.objects.filter(
        models.Q(from_card__client=client) | models.Q(to_card__client=client)
    )
    total_transactions = all_transactions.count()
    completed_transactions = all_transactions.filter(status='completed').count()
    pending_transactions = all_transactions.filter(status='pending').count()
    failed_transactions = all_transactions.filter(status='failed').count()
    
    # Статистика по типам
    transfers_count = all_transactions.filter(transaction_type='transfer').count()
    payments_count = all_transactions.filter(transaction_type='payment').count()
    deposits_count = all_transactions.filter(transaction_type='deposit').count()
    withdrawals_count = all_transactions.filter(transaction_type='withdrawal').count()
    fees_count = all_transactions.filter(transaction_type='fee').count()
    
    # Общая сумма по типам
    # Доходы: входящие транзакции, где получатель - клиент, но отправитель - не он сам
    total_income = all_transactions.filter(
        models.Q(to_card__client=client) & 
        models.Q(status='completed') &
        ~models.Q(from_card__client=client)  # Исключаем переводы самому себе
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Расходы: исходящие транзакции, где отправитель - клиент, но получатель - не он сам
    total_expense = all_transactions.filter(
        models.Q(from_card__client=client) & 
        models.Q(status='completed') &
        ~models.Q(to_card__client=client)  # Исключаем переводы самому себе
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Типы транзакций для фильтра
    transaction_types = [
        ('', 'Все типы'),
        ('transfer', 'Переводы'),
        ('payment', 'Платежи'),
        ('deposit', 'Пополнения'),
        ('withdrawal', 'Снятия'),
        ('fee', 'Комиссии'),
    ]
    
    # Статусы для фильтра
    statuses = [
        ('', 'Все статусы'),
        ('completed', 'Завершена'),
        ('pending', 'Ожидает'),
        ('failed', 'Отклонена'),
        ('cancelled', 'Отменена'),
    ]
    
    context = {
        'client': client,
        'page_obj': page_obj,
        'transactions': page_obj,
        'total_transactions': total_transactions,
        'completed_transactions': completed_transactions,
        'pending_transactions': pending_transactions,
        'failed_transactions': failed_transactions,
        'transfers_count': transfers_count,
        'payments_count': payments_count,
        'deposits_count': deposits_count,
        'withdrawals_count': withdrawals_count,
        'fees_count': fees_count,
        'total_income': total_income,
        'total_expense': total_expense,
        'transaction_types': transaction_types,
        'statuses': statuses,
        'current_type': transaction_type,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'transactions.html', context)

@login_required
def history_view(request):
    """Страница истории операций - единое представление всех операций"""
    return transactions_view(request)

@login_required
@require_http_methods(["GET"])
def get_card_details(request, card_id):
    """Возвращает детали счета клиента (JSON)."""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Клиент не найден'}, status=400)

    try:
        card = BankCard.objects.get(id=card_id, client=client)
    except BankCard.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Счет не найден'}, status=404)

    data = {
        'id': card.id,
        'card_number': card.card_number,
        'card_type': card.card_type,
        'balance': float(card.balance),
        'currency': card.currency,
        'is_active': card.is_active,
        'created_at': card.created_at.strftime('%d.%m.%Y %H:%M') if hasattr(card, 'created_at') else '',
    }
    return JsonResponse({'success': True, 'card': data})

@login_required
@require_http_methods(["GET"])
def get_card_statements(request, card_id):
    """Возвращает последние операции по счету клиента (JSON)."""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Клиент не найден'}, status=400)

    try:
        card = BankCard.objects.get(id=card_id, client=client)
    except BankCard.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Счет не найден'}, status=404)

    txs = Transaction.objects.filter(
        models.Q(from_card=card) | models.Q(to_card=card)
    ).order_by('-created_at')[:20]

    items = []
    for tx in txs:
        items.append({
            'id': tx.id,
            'type': tx.transaction_type,
            'amount': float(tx.amount),
            'currency': tx.currency,
            'status': tx.status,
            'description': tx.description,
            'created_at': tx.created_at.strftime('%d.%m.%Y %H:%M'),
        })
    return JsonResponse({'success': True, 'statements': items})
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
def cards(request):
    """Старый маршрут для счетов"""
    return cards_view(request)

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
def cards_service(request):
    """Страница расчетно-кассового обслуживания"""
    try:
        client = Client.objects.get(user=request.user)
        cards = BankCard.objects.filter(client=client, is_active=True)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'cards': cards,
    }
    
    return render(request, 'cards.html', context)

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
        cards = BankCard.objects.filter(client=client, is_active=True)
        deposits = Deposit.objects.filter(client=client)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'cards': cards,
        'deposits': deposits,
    }
    
    return render(request, 'deposits.html', context)

@login_required
def transfers_service(request):
    """Страница переводов и платежей"""
    try:
        client = Client.objects.get(user=request.user)
        cards = BankCard.objects.filter(client=client, is_active=True)
        transactions = Transaction.objects.filter(
            models.Q(from_card__client=client) | models.Q(to_card__client=client)
        ).order_by('-created_at')[:20]
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'cards': cards,
        'transactions': transactions,
    }
    
    return render(request, 'transfers.html', context)

@login_required
def cards_service(request):
    """Страница банковских карт"""
    try:
        client = Client.objects.get(user=request.user)
        cards = BankCard.objects.filter(client=client, is_active=True)
        cards = BankCard.objects.filter(client=client, is_active=True)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'cards': cards,
    }
    
    return render(request, 'cards.html', context)

@login_required
def investments_service(request):
    """Страница инвестиционных продуктов"""
    try:
        client = Client.objects.get(user=request.user)
        cards = BankCard.objects.filter(client=client, is_active=True)
        investments = ClientInvestment.objects.filter(client=client)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    context = {
        'client': client,
        'cards': cards,
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
    cards = BankCard.objects.filter(client=client, is_active=True)
    cards = BankCard.objects.filter(client=client, is_active=True)
    credits = Credit.objects.filter(client=client)
    deposits = Deposit.objects.filter(client=client)
    investments = ClientInvestment.objects.filter(client=client)
    transactions = Transaction.objects.filter(
        models.Q(from_card__client=client) | models.Q(to_card__client=client)
    ).order_by('-created_at')[:5]
    
    # Подключенные услуги
    connected_services = ClientService.objects.filter(client=client, status='active')
    
    # Общая стоимость услуг
    total_cost = sum(service.monthly_fee for service in connected_services)
    
    # Статистика
    total_balance = sum(card.balance for card in cards)
    total_credit_debt = sum(credit.remaining_amount for credit in credits if credit.status == 'active')
    total_credit_amount = total_credit_debt if total_credit_debt > 0 else 0  # Гарантируем, что всегда будет число
    total_deposit_amount = sum(deposit.amount for deposit in deposits)
    total_investment_value = sum(investment.current_value for investment in investments if investment.status == 'active')
    
    context = {
        'client': client,
        'cards': cards,
        'credits': credits,
        'deposits': deposits,
        'investments': investments,
        'transactions': transactions,
        'connected_services': connected_services,
        'total_cost': total_cost,
        'total_balance': total_balance,
        'total_credit_debt': total_credit_debt,
        'total_credit_amount': total_credit_amount,
        'total_deposit_amount': total_deposit_amount,
        'total_investment_value': total_investment_value,
    }
    
    return render(request, 'client_dashboard.html', context)


@login_required
def transfers_service(request):
    """Страница переводов и платежей"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем счета клиента
    cards = BankCard.objects.filter(client=client, is_active=True)
    print(f"DEBUG: Найдено карт для клиента {client.full_name}: {cards.count()}")
    for card in cards:
        print(f"DEBUG: Карта {card.id}: {card.card_number}, баланс: {card.balance}, активна: {card.is_active}")
    
    # Получаем основной счет (первый активный счет или создаем его)
    main_card = cards.first()
    if not main_card:
        print(f"DEBUG: У клиента {client.full_name} нет активных карт, создаем основную карту")
        # Создаем основной счет если его нет
        from datetime import date, timedelta
        expiry_date = date.today() + timedelta(days=365*5)  # Карта действует 5 лет
        
        # Генерируем номер карты длиной максимум 19 символов
        client_id_str = str(client.client_id).zfill(11)
        # Формат: 40817810 + client_id (11 символов) + остаток до 19 символов
        card_num_base = f"40817810{client_id_str}"
        card_number = card_num_base[:19] if len(card_num_base) > 19 else card_num_base.ljust(19, '0')
        
        main_card = BankCard.objects.create(
            client=client,
            card_number=card_number,
            card_type='debit',
            balance=Decimal('100000.00'),  # Начальный баланс
            currency='RUB',
            expiry_date=expiry_date,
            is_active=True
        )
        print(f"DEBUG: Создана основная карта: {main_card.card_number}")
        
        # Автоматически делаем первую карту основной
        if not client.primary_card:
            client.primary_card = main_card
            client.save(update_fields=['primary_card'])
            print(f"DEBUG: Установлена основная карта для клиента {client.full_name}")
        
        cards = BankCard.objects.filter(client=client, is_active=True)
    else:
        print(f"DEBUG: Найдена основная карта: {main_card.card_number}")
    
    # Обработка POST-запроса (выполнение перевода)
    if request.method == 'POST':
        from_card_id = request.POST.get('from_account')
        print(f"DEBUG: Получен ID карты отправителя: {from_card_id}")
        recipient_phone = request.POST.get('recipient_phone')
        amount = request.POST.get('amount')
        description = request.POST.get('description', 'Перевод')

        # Проверяем, что все обязательные поля заполнены
        if not from_card_id:
            messages.error(request, 'Выберите карточку для списания')
            return redirect('transfers_service')
        
        if not recipient_phone:
            messages.error(request, 'Введите номер телефона получателя')
            return redirect('transfers_service')
        
        if not amount:
            messages.error(request, 'Введите сумму перевода')
            return redirect('transfers_service')

        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Сумма перевода должна быть положительной')
                return redirect('transfers_service')

            try:
                from_card = BankCard.objects.get(id=from_card_id, client=client, is_active=True)
                print(f"DEBUG: Найдена карта отправителя: {from_card.card_number}, баланс: {from_card.balance}")
            except BankCard.DoesNotExist:
                print(f"DEBUG: Карта отправителя не найдена. ID: {from_card_id}, клиент: {client.full_name}")
                messages.error(request, 'Карта списания не найдена или неактивна')
                return redirect('transfers_service')

            if from_card.balance < amount:
                messages.error(request, 'Недостаточно средств на счете')
                return redirect('transfers_service')

            # Нормализуем номер телефона получателя (оставляем только цифры)
            normalized_recipient_phone = ''.join(filter(str.isdigit, recipient_phone))
            print(f"DEBUG: Поиск получателя по номеру: {recipient_phone} -> {normalized_recipient_phone}")

            # Ищем получателя по точному совпадению нормализованного номера телефона
            try:
                recipient_client = Client.objects.get(phone=normalized_recipient_phone)
                print(f"DEBUG: Найден получатель: {recipient_client.full_name}")

                # Используем основную карту получателя, если она установлена и активна
                if recipient_client.primary_card and recipient_client.primary_card.is_active:
                    recipient_card = recipient_client.primary_card
                    print(f"DEBUG: Используем основную карту получателя: {recipient_card.card_number}")
                else:
                    # В противном случае используем первый активный счет
                    recipient_card = BankCard.objects.filter(client=recipient_client, is_active=True).first()
                    print(f"DEBUG: Используем первую активную карту получателя: {recipient_card.card_number if recipient_card else 'НЕТ КАРТ'}")

                if not recipient_card:
                    print(f"DEBUG: У получателя {recipient_client.full_name} нет активных карт")
                    messages.error(request, f'У получателя с номером {recipient_phone} нет активных карт')
                    return redirect('transfers_service')

                # Выполняем перевод
                from_card.balance -= amount
                from_card.save()

                recipient_card.balance += amount
                recipient_card.save()

                # Создаем транзакцию
                Transaction.objects.create(
                    from_card=from_card,
                    to_card=recipient_card,
                    amount=amount,
                    currency='RUB',
                    transaction_type='transfer',
                    description=f"Перевод по номеру телефона {recipient_phone}: {description}",
                    status='completed',
                    completed_at=timezone.now()
                )

                messages.success(request, f'Перевод на сумму {amount} ₽ успешно выполнен на номер {recipient_phone}')

            except Client.DoesNotExist:
                messages.error(request, f'Пользователь с номером телефона {recipient_phone} не найден')
                return redirect('transfers_service')

            return redirect('transfers_service')

        except ValueError:
            messages.error(request, 'Неверная сумма перевода')
        except Exception as e:
            messages.error(request, f'Ошибка при выполнении перевода: {str(e)}')

        return redirect('transfers_service')
    
    # Получаем последние транзакции
    transactions = Transaction.objects.filter(
        models.Q(from_card__client=client) | models.Q(to_card__client=client)
    ).order_by('-created_at')[:10]
    
    print(f"DEBUG: Передаем в шаблон - клиент: {client.full_name}, карт: {cards.count()}, основная карта: {main_card.card_number if main_card else 'НЕТ'}")
    
    context = {
        'client': client,
        'accounts': cards,
        'main_account': main_card,
        'transactions': transactions,
    }
    
    return render(request, 'transfers.html', context)


@csrf_exempt
def api_login(request):
    """API endpoint для авторизации (для ботов)"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Только POST запросы'
        }, status=405)
    
    try:
        data = json.loads(request.body) if request.body else {}
        email_input = data.get('email') or request.POST.get('email')
        password = data.get('password') or request.POST.get('password')
        
        if not email_input or not password:
            return JsonResponse({
                'success': False,
                'error': 'Email и пароль обязательны'
            }, status=400)
        
        user_obj = (
            User.objects.filter(email=email_input).first()
            or User.objects.filter(username=email_input).first()
            if email_input
            else None
        )
        user = authenticate(request, username=user_obj.username, password=password) if user_obj else None
        
        if user:
            login(request, user)
            return JsonResponse({
                'success': True,
                'username': user.username,
                'email': user.email,
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Неверные email или пароль'
            }, status=401)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def check_recipient_phone(request):
    """API endpoint для проверки существования пользователя по номеру телефона"""
    phone = request.GET.get('phone', '').strip()
    
    if not phone:
        return JsonResponse({
            'exists': False,
            'error': 'Номер телефона не указан'
        }, status=400)
    
    # Нормализуем номер телефона (оставляем только цифры)
    normalized_phone = ''.join(filter(str.isdigit, phone))
    
    if not normalized_phone:
        return JsonResponse({
            'exists': False,
            'error': 'Неверный формат номера телефона'
        }, status=400)
    
    try:
        recipient_client = Client.objects.get(phone=normalized_phone)
        # Проверяем, что у получателя есть активные карты
        has_active_cards = BankCard.objects.filter(
            client=recipient_client, 
            is_active=True
        ).exists()
        
        return JsonResponse({
            'exists': True,
            'has_active_cards': has_active_cards,
            'recipient_name': recipient_client.full_name,
            'message': f'Получатель найден: {recipient_client.full_name}' if has_active_cards else 'Получатель найден, но у него нет активных карт'
        })
    except Client.DoesNotExist:
        return JsonResponse({
            'exists': False,
            'message': 'Пользователь с таким номером телефона не найден'
        })
    except Exception as e:
        return JsonResponse({
            'exists': False,
            'error': f'Ошибка при проверке: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def set_primary_card(request, card_id):
    """Установка основной карты для клиента"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Клиент не найден'}, status=400)

    try:
        card = BankCard.objects.get(id=card_id, client=client)
    except BankCard.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Карта не найдена'}, status=404)

    if not card.is_active:
        return JsonResponse({'success': False, 'error': 'Нельзя установить заблокированную карту как основную'}, status=400)

    # Устанавливаем карту как основную
    client.primary_card = card
    client.save()

    return JsonResponse({
        'success': True,
        'message': f'Карта {card.card_number} установлена как основная',
        'card_number': card.card_number
    })


@login_required
def cards_service(request):
    """Страница управления банковскими картами"""
    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        messages.error(request, 'Клиент не найден')
        return redirect('home')
    
    # Получаем все карты клиента
    cards = BankCard.objects.filter(client=client).order_by('-created_at')
    
    context = {
        'client': client,
        'cards': cards,
        'primary_card': client.primary_card,
    }

    return render(request, 'cards.html', context)

