#!/usr/bin/env python3
"""
Генератор PDF документации для системы ДБО с поддержкой кириллицы
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
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Установите зависимости: pip install reportlab")
    sys.exit(1)

def register_fonts():
    """Регистрация шрифтов для поддержки кириллицы"""
    try:
        # Попробуем найти системные шрифты
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/System/Library/Fonts/Arial.ttf',  # macOS
            '/Windows/Fonts/arial.ttf',  # Windows
            '/Windows/Fonts/arialbd.ttf',  # Windows Bold
        ]
        
        # Регистрируем обычный шрифт
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
                    print(f"Зарегистрирован шрифт: {font_path}")
                    break
                except:
                    continue
        
        # Регистрируем жирный шрифт
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path))
                    print(f"Зарегистрирован жирный шрифт: {font_path}")
                    break
                except:
                    continue
        
        # Если не нашли системные шрифты, используем встроенные
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
            print("Используются встроенные Unicode шрифты")
        except:
            pass
            
    except Exception as e:
        print(f"Предупреждение: Не удалось зарегистрировать шрифты: {e}")
        print("Будут использованы стандартные шрифты")

def create_simple_pdf():
    """Создание простого PDF документа с поддержкой кириллицы"""
    
    # Регистрируем шрифты
    register_fonts()
    
    # Создаем PDF документ
    doc = SimpleDocTemplate(
        "ДБО_Система_Документация.pdf",
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50
    )
    
    # Получаем стили
    styles = getSampleStyleSheet()
    
    # Создаем пользовательские стили с поддержкой кириллицы
    try:
        font_name = 'DejaVuSans'
        font_name_bold = 'DejaVuSans-Bold'
    except:
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=HexColor('#1e40af'),
        fontName=font_name_bold
    )
    
    section_style = ParagraphStyle(
        'CustomSection',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=15,
        spaceAfter=10,
        textColor=HexColor('#1e40af'),
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
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=8
    )
    
    # Создаем элементы документа
    elements = []
    
    # Титульная страница
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Система Дистанционного<br/>Банковского Обслуживания", title_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Техническая документация", section_style))
    elements.append(Spacer(1, 1*inch))
    
    info_text = f"""
    <b>Версия:</b> 1.0<br/>
    <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y')}<br/>
    <b>Автор:</b> Система ДБО "ФинансПро"<br/>
    <b>Статус:</b> Активная разработка
    """
    elements.append(Paragraph(info_text, body_style))
    elements.append(PageBreak())
    
    # Содержание
    elements.append(Paragraph("Содержание", section_style))
    elements.append(Spacer(1, 12))
    
    toc_items = [
        "1. Обзор системы ......................... 3",
        "2. Архитектура ............................ 4", 
        "3. Модели данных .......................... 5",
        "4. API и эндпоинты ........................ 6",
        "5. Безопасность ........................... 7",
        "6. Установка и настройка .................. 8",
        "7. Администрирование ....................... 9",
        "8. Тестирование ........................... 10",
        "9. Развертывание .......................... 11"
    ]
    
    for item in toc_items:
        elements.append(Paragraph(item, body_style))
    
    elements.append(PageBreak())
    
    # Раздел 1: Обзор системы
    elements.append(Paragraph("1. Обзор системы", section_style))
    
    overview_text = """
    Система Дистанционного Банковского Обслуживания (ДБО) "ФинансПро" представляет собой 
    современную веб-платформу для управления банковскими услугами онлайн. Система построена 
    на Django и предоставляет полный спектр банковских операций через веб-интерфейс.
    """
    elements.append(Paragraph(overview_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Основные возможности:", section_style))
    capabilities = [
        "• Управление клиентами: Регистрация, верификация и управление клиентскими данными",
        "• Банковские услуги: Каталог услуг с возможностью подключения и управления", 
        "• Финансовые операции: Переводы, платежи, депозиты, кредиты",
        "• Инвестиционные продукты: Управление инвестиционными портфелями",
        "• Безопасность: Многоуровневая система безопасности с логированием атак",
        "• Администрирование: Панели управления для операторов и администраторов"
    ]
    
    for capability in capabilities:
        elements.append(Paragraph(capability, body_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Технологический стек:", section_style))
    
    # Таблица технологий
    tech_data = [
        ['Компонент', 'Технология'],
        ['Backend', 'Django 5.2.7, Python 3.13'],
        ['Database', 'SQLite (разработка), PostgreSQL (продакшн)'],
        ['Frontend', 'HTML5, CSS3, JavaScript, daisyUI 5'],
        ['Стилизация', 'Tailwind CSS 4'],
        ['Безопасность', 'Django Security Framework']
    ]
    
    tech_table = Table(tech_data, colWidths=[2*inch, 3*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
    ]))
    
    elements.append(tech_table)
    elements.append(PageBreak())
    
    # Раздел 2: Архитектура
    elements.append(Paragraph("2. Архитектура", section_style))
    
    arch_text = """
    Система построена по принципу MVC (Model-View-Controller) с использованием Django Framework.
    Архитектура обеспечивает разделение ответственности между компонентами и упрощает 
    разработку и поддержку системы.
    """
    elements.append(Paragraph(arch_text, body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Компоненты системы:", section_style))
    
    components_text = """
    <b>1. Модели данных (Models)</b><br/>
    • Operator: Операторы ДБО (два типа)<br/>
    • Client: Клиенты банка<br/>
    • Service: Банковские услуги<br/>
    • ServiceCategory: Категории услуг<br/>
    • BankCard: Банковские карты<br/>
    • Transaction: Финансовые транзакции<br/><br/>
    
    <b>2. Представления (Views)</b><br/>
    • home: Главная страница<br/>
    • banking_services: Каталог услуг<br/>
    • client_dashboard: Панель клиента<br/>
    • operator1_dashboard: Панель оператора ДБО #1<br/>
    • operator2_dashboard: Панель оператора ДБО #2<br/><br/>
    
    <b>3. Шаблоны (Templates)</b><br/>
    • base.html: Базовый шаблон<br/>
    • index.html: Главная страница<br/>
    • dashboard.html: Дашборды<br/>
    • banking_services.html: Каталог услуг
    """
    elements.append(Paragraph(components_text, body_style))
    elements.append(PageBreak())
    
    # Раздел 3: Модели данных
    elements.append(Paragraph("3. Модели данных", section_style))
    
    elements.append(Paragraph("Operator (Операторы ДБО)", section_style))
    
    operator_code = """
class Operator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    operator_type = models.CharField(max_length=50, choices=[
        ('client_service', 'Оператор ДБО #1 (Отдел клиентского обслуживания)'),
        ('security', 'Оператор ДБО #2 (Отдел безопасности/валидации)'),
    ])
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    """
    
    elements.append(Paragraph(operator_code, code_style))
    elements.append(Paragraph("Назначение: Управление операторами системы с разделением ролей.", body_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Client (Клиенты)", section_style))
    
    client_code = """
class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    primary_card = models.ForeignKey('BankCard', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    """
    
    elements.append(Paragraph(client_code, code_style))
    elements.append(Paragraph("Назначение: Хранение информации о клиентах банка.", body_style))
    elements.append(PageBreak())
    
    # Раздел 5: Безопасность
    elements.append(Paragraph("5. Безопасность", section_style))
    
    elements.append(Paragraph("Уязвимости для тестирования", section_style))
    
    elements.append(Paragraph("1. SQL-инъекция в banking_services", section_style))
    
    sql_text = """
    Расположение: dbo/views.py, функция banking_services
    
    Код уязвимости:
    """
    elements.append(Paragraph(sql_text, body_style))
    
    sql_code = """
# ОПАСНО: Прямая конкатенация без параметризации
if q:
    where_clauses.append(f"(s.name LIKE '%{q}%' OR s.description LIKE '%{q}%')")

if category_name:
    where_clauses.append(f"c.name = '{category_name}'")
    """
    
    elements.append(Paragraph(sql_code, code_style))
    
    elements.append(Paragraph("Эксплойт:", section_style))
    elements.append(Paragraph("-- Поиск: ' OR '1'='1' --", code_style))
    elements.append(Paragraph("-- Категория: '; DROP TABLE dbo_service; --", code_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("2. XSS в ServiceRequest", section_style))
    
    xss_text = """
    Расположение: dbo/models.py, поле service_description
    
    Описание: Поле service_description в модели ServiceRequest не экранируется 
    при отображении, что позволяет внедрить JavaScript код.
    """
    elements.append(Paragraph(xss_text, body_style))
    
    elements.append(Paragraph("Эксплойт:", section_style))
    elements.append(Paragraph("<script>alert('XSS Attack!')</script>", code_style))
    elements.append(PageBreak())
    
    # Раздел 6: Установка и настройка
    elements.append(Paragraph("6. Установка и настройка", section_style))
    
    elements.append(Paragraph("Требования", section_style))
    requirements = [
        "• Python 3.13+",
        "• Django 5.2.7", 
        "• PostgreSQL (для продакшна)",
        "• Node.js (для сборки статических файлов)"
    ]
    
    for req in requirements:
        elements.append(Paragraph(req, body_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Установка", section_style))
    install_steps = [
        "1. Клонирование репозитория: git clone <repository-url>",
        "2. Создание виртуального окружения: python -m venv venv",
        "3. Установка зависимостей: pip install -r requirements.txt",
        "4. Настройка базы данных: python manage.py migrate",
        "5. Создание суперпользователя: python manage.py createsuperuser",
        "6. Инициализация демо-данных: python init_data.py",
        "7. Запуск сервера: python manage.py runserver"
    ]
    
    for step in install_steps:
        elements.append(Paragraph(step, body_style))
    elements.append(PageBreak())
    
    # Заключение
    elements.append(Paragraph("Заключение", section_style))
    
    conclusion_text = """
    Система ДБО "ФинансПро" представляет собой комплексное решение для дистанционного 
    банковского обслуживания с современной архитектурой и широкими возможностями настройки. 
    Система включает в себя все необходимые компоненты для полноценного банковского сервиса 
    и может быть легко адаптирована под конкретные требования.
    """
    elements.append(Paragraph(conclusion_text, body_style))
    
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Основные преимущества:", section_style))
    advantages = [
        "• Масштабируемость: Архитектура позволяет легко добавлять новые функции",
        "• Безопасность: Многоуровневая система защиты с возможностью тестирования уязвимостей",
        "• Гибкость: Модульная структура упрощает кастомизацию",
        "• Производительность: Оптимизированные запросы и кэширование"
    ]
    
    for advantage in advantages:
        elements.append(Paragraph(advantage, body_style))
    
    elements.append(Spacer(1, 20))
    
    copyright_text = "© 2024 Система ДБО 'ФинансПро'. Все права защищены."
    elements.append(Paragraph(copyright_text, body_style))
    
    # Создаем функцию для заголовков и подвалов
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
    
    print("PDF документация успешно создана: ДБО_Система_Документация.pdf")

if __name__ == "__main__":
    print("Генератор PDF документации для системы ДБО (с поддержкой кириллицы)")
    print("=" * 70)
    
    try:
        create_simple_pdf()
        print("\n✅ Документация успешно создана!")
        print("📄 Файл: ДБО_Система_Документация.pdf")
        print("🔤 Поддержка кириллицы: Включена")
    except Exception as e:
        print(f"\n❌ Ошибка при создании PDF: {e}")
        sys.exit(1)
