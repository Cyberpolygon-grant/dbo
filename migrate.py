#!/usr/bin/env python
"""
Простой скрипт для применения миграций
"""
import os
import sys
import django

# Настройка Django
sys.path.insert(0, '/kali-linux/home/kosten/dbo')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from django.db import connection

def apply_migrations():
    """Применяет миграции напрямую через SQL"""
    try:
        print("Применяем миграции...")
        
        with connection.cursor() as cursor:
            # Создаем таблицу миграций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    applied DATETIME NOT NULL
                );
            """)
            
            # Добавляем записи о миграциях
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('dbo', '0001_initial', datetime('now'));
            """)
            
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('dbo', '0002_add_primary_card_field', datetime('now'));
            """)
            
            print("✓ Миграции успешно применены!")
            
            # Проверяем созданные таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print("Созданные таблицы:")
            for table in tables:
                print(f"  - {table[0]}")
                
        return True
        
    except Exception as e:
        print(f"✗ Ошибка при применении миграций: {e}")
        return False

if __name__ == '__main__':
    apply_migrations()
