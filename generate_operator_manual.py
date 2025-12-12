
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# Регистрируем шрифты для поддержки кириллицы
try:
    # Пробуем использовать системные шрифты
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    font_name = 'DejaVuSans'
    font_bold = 'DejaVuSans-Bold'
except:
    # Если не получилось, используем стандартные
    font_name = 'Helvetica'
    font_bold = 'Helvetica-Bold'

# Создаем PDF
pdf_file = "Инструкция_оператора_ДБО1.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

story = []
styles = getSampleStyleSheet()

# Стили с кириллицей
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=18,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName=font_bold
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=colors.HexColor('#2c3e50'),
    spaceAfter=12,
    spaceBefore=20,
    fontName=font_bold
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=11,
    textColor=colors.HexColor('#2c3e50'),
    spaceAfter=12,
    fontName=font_name
)

# Заголовок
story.append(Paragraph("БАНК «ФИНАНСПРО»", title_style))
story.append(Paragraph("Система дистанционного банковского обслуживания", heading_style))
story.append(Spacer(1, 0.5*cm))

# Гриф
confidential_style = ParagraphStyle(
    'Confidential',
    parent=styles['Normal'],
    fontSize=12,
    textColor=colors.red,
    alignment=TA_CENTER,
    fontName=font_bold
)
story.append(Paragraph("КОНФИДЕНЦИАЛЬНО", confidential_style))
story.append(Paragraph("Для служебного пользования", confidential_style))
story.append(Spacer(1, 1*cm))

# Основной заголовок
story.append(Paragraph("ИНСТРУКЦИЯ ПО РАБОТЕ В СИСТЕМЕ ДБО", title_style))
story.append(Paragraph("Оператор клиентского обслуживания (ДБО #1)", heading_style))
story.append(Spacer(1, 0.5*cm))

# Дата
date_str = datetime.now().strftime("%d.%m.%Y")
story.append(Paragraph(f"<i>Дата выдачи: {date_str}</i>", normal_style))
story.append(Spacer(1, 1*cm))

# Раздел 1: Учетные данные
story.append(Paragraph("1. УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА В СИСТЕМУ", heading_style))
story.append(Spacer(1, 0.3*cm))

# Таблица с учетными данными
credentials_data = [
    ['Параметр', 'Значение'],
    ['URL системы', 'http://10.18.2.6:8000/'],
    ['Логин', 'operator1'],
    ['Пароль', '1q2w#E$R'],
    ['Роль', 'Оператор ДБО #1 (Клиентское обслуживание)']
]

credentials_table = Table(credentials_data, colWidths=[6*cm, 10*cm])
credentials_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTNAME', (0, 1), (-1, -1), font_bold),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
]))

story.append(credentials_table)
story.append(Spacer(1, 0.5*cm))

# Предупреждение
warning_style = ParagraphStyle(
    'Warning',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.red,
    spaceAfter=12,
    fontName=font_bold,
    borderColor=colors.red,
    borderWidth=2,
    borderPadding=10
)
story.append(Paragraph("⚠ ВАЖНО: Храните учетные данные в секрете! Не передавайте третьим лицам!", warning_style))
story.append(Spacer(1, 1*cm))

# Раздел 2: Обязанности
story.append(Paragraph("2. ОБЯЗАННОСТИ ОПЕРАТОРА ДБО #1", heading_style))
story.append(Paragraph("• Обработка заявок на регистрацию новых клиентов в системе ДБО", normal_style))
story.append(Paragraph("• Создание учетных записей клиентов банка", normal_style))
story.append(Paragraph("• Просмотр и мониторинг транзакций клиентов", normal_style))
story.append(Paragraph("• Ведение журнала действий оператора", normal_style))
story.append(Spacer(1, 0.5*cm))

# Раздел 3: Пошаговая инструкция
story.append(Paragraph("3. ПОРЯДОК РАБОТЫ В СИСТЕМЕ", heading_style))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("<b>3.1. Вход в систему:</b>", normal_style))
story.append(Paragraph("1) Откройте браузер и перейдите по адресу: http://10.18.2.6:8000/login/", normal_style))
story.append(Paragraph("2) Введите логин: <b>operator1</b>", normal_style))
story.append(Paragraph("3) Введите пароль: <b>1q2w#E$R</b>", normal_style))
story.append(Paragraph("4) Нажмите кнопку «Войти»", normal_style))
story.append(Spacer(1, 0.5*cm))

story.append(Paragraph("<b>3.2. Создание нового клиента:</b>", normal_style))
story.append(Paragraph("1) На главной странице оператора нажмите «Создать клиента»", normal_style))
story.append(Paragraph("2) Заполните форму регистрации:", normal_style))
story.append(Paragraph("   - ФИО клиента", normal_style))
story.append(Paragraph("   - Email (используется как логин)", normal_style))
story.append(Paragraph("   - Номер телефона", normal_style))
story.append(Paragraph("3) Нажмите кнопку «Создать клиента»", normal_style))
story.append(Paragraph("4) Сохраните сгенерированные учетные данные клиента", normal_style))
story.append(Spacer(1, 0.5*cm))

story.append(Paragraph("<b>3.3. Просмотр транзакций:</b>", normal_style))
story.append(Paragraph("1) На главной странице нажмите «Транзакции»", normal_style))
story.append(Paragraph("2) Используйте фильтры для поиска нужных операций", normal_style))
story.append(Paragraph("3) Просматривайте детали транзакций при необходимости", normal_style))
story.append(Spacer(1, 0.5*cm))

story.append(Paragraph("<b>3.4. Просмотр журнала действий:</b>", normal_style))
story.append(Paragraph("1) На главной странице нажмите «Мои логи»", normal_style))
story.append(Paragraph("2) Просмотрите историю всех ваших действий в системе", normal_style))
story.append(Paragraph("3) Используйте фильтры по типу события и дате", normal_style))
story.append(Spacer(1, 1*cm))

# Раздел 4: Правила безопасности
story.append(Paragraph("4. ПРАВИЛА ИНФОРМАЦИОННОЙ БЕЗОПАСНОСТИ", heading_style))
story.append(Paragraph("• НЕ передавайте свои учетные данные другим лицам", normal_style))
story.append(Paragraph("• НЕ используйте публичные компьютеры для входа в систему", normal_style))
story.append(Paragraph("• ВСЕГДА выходите из системы после завершения работы", normal_style))
story.append(Paragraph("• НЕ оставляйте рабочее место без блокировки компьютера", normal_style))
story.append(Paragraph("• Сообщайте о любых подозрительных действиях в отдел ИБ", normal_style))
story.append(Spacer(1, 1*cm))

# Контакты
story.append(Paragraph("5. КОНТАКТНАЯ ИНФОРМАЦИЯ", heading_style))
story.append(Paragraph("Отдел информационной безопасности: security@finanspro.ru", normal_style))
story.append(Paragraph("Техническая поддержка: support@finanspro.ru", normal_style))
story.append(Paragraph("Горячая линия: 8-800-555-35-35", normal_style))
story.append(Spacer(1, 1*cm))

# Подпись
story.append(Spacer(1, 1*cm))
signature_data = [
    ['Начальник отдела ДБО', '_____________', 'И.О. Петров'],
    ['', '', ''],
    ['Получил:', '_____________', '____________________'],
    ['', '(подпись)', '(ФИО)']
]

signature_table = Table(signature_data, colWidths=[5*cm, 4*cm, 6*cm])
signature_table.setStyle(TableStyle([
    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ('ALIGN', (2, 0), (2, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, -1), font_name),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))

story.append(signature_table)

# Генерация PDF
doc.build(story)
print(f"✓ PDF успешно создан: {pdf_file}")
print(f"✓ URL входа: http://10.18.2.6:8000/")
print(f"✓ Логин: operator1")
print(f"✓ Пароль: 1q2w#E$R")
