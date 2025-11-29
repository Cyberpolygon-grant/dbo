#!/usr/bin/env python3
# coding: utf-8
import os
import sys
import django
from django.contrib.auth.models import User

# ================== Конфигурация (укажите значения ниже) ==================
# Настройки Django проекта
DJANGO_SETTINGS_MODULE = "cyberpolygon.settings"

# Кого менять (ищем по email, при отсутствии — по username)
TARGET_EMAIL = "ivan.petrov@example.com"   # укажите email созданного клиента
TARGET_USERNAME = None                      # опционально, если нужно искать по username

# Новый пароль (как просили)
NEW_PASSWORD = "1й2ц№У;К"


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    django.setup()

    user = None
    # Ищем по email
    if TARGET_EMAIL:
        user = User.objects.filter(email=TARGET_EMAIL).first()
    # Если не нашли — пробуем по username
    if not user and TARGET_USERNAME:
        user = User.objects.filter(username=TARGET_USERNAME).first()

    if not user:
        print("ERROR: Пользователь не найден по указанным email/username", file=sys.stderr)
        sys.exit(1)

    user.set_password(NEW_PASSWORD)
    user.save(update_fields=["password"])
    print(f"OK: пароль пользователя '{user.username}' обновлён")


if __name__ == "__main__":
    main()


