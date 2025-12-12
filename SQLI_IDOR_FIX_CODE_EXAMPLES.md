# Конкретные изменения в коде для устранения SQL+IDOR

## 1. Исправление SQL-инъекции в функции `banking_services`

### Файл: `dbo/views.py`, строки 54-78

**БЫЛО (небезопасно - SQL-инъекция):**

```54:78:dbo/views.py
    where_clauses = ["s.is_active = true"]
    if category_name:
        where_clauses.append(f"c.name = '{category_name}'")  # ❌ SQL-инъекция!
    if q:
        where_clauses.append(f"(s.name LIKE '%{q}%' OR s.description LIKE '%{q}%')")  # ❌ SQL-инъекция!
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

    sql = f"""SELECT s.id, s.name, s.description, s.price, s.is_active, s.rating, s.rating_count, c.name as category_name
              FROM dbo_service s JOIN dbo_servicecategory c ON s.category_id = c.id
              WHERE {' AND '.join(where_clauses)} ORDER BY {order_by}"""

    services_rows = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)  # ❌ Выполнение уязвимого SQL
```

**СТАЛО (безопасно - параметризованные запросы):**

```python
    # Безопасное построение SQL с параметрами
    sql_parts = ["SELECT s.id, s.name, s.description, s.price, s.is_active, s.rating, s.rating_count, c.name as category_name",
                 "FROM dbo_service s JOIN dbo_servicecategory c ON s.category_id = c.id",
                 "WHERE s.is_active = true"]
    params = []
    
    if category_name:
        sql_parts.append("AND c.name = %s")  # ✅ Параметризованный запрос
        params.append(category_name)
    if q:
        sql_parts.append("AND (s.name LIKE %s OR s.description LIKE %s)")  # ✅ Параметризованный запрос
        params.extend([f'%{q}%', f'%{q}%'])
    if price_filter == 'free':
        sql_parts.append("AND s.price = 0")
    elif price_filter == 'low':
        sql_parts.append("AND s.price > 0 AND s.price <= 1000")
    elif price_filter == 'medium':
        sql_parts.append("AND s.price > 1000 AND s.price <= 5000")
    elif price_filter == 'high':
        sql_parts.append("AND s.price > 5000")

    order_map = {'name': 's.name', 'price-low': 's.price ASC', 'price-high': 's.price DESC', 'popular': 's.rating_count DESC'}
    order_by = order_map.get(sort_by, 's.name')
    sql_parts.append(f"ORDER BY {order_by}")

    sql = " ".join(sql_parts)
    services_rows = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)  # ✅ Параметры передаются вторым аргументом
```

## 2. Исправление SQL-инъекции в функции `search_services`

### Файл: `dbo/views.py`, строки 117-131

**БЫЛО (небезопасно - SQL-инъекция):**

```117:131:dbo/views.py
@login_required
def search_services(request):
    """Поиск услуг (SQL-инъекция исправлена параметризованными запросами)"""
    query = request.GET.get('query', '').strip()
    
    # БЕЗОПАСНО: Django ORM автоматически экранирует параметры
    if query:
        services_queryset = Service.objects.filter(
            models.Q(name__icontains=query) | models.Q(description__icontains=query),
            is_active=True
        ).select_related('category').order_by('name')
```

**Примечание:** Эта функция уже исправлена и использует Django ORM, что безопасно. Но если бы использовался прямой SQL, было бы так:

**БЫЛО БЫ (небезопасно):**
```python
sql = f"SELECT ... WHERE s.name LIKE '%{query}%' OR s.description LIKE '%{query}%' ..."
cursor.execute(sql)  # ❌ SQL-инъекция!
```

**СТАЛО (безопасно):**
```python
sql = "SELECT s.id, s.name, s.description, s.price, c.name as category_name FROM dbo_service s JOIN dbo_servicecategory c ON s.category_id = c.id WHERE s.name LIKE %s OR s.description LIKE %s ORDER BY s.name"
search_pattern = f'%{query}%'
cursor.execute(sql, [search_pattern, search_pattern])  # ✅ Параметры передаются вторым аргументом
```

## 3. Исправление IDOR в функции `connect_service`

### Файл: `dbo/views.py`, строки 347-443

**БЫЛО (небезопасно - IDOR):**

```347:370:dbo/views.py
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
```

**СТАЛО (безопасно - с проверкой прав доступа):**

```python
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
        
        # ✅ ПРОВЕРКА ПРАВ ДОСТУПА: Предотвращение IDOR
        # Проверяем, не является ли услуга служебной
        if service.category.name == 'Служебные' and not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен: служебные услуги доступны только администраторам'})
        
        # Проверяем, не подключена ли уже услуга (только активные)
        if ClientService.objects.filter(client=client, service=service, status='active', is_active=True).exists():
            # Уже подключена — ведём себя как успех
            message = f'Услуга "{service.name}" уже подключена'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': message, 'service_uuid': str(service.uuid)})
```

## Итоговые изменения

### Изменение 1: Строки 54-78 в `dbo/views.py`
- **Было:** `where_clauses.append(f"c.name = '{category_name}'")` и `cursor.execute(sql)`
- **Стало:** `sql_parts.append("AND c.name = %s")`, `params.append(category_name)` и `cursor.execute(sql, params)`

### Изменение 2: Строки 335-338 в `dbo/views.py` (функция `connect_service`)
- **Добавить после строки 338:**
```python
        # ✅ ПРОВЕРКА ПРАВ ДОСТУПА: Предотвращение IDOR
        if service.category.name == 'Служебные' and not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'success': False, 'error': 'Доступ запрещен: служебные услуги доступны только администраторам'})
```

