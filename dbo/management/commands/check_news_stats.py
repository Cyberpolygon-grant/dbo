from django.core.management.base import BaseCommand
from dbo.models import News

class Command(BaseCommand):
    help = 'Показывает статистику новостей'

    def handle(self, *args, **options):
        total_news = News.objects.count()
        active_news = News.objects.filter(is_active=True).count()
        
        self.stdout.write(f'Всего новостей в базе: {total_news}')
        self.stdout.write(f'Активных новостей: {active_news}')
        
        # Показываем новости по категориям
        categories = ['general', 'rates', 'promotions', 'security', 'services']
        for category in categories:
            count = News.objects.filter(category=category, is_active=True).count()
            self.stdout.write(f'  {category}: {count} новостей')
        
        # Показываем первые 10 новостей
        self.stdout.write('\nПервые 10 новостей:')
        for news in News.objects.filter(is_active=True).order_by('-priority', '-created_at')[:10]:
            self.stdout.write(f'  - {news.title} ({news.category})')
