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
    
    # Пропускаем тяжелые запросы для страницы входа и других публичных страниц
    path = request.path
    if path in ['/login', '/logout', '/']:
        # Для публичных страниц возвращаем минимальный контекст без запросов к БД
        return {
            'news_ticker': News.objects.none(),
            'user_display_name': None,
            'user_display_initial': None,
            'is_dbo_client': False,
            'is_operator': False,
        }
    
    # Определяем красивое имя для шапки (оптимизировано)
    try:
        if request.user.is_authenticated:
            # Используем только() для получения только нужных полей
            try:
                client = Client.objects.only('full_name').get(user=request.user)
                user_display_name = client.full_name
                is_dbo_client = True
            except Client.DoesNotExist:
                # Для оператора или обычного пользователя
                full_name = f"{request.user.first_name} {request.user.last_name}".strip()
                user_display_name = full_name or request.user.username
                # Используем exists() вместо get() для быстрой проверки
                is_operator = Operator.objects.filter(user=request.user).exists()

            if user_display_name:
                user_display_initial = user_display_name[:1].upper()
    except Exception as e:
        logger.warning(f"Ошибка при определении user_display_name: {e}", exc_info=True)

    # Получаем новости для бегущей строки (только для авторизованных пользователей)
    # Ограничиваем количество и используем только необходимые поля
    try:
        news = News.objects.filter(is_active=True).order_by('-priority', '-created_at')[:20]  # Уменьшили до 20
        
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


