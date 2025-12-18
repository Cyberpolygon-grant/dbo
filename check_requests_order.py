#!/usr/bin/env python3
"""
Скрипт для проверки порядка заявок
Может автоматически исправить порядок, если передан аргумент --fix
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberpolygon.settings')
django.setup()

from dbo.models import ServiceRequest

def check_requests_order(auto_fix=False):
    """Проверяет порядок заявок и их ID"""
    print("=" * 70)
    print("📋 ПРОВЕРКА ПОРЯДКА ЗАЯВОК")
    print("=" * 70)
    
    requests = ServiceRequest.objects.all().order_by('id')
    
    if not requests.exists():
        print("\n⚠️  Заявок не найдено в базе данных")
        print("💡 Запустите: bash restart.sh")
        return False
    
    print(f"\n📊 Всего заявок: {requests.count()}")
    print("-" * 70)
    
    for i, req in enumerate(requests, 1):
        is_test = req.service_name.lower().startswith('тест')
        marker = "🧪 ТЕСТОВАЯ" if is_test else "📝 Обычная"
        
        print(f"\n{i}. {marker}")
        print(f"   ID: {req.id}")
        print(f"   Название: {req.service_name}")
        print(f"   Клиент: {req.client.full_name}")
        print(f"   Статус: {req.status}")
        print(f"   URL: /review-services/{req.id}")
    
    print("\n" + "-" * 70)
    
    # Проверяем, что тестовая заявка первая
    first_request = requests.first()
    is_first_test = first_request.service_name.lower().startswith('тест')
    
    print("\n🔍 ПРОВЕРКА ПОРЯДКА:")
    if is_first_test and first_request.id == 1:
        print("   ✅ Тестовая заявка ПЕРВАЯ (ID=1)")
        print(f"   ✅ URL: /review-services/1")
        return True
    elif is_first_test:
        print(f"   ⚠️  Тестовая заявка первая, но ID={first_request.id} (не 1)")
        print(f"   💡 URL: /review-services/{first_request.id}")
        
        if auto_fix:
            print("\n🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ...")
            print("   🔄 Перезапуск init_test_request.py...")
            import subprocess
            result = subprocess.run(['python', 'init_test_request.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Заявка пересоздана!")
                # Повторная проверка
                return check_requests_order(auto_fix=False)
            else:
                print(f"   ❌ Ошибка при пересоздании: {result.stderr}")
                return False
        else:
            print("   💡 Запустите: python check_requests_order.py --fix (автоматическое исправление)")
            print("   💡 Или: bash restart.sh (полный перезапуск)")
        return False
    else:
        print("   ❌ Тестовая заявка НЕ первая!")
        
        if auto_fix:
            print("\n🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ...")
            print("   🔄 Перезапуск init_test_request.py...")
            import subprocess
            result = subprocess.run(['python', 'init_test_request.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Заявка пересоздана!")
                # Повторная проверка
                return check_requests_order(auto_fix=False)
            else:
                print(f"   ❌ Ошибка при пересоздании: {result.stderr}")
                return False
        else:
            print("   💡 Запустите: python check_requests_order.py --fix (автоматическое исправление)")
            print("   💡 Или: bash restart.sh (порядок будет исправлен)")
        return False
    
    print("=" * 70)

if __name__ == '__main__':
    auto_fix = '--fix' in sys.argv
    
    if auto_fix:
        print("⚙️  Режим автоматического исправления активирован\n")
    
    try:
        success = check_requests_order(auto_fix=auto_fix)
        print("=" * 70)
        
        if success:
            exit(0)
        else:
            exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        exit(2)
