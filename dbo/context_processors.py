from .models import News, Client, Operator
import logging
import traceback

logger = logging.getLogger(__name__)


def news_ticker(request):
    """
    Provides active news and user display data for the base layout.
    This context processor is called on every request.
    """
    user_display_name = None
    user_display_initial = None
    is_dbo_client = False
    is_operator = False
    
    # Определяем красивое имя для шапки
    try:
        if request.user.is_authenticated:
            try:
                client = Client.objects.get(user=request.user)
                user_display_name = client.full_name
                is_dbo_client = True
            except Client.DoesNotExist:
                # Для оператора или обычного пользователя
                full_name = f"{request.user.first_name} {request.user.last_name}".strip()
                user_display_name = full_name or request.user.username
                is_operator = Operator.objects.filter(user=request.user).exists()

            if user_display_name:
                user_display_initial = user_display_name[:1].upper()
    except Exception as e:
        logger.warning(f"Ошибка при определении user_display_name: {e}", exc_info=True)

    # Получаем новости для бегущей строки
    try:
        news = News.objects.filter(is_active=True).order_by('-priority', '-created_at')
        news_count = news.count()
        
        # Логируем только при первом запросе или если есть изменения (для отладки)
        if not hasattr(news_ticker, '_last_logged_count'):
            logger.info(f"Context processor executed. Active news count: {news_count}")
            news_ticker._last_logged_count = news_count
        
        return {
            'news_ticker': news,
            'user_display_name': user_display_name,
            'user_display_initial': user_display_initial,
            'is_dbo_client': is_dbo_client,
            'is_operator': is_operator,
        }
    except Exception as e:
        logger.error(
            f"Ошибка при получении новостей в контекстном процессоре: {e}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        # Возвращаем безопасные значения даже при ошибке
        try:
            return {
                'news_ticker': News.objects.none(),
                'user_display_name': user_display_name,
                'user_display_initial': user_display_initial,
                'is_dbo_client': is_dbo_client,
                'is_operator': is_operator,
            }
        except Exception as fallback_error:
            logger.critical(f"Критическая ошибка в context processor fallback: {fallback_error}")
            # Последний резерв - возвращаем минимальный контекст
            return {
                'news_ticker': [],
                'user_display_name': None,
                'user_display_initial': None,
                'is_dbo_client': False,
                'is_operator': False,
            }


