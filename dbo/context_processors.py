from .models import News, Client, Operator
import logging

logger = logging.getLogger(__name__)


def news_ticker(request):
    """Provides active news and user display data for the base layout."""
    user_display_name = None
    user_display_initial = None
    try:
        if request.user.is_authenticated:
            # Определяем красивое имя для шапки
            try:
                client = Client.objects.get(user=request.user)
                user_display_name = client.full_name
            except Client.DoesNotExist:
                # Для оператора или обычного пользователя
                full_name = f"{request.user.first_name} {request.user.last_name}".strip()
                user_display_name = full_name or request.user.username

            if user_display_name:
                user_display_initial = user_display_name[:1].upper()
    except Exception as e:
        logger.warning(f"Ошибка при определении user_display_name: {e}")

    try:
        news = News.objects.filter(is_active=True).order_by('-priority', '-created_at')
        # Флаги ролей для шаблонов
        is_dbo_client = False
        is_operator = False
        if request.user.is_authenticated:
            try:
                _ = Client.objects.get(user=request.user)
                is_dbo_client = True
            except Client.DoesNotExist:
                is_operator = Operator.objects.filter(user=request.user).exists()
        return {
            'news_ticker': news,
            'user_display_name': user_display_name,
            'user_display_initial': user_display_initial,
            'is_dbo_client': is_dbo_client,
            'is_operator': is_operator,
        }
    except Exception as e:
        logger.error(f"Ошибка при получении новостей в контекстном процессоре: {e}")
        return {
            'news_ticker': News.objects.none(),
            'user_display_name': user_display_name,
            'user_display_initial': user_display_initial,
        }


