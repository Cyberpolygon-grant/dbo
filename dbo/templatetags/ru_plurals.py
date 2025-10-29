from django import template

register = template.Library()


@register.filter
def ru_pluralize(value, forms="заявка,заявки,заявок"):
    """
    Russian pluralization helper.
    Usage:
        {{ count }} {{ count|ru_pluralize:"новая заявка,новые заявки,новых заявок" }}
    forms: singular, paucal (2-4), plural (5+)
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = 0

    parts = [s.strip() for s in str(forms).split(',')]
    # Ensure 3 forms
    while len(parts) < 3:
        parts.append(parts[-1] if parts else '')

    # Russian rules
    n_abs = abs(n)
    last_two = n_abs % 100
    last = n_abs % 10

    if 11 <= last_two <= 14:
        idx = 2
    elif last == 1:
        idx = 0
    elif 2 <= last <= 4:
        idx = 1
    else:
        idx = 2

    return parts[idx]


