#!/usr/bin/env python3
"""
Генератор PDF документации для системы ДБО
Создает PDF по примеру WordPress документации
"""

import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import markdown
from markdown.extensions import codehilite, tables, toc

class DBODocumentGenerator:
    def __init__(self, output_filename="ДБО_Система_Документация.pdf"):
        self.output_filename = output_filename
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Настройка пользовательских стилей"""
        # Заголовок документа
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#1e40af'),  # Синий цвет
            fontName='Helvetica-Bold'
        ))
        
        # Подзаголовок
        self.styles.add(ParagraphStyle(
            name='DocumentSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=HexColor('#6b7280'),  # Серый цвет
            fontName='Helvetica'
        ))
        
        # Заголовки разделов
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceBefore=20,
            spaceAfter=12,
            textColor=HexColor('#1e40af'),
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=HexColor('#e5e7eb'),
            borderPadding=8,
            backColor=HexColor('#f8fafc')
        ))
        
        # Подзаголовки
        self.styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=HexColor('#374151'),
            fontName='Helvetica-Bold'
        ))
        
        # Код
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=self.styles['Code'],
            fontSize=9,
            fontName='Courier',
            backColor=HexColor('#f3f4f6'),
            borderWidth=1,
            borderColor=HexColor('#d1d5db'),
            borderPadding=8,
            spaceBefore=8,
            spaceAfter=8
        ))
        
        # Обычный текст
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Список
        self.styles.add(ParagraphStyle(
            name='ListText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=4,
            leftIndent=20,
            fontName='Helvetica'
        ))

    def create_header_footer(self, canvas, doc):
        """Создание заголовка и подвала страницы"""
        canvas.saveState()
        
        # Заголовок
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(HexColor('#1e40af'))
        canvas.drawString(50, A4[1] - 30, "Система ДБО 'ФинансПро' - Техническая документация")
        
        # Подвал
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(HexColor('#6b7280'))
        canvas.drawString(50, 30, f"Страница {doc.page}")
        canvas.drawRightString(A4[0] - 50, 30, f"Версия 1.0 - {datetime.now().strftime('%d.%m.%Y')}")
        
        # Линия разделения
        canvas.setStrokeColor(HexColor('#e5e7eb'))
        canvas.line(50, A4[1] - 40, A4[0] - 50, A4[1] - 40)
        canvas.line(50, 40, A4[0] - 50, 40)
        
        canvas.restoreState()

    def create_title_page(self):
        """Создание титульной страницы"""
        elements = []
        
        # Логотип (заглушка)
        elements.append(Spacer(1, 2*inch))
        
        # Название документа
        title = Paragraph("Система Дистанционного<br/>Банковского Обслуживания", 
                          self.styles['DocumentTitle'])
        elements.append(title)
        
        # Подзаголовок
        subtitle = Paragraph("Техническая документация", 
                           self.styles['DocumentSubtitle'])
        elements.append(subtitle)
        
        elements.append(Spacer(1, 1*inch))
        
        # Информация о документе
        info_text = """
        <b>Версия:</b> 1.0<br/>
        <b>Дата:</b> {date}<br/>
        <b>Автор:</b> Система ДБО "ФинансПро"<br/>
        <b>Статус:</b> Активная разработка<br/>
        """.format(date=datetime.now().strftime('%d.%m.%Y'))
        
        info = Paragraph(info_text, self.styles['BodyText'])
        elements.append(info)
        
        elements.append(Spacer(1, 2*inch))
        
        # Описание
        description = """
        Система ДБО "ФинансПро" представляет собой современную веб-платформу 
        для управления банковскими услугами онлайн. Система построена на Django 
        и предоставляет полный спектр банковских операций через веб-интерфейс.
        """
        
        desc_para = Paragraph(description, self.styles['BodyText'])
        elements.append(desc_para)
        
        elements.append(PageBreak())
        return elements

    def create_table_of_contents(self):
        """Создание содержания"""
        elements = []
        
        toc_title = Paragraph("Содержание", self.styles['SectionTitle'])
        elements.append(toc_title)
        
        toc_items = [
            ("1. Обзор системы", "3"),
            ("2. Архитектура", "4"),
            ("3. Модели данных", "6"),
            ("4. API и эндпоинты", "8"),
            ("5. Безопасность", "10"),
            ("6. Установка и настройка", "12"),
            ("7. Администрирование", "14"),
            ("8. Тестирование", "16"),
            ("9. Развертывание", "18")
        ]
        
        for item, page in toc_items:
            toc_line = f"{item} ......................... {page}"
            toc_para = Paragraph(toc_line, self.styles['BodyText'])
            elements.append(toc_para)
            elements.append(Spacer(1, 6))
        
        elements.append(PageBreak())
        return elements

    def create_overview_section(self):
        """Создание раздела 'Обзор системы'"""
        elements = []
        
        # Заголовок раздела
        title = Paragraph("1. Обзор системы", self.styles['SectionTitle'])
        elements.append(title)
        
        # Описание
        description = """
        Система Дистанционного Банковского Обслуживания (ДБО) "ФинансПро" 
        представляет собой современную веб-платформу для управления банковскими 
        услугами онлайн. Система построена на Django и предоставляет полный 
        спектр банковских операций через веб-интерфейс.
        """
        elements.append(Paragraph(description, self.styles['BodyText']))
        elements.append(Spacer(1, 12))
        
        # Основные возможности
        capabilities_title = Paragraph("Основные возможности", self.styles['SubsectionTitle'])
        elements.append(capabilities_title)
        
        capabilities = [
            "• Управление клиентами: Регистрация, верификация и управление клиентскими данными",
            "• Банковские услуги: Каталог услуг с возможностью подключения и управления",
            "• Финансовые операции: Переводы, платежи, депозиты, кредиты",
            "• Инвестиционные продукты: Управление инвестиционными портфелями",
            "• Безопасность: Многоуровневая система безопасности с логированием атак",
            "• Администрирование: Панели управления для операторов и администраторов"
        ]
        
        for capability in capabilities:
            elements.append(Paragraph(capability, self.styles['ListText']))
        
        elements.append(Spacer(1, 12))
        
        # Технологический стек
        tech_title = Paragraph("Технологический стек", self.styles['SubsectionTitle'])
        elements.append(tech_title)
        
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
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb'))
        ]))
        
        elements.append(tech_table)
        elements.append(PageBreak())
        return elements

    def create_architecture_section(self):
        """Создание раздела 'Архитектура'"""
        elements = []
        
        title = Paragraph("2. Архитектура", self.styles['SectionTitle'])
        elements.append(title)
        
        # Общая архитектура
        arch_title = Paragraph("Общая архитектура", self.styles['SubsectionTitle'])
        elements.append(arch_title)
        
        arch_description = """
        Система построена по принципу MVC (Model-View-Controller) с использованием Django Framework.
        Архитектура обеспечивает разделение ответственности между компонентами и упрощает 
        разработку и поддержку системы.
        """
        elements.append(Paragraph(arch_description, self.styles['BodyText']))
        elements.append(Spacer(1, 12))
        
        # Компоненты системы
        components_title = Paragraph("Компоненты системы", self.styles['SubsectionTitle'])
        elements.append(components_title)
        
        components = [
            ("1. Модели данных (Models)", [
                "• Operator: Операторы ДБО (два типа)",
                "• Client: Клиенты банка",
                "• Service: Банковские услуги",
                "• ServiceCategory: Категории услуг",
                "• BankCard: Банковские карты",
                "• Transaction: Финансовые транзакции"
            ]),
            ("2. Представления (Views)", [
                "• home: Главная страница",
                "• banking_services: Каталог услуг",
                "• client_dashboard: Панель клиента",
                "• operator1_dashboard: Панель оператора ДБО #1",
                "• operator2_dashboard: Панель оператора ДБО #2"
            ]),
            ("3. Шаблоны (Templates)", [
                "• base.html: Базовый шаблон",
                "• index.html: Главная страница",
                "• dashboard.html: Дашборды",
                "• banking_services.html: Каталог услуг"
            ])
        ]
        
        for comp_title, comp_items in components:
            elements.append(Paragraph(comp_title, self.styles['SubsectionTitle']))
            for item in comp_items:
                elements.append(Paragraph(item, self.styles['ListText']))
            elements.append(Spacer(1, 8))
        
        elements.append(PageBreak())
        return elements

    def create_models_section(self):
        """Создание раздела 'Модели данных'"""
        elements = []
        
        title = Paragraph("3. Модели данных", self.styles['SectionTitle'])
        elements.append(title)
        
        # Операторы
        operator_title = Paragraph("Operator (Операторы ДБО)", self.styles['SubsectionTitle'])
        elements.append(operator_title)
        
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
        
        elements.append(Paragraph(operator_code, self.styles['CodeBlock']))
        elements.append(Paragraph("Назначение: Управление операторами системы с разделением ролей.", 
                                 self.styles['BodyText']))
        elements.append(Spacer(1, 12))
        
        # Клиенты
        client_title = Paragraph("Client (Клиенты)", self.styles['SubsectionTitle'])
        elements.append(client_title)
        
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
        
        elements.append(Paragraph(client_code, self.styles['CodeBlock']))
        elements.append(Paragraph("Назначение: Хранение информации о клиентах банка.", 
                                 self.styles['BodyText']))
        
        elements.append(PageBreak())
        return elements

    def create_security_section(self):
        """Создание раздела 'Безопасность'"""
        elements = []
        
        title = Paragraph("5. Безопасность", self.styles['SectionTitle'])
        elements.append(title)
        
        # Уязвимости для тестирования
        vuln_title = Paragraph("Уязвимости для тестирования", self.styles['SubsectionTitle'])
        elements.append(vuln_title)
        
        # SQL-инъекция
        sql_title = Paragraph("1. SQL-инъекция в banking_services", self.styles['SubsectionTitle'])
        elements.append(sql_title)
        
        sql_description = """
        Расположение: dbo/views.py, функция banking_services
        
        Код уязвимости:
        """
        elements.append(Paragraph(sql_description, self.styles['BodyText']))
        
        sql_code = """
# ОПАСНО: Прямая конкатенация без параметризации
if q:
    where_clauses.append(f"(s.name LIKE '%{q}%' OR s.description LIKE '%{q}%')")

if category_name:
    where_clauses.append(f"c.name = '{category_name}'")
        """
        
        elements.append(Paragraph(sql_code, self.styles['CodeBlock']))
        
        sql_exploit = """
Эксплойт:
-- Поиск: ' OR '1'='1' --
-- Категория: '; DROP TABLE dbo_service; --
        """
        
        elements.append(Paragraph(sql_exploit, self.styles['CodeBlock']))
        elements.append(Spacer(1, 12))
        
        # XSS
        xss_title = Paragraph("2. XSS в ServiceRequest", self.styles['SubsectionTitle'])
        elements.append(xss_title)
        
        xss_description = """
        Расположение: dbo/models.py, поле service_description
        
        Описание: Поле service_description в модели ServiceRequest не экранируется 
        при отображении, что позволяет внедрить JavaScript код.
        """
        elements.append(Paragraph(xss_description, self.styles['BodyText']))
        
        xss_exploit = """
Эксплойт:
<script>alert('XSS Attack!')</script>
        """
        
        elements.append(Paragraph(xss_exploit, self.styles['CodeBlock']))
        
        elements.append(PageBreak())
        return elements

    def create_installation_section(self):
        """Создание раздела 'Установка и настройка'"""
        elements = []
        
        title = Paragraph("6. Установка и настройка", self.styles['SectionTitle'])
        elements.append(title)
        
        # Требования
        req_title = Paragraph("Требования", self.styles['SubsectionTitle'])
        elements.append(req_title)
        
        requirements = [
            "• Python 3.13+",
            "• Django 5.2.7",
            "• PostgreSQL (для продакшна)",
            "• Node.js (для сборки статических файлов)"
        ]
        
        for req in requirements:
            elements.append(Paragraph(req, self.styles['ListText']))
        
        elements.append(Spacer(1, 12))
        
        # Установка
        install_title = Paragraph("Установка", self.styles['SubsectionTitle'])
        elements.append(install_title)
        
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
            elements.append(Paragraph(step, self.styles['ListText']))
        
        elements.append(PageBreak())
        return elements

    def create_conclusion_section(self):
        """Создание заключительного раздела"""
        elements = []
        
        title = Paragraph("Заключение", self.styles['SectionTitle'])
        elements.append(title)
        
        conclusion_text = """
        Система ДБО "ФинансПро" представляет собой комплексное решение для дистанционного 
        банковского обслуживания с современной архитектурой и широкими возможностями настройки. 
        Система включает в себя все необходимые компоненты для полноценного банковского сервиса 
        и может быть легко адаптирована под конкретные требования.
        """
        elements.append(Paragraph(conclusion_text, self.styles['BodyText']))
        elements.append(Spacer(1, 12))
        
        # Основные преимущества
        advantages_title = Paragraph("Основные преимущества", self.styles['SubsectionTitle'])
        elements.append(advantages_title)
        
        advantages = [
            "• Масштабируемость: Архитектура позволяет легко добавлять новые функции",
            "• Безопасность: Многоуровневая система защиты с возможностью тестирования уязвимостей",
            "• Гибкость: Модульная структура упрощает кастомизацию",
            "• Производительность: Оптимизированные запросы и кэширование"
        ]
        
        for advantage in advantages:
            elements.append(Paragraph(advantage, self.styles['ListText']))
        
        elements.append(Spacer(1, 12))
        
        # Планы развития
        plans_title = Paragraph("Планы развития", self.styles['SubsectionTitle'])
        elements.append(plans_title)
        
        plans = [
            "1. Мобильное приложение: Разработка React Native приложения",
            "2. API: Создание REST API для интеграции с внешними системами",
            "3. Аналитика: Система бизнес-аналитики и отчетности",
            "4. ИИ: Интеграция машинного обучения для обнаружения мошенничества"
        ]
        
        for plan in plans:
            elements.append(Paragraph(plan, self.styles['ListText']))
        
        elements.append(Spacer(1, 20))
        
        # Поддержка
        support_title = Paragraph("Поддержка", self.styles['SubsectionTitle'])
        elements.append(support_title)
        
        support_text = """
        Для получения технической поддержки обращайтесь:
        • Email: support@finanspro.ru
        • Документация: https://docs.finanspro.ru
        • GitHub: https://github.com/finanspro/dbo
        """
        elements.append(Paragraph(support_text, self.styles['BodyText']))
        
        elements.append(Spacer(1, 20))
        
        # Копирайт
        copyright_text = "© 2024 Система ДБО 'ФинансПро'. Все права защищены."
        elements.append(Paragraph(copyright_text, self.styles['BodyText']))
        
        return elements

    def generate_pdf(self):
        """Генерация PDF документа"""
        doc = SimpleDocTemplate(
            self.output_filename,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=60,
            bottomMargin=50
        )
        
        # Создание элементов документа
        elements = []
        
        # Титульная страница
        elements.extend(self.create_title_page())
        
        # Содержание
        elements.extend(self.create_table_of_contents())
        
        # Основные разделы
        elements.extend(self.create_overview_section())
        elements.extend(self.create_architecture_section())
        elements.extend(self.create_models_section())
        elements.extend(self.create_security_section())
        elements.extend(self.create_installation_section())
        elements.extend(self.create_conclusion_section())
        
        # Сборка PDF
        doc.build(elements, onFirstPage=self.create_header_footer, 
                 onLaterPages=self.create_header_footer)
        
        print(f"PDF документация создана: {self.output_filename}")

def main():
    """Основная функция"""
    print("Генератор PDF документации для системы ДБО")
    print("=" * 50)
    
    generator = DBODocumentGenerator()
    generator.generate_pdf()
    
    print("\nДокументация успешно создана!")
    print("Файл:", generator.output_filename)

if __name__ == "__main__":
    main()
