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
        ip_address: IP адрес (обязателен)
        user_agent: User Agent (опционально)
        metadata: Дополнительные данные в виде dict (опционально)
    """
    try:
        # IP адрес обязателен
        if not ip_address:
            ip_address = '0.0.0.0'  # Значение по умолчанию
        
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
        request: Django request объект (обязателен для получения IP)
        client: Клиент (опционально)
        operator: Оператор (опционально)
        severity: Уровень важности
        metadata: Дополнительные данные
    """
    if not request:
        raise ValueError("Request обязателен для логирования - требуется для получения IP адреса")
    
    ip_address = get_client_ip(request)
    if not ip_address:
        # Если не удалось получить IP, логируем все доступные заголовки для отладки
        import logging
        logger = logging.getLogger(__name__)
        all_headers = {k: v for k, v in request.META.items() if 'IP' in k.upper() or 'FORWARDED' in k.upper() or 'REMOTE' in k.upper()}
        logger.warning(f"Could not determine client IP. Available headers: {all_headers}")
        ip_address = '0.0.0.0'  # Значение по умолчанию, если IP не удалось получить
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    return log_dbo_event(
        event_type=event_type,
        description=description,
        user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
        client=client,
        operator=operator,
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata
    )


def get_client_ip(request):
    """Получает IP адрес клиента из request"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Список всех возможных заголовков для получения IP клиента
    # Проверяем в порядке приоритета
    
    # 1. X-Forwarded-For - стандартный заголовок для прокси
    # Формат: "client_ip, proxy1_ip, proxy2_ip"
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Берем первый IP из цепочки (реальный IP клиента)
        ip = x_forwarded_for.split(',')[0].strip()
        # Убираем порт если есть (например, "192.168.1.1:12345" -> "192.168.1.1")
        if ':' in ip:
            ip = ip.split(':')[0]
        if ip and ip != 'unknown':
            logger.debug(f"IP from X-Forwarded-For: {ip}")
            return ip
    
    # 2. X-Real-IP - часто используется nginx и другими прокси
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        ip = x_real_ip.strip()
        if ':' in ip:
            ip = ip.split(':')[0]
        if ip and ip != 'unknown':
            logger.debug(f"IP from X-Real-IP: {ip}")
            return ip
    
    # 3. X-Forwarded - альтернативный заголовок
    x_forwarded = request.META.get('HTTP_X_FORWARDED')
    if x_forwarded:
        ip = x_forwarded.split(',')[0].strip()
        if ':' in ip:
            ip = ip.split(':')[0]
        if ip and ip != 'unknown':
            logger.debug(f"IP from X-Forwarded: {ip}")
            return ip
    
    # 4. CF-Connecting-IP - используется Cloudflare
    cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_connecting_ip:
        ip = cf_connecting_ip.strip()
        if ':' in ip:
            ip = ip.split(':')[0]
        if ip and ip != 'unknown':
            logger.debug(f"IP from CF-Connecting-IP: {ip}")
            return ip
    
    # 5. True-Client-IP - используется некоторыми CDN
    true_client_ip = request.META.get('HTTP_TRUE_CLIENT_IP')
    if true_client_ip:
        ip = true_client_ip.strip()
        if ':' in ip:
            ip = ip.split(':')[0]
        if ip and ip != 'unknown':
            logger.debug(f"IP from True-Client-IP: {ip}")
            return ip
    
    # 6. REMOTE_ADDR - прямой IP соединения
    # ВНИМАНИЕ: Если приложение за прокси, это будет IP прокси, а не клиента!
    # Но если нет заголовков прокси, это единственный способ получить IP
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr:
        ip = remote_addr.strip()
        # Обработка IPv6 (формат [::1] или ::1)
        if ip.startswith('[') and ip.endswith(']'):
            ip = ip[1:-1]
        # Убираем порт если есть
        if ':' in ip and not ip.count(':') > 1:  # IPv4 с портом, не IPv6
            ip = ip.split(':')[0]
        # Проверяем, что это не localhost/прокси IP
        # Но если нет других заголовков, используем REMOTE_ADDR даже если это localhost
        if ip:
            # Если есть заголовки прокси, но они пустые, значит прокси не настроен
            # В этом случае REMOTE_ADDR - это реальный IP клиента
            if not x_forwarded_for and not x_real_ip:
                logger.debug(f"IP from REMOTE_ADDR (no proxy headers): {ip}")
                return ip
            # Если есть заголовки прокси, но IP не localhost, используем его
            elif ip not in ['127.0.0.1', '::1', 'localhost', '0.0.0.0']:
                logger.debug(f"IP from REMOTE_ADDR: {ip}")
                return ip
    
    # Отладочная информация - логируем все заголовки связанные с IP
    all_ip_headers = {
        'HTTP_X_FORWARDED_FOR': x_forwarded_for,
        'HTTP_X_REAL_IP': x_real_ip,
        'HTTP_X_FORWARDED': x_forwarded,
        'HTTP_CF_CONNECTING_IP': cf_connecting_ip,
        'HTTP_TRUE_CLIENT_IP': true_client_ip,
        'REMOTE_ADDR': remote_addr,
    }
    logger.warning(f"Could not determine client IP. Available headers: {all_ip_headers}")
    return None

