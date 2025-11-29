#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Проверяет, есть ли услуги с описанием, содержащим указанные слова.

Запуск примеры:
  python3 service_checker.py --words "план,рассрочка" --mode any
  python3 service_checker.py --words "инвестиции,риск" --mode all

Параметры:
  --words   список слов через запятую (обязательно)
  --mode    any | all (по умолчанию any)
"""

import os
import sys
import argparse
import django
from typing import List
from django.db.models import Q


# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cyberpolygon.settings")
django.setup()

from dbo.models import Service  # noqa: E402


def parse_words(words_csv: str) -> List[str]:
    return [w.strip() for w in (words_csv or "").split(',') if w.strip()]


def find_services(words: List[str], mode: str) -> List[Service]:
    qs = Service.objects.filter(is_active=True)
    if not words:
        return list(qs[:0])

    if mode == 'all':
        for w in words:
            qs = qs.filter(description__icontains=w)
        return list(qs)

    # mode == 'any'
    q = Q()
    for w in words:
        q |= Q(description__icontains=w)
    return list(qs.filter(q))


def main() -> None:
    parser = argparse.ArgumentParser(description="Check services containing specific words in description")
    parser.add_argument('--words', required=True, help='Comma-separated words to search for')
    parser.add_argument('--mode', choices=['any', 'all'], default='any', help='Match mode: any or all (default any)')
    args = parser.parse_args()

    words = parse_words(args.words)
    if not words:
        print("[ERROR] No words provided (after parsing)", file=sys.stderr)
        sys.exit(2)

    print(f"[INFO] Searching services | mode={args.mode} | words={words}")
    matches = find_services(words, args.mode)
    print(f"[INFO] Found {len(matches)} services")

    for s in matches:
        print(f"- id={s.id} name='{s.name}'")

    if not matches:
        sys.exit(1)


if __name__ == '__main__':
    main()


