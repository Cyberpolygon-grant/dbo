"""
Helper функции для логирования событий ДБО
"""
from django.contrib.auth.models import User
from .models import DBOLog, Client, Operator


def log_dbo_event(event_type, description, user=None, client=None, operator=None, 
                  severity='info', ip_address=None, user_agent=None, metadata=None):
    """
    Создает запись в логе ДБО
    
    Args:
        event_type: Тип события (из DBOLog.EVENT_TYPES)
        description: Описание события
        user: Пользователь Django (опционально)
        client: Клиент (опционально)
        operator: Оператор (опционально)
        severity: Уровень важности ('info', 'warning', 'error', 'critical')
        ip_address: IP адрес (опционально)
        user_agent: User Agent (опционально)
        metadata: Дополнительные данные в виде dict (опционально)
    """
    try:
        # Если передан user, пытаемся найти оператора
        if user and not operator:
            try:
                operator = Operator.objects.get(user=user)
            except Operator.DoesNotExist:
                pass
        
        # Если передан user, пытаемся найти клиента
        if user and not client:
            try:
                client = Client.objects.get(user=user)
            except Client.DoesNotExist:
                pass
        
        log_entry = DBOLog.objects.create(
            event_type=event_type,
            description=description,
            user=user,
            client=client,
            operator=operator,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent or '',
            metadata=metadata or {}
        )
        return log_entry
    except Exception as e:
        # Не прерываем выполнение при ошибке логирования
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка логирования события: {e}")
        return None


def log_from_request(event_type, description, request, client=None, operator=None, 
                     severity='info', metadata=None):
    """
    Удобная функция для логирования из view с автоматическим извлечением данных из request
    
    Args:
        event_type: Тип события
        description: Описание события
        request: Django request объект
        client: Клиент (опционально)
        operator: Оператор (опционально)
        severity: Уровень важности
        metadata: Дополнительные данные
    """
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    return log_dbo_event(
        event_type=event_type,
        description=description,
        user=request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None,
        client=client,
        operator=operator,
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata
    )


def get_client_ip(request):
    """Получает IP адрес клиента из request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

