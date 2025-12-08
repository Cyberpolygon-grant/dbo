"""
URL configuration for cyberpolygon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from dbo import views
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Основные страницы
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("banking-services/", views.banking_services, name="banking_services"),
    path("create-service-request/", views.create_service_request, name="create_service_request"),
    path("connect-service/<int:service_id>/", views.connect_service, name="connect_service"),
    path("disconnect-service/<int:service_id>/", views.disconnect_service, name="disconnect_service"),
    path("my-services/", views.my_services, name="my_services"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("xss-success/", views.xss_success, name="xss_success"),
    path("first-login-password/", views.first_login_password, name="first_login_password"),
    
    # Дашборды
    path("operator1/", views.operator1_dashboard, name="operator1_dashboard"),
    path("operator2/", views.operator2_dashboard, name="operator2_dashboard"),
    path("client/", views.client_dashboard, name="client_dashboard"),
    # attack-dashboard отключен
    
    # Функционал оператора ДБО #1
    path("create-client/", views.create_client, name="create_client"),
    path("operator/transactions/", views.operator_transactions_view, name="operator_transactions"),
    
    # Функционал оператора ДБО #2
    path("review-request/<int:request_id>/", views.review_service_request, name="review_service_request"),
    path("approve-request/<int:request_id>/", views.approve_service_request, name="approve_service_request"),
    path("reject-request/<int:request_id>/", views.reject_service_request, name="reject_service_request"),
    
    # Функционал клиента
    path("create-service-request/", views.create_service_request, name="create_service_request"),
    path("search-services/", views.search_services, name="search_services"),
    # Публичный каталог услуг
    path("services/<int:service_id>/", views.service_detail, name="service_detail"),
    path("api/service-details/<int:service_id>/", views.get_service_details, name="get_service_details"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    
    # Банковские функции для клиентов
    path("client/transfers/", views.transfers_view, name="transfers"),  # Отдельная страница переводов
    path("client/deposits/", views.deposits_view, name="deposits"),
    path("client/transactions/", views.transactions_view, name="transactions"),  # Страница истории операций
    path("client/history/", views.history_view, name="history"),  # Алиас для истории операций
    # кредиты вырезаны
    
    # Банковские услуги
    path("deposits/", views.deposits_view, name="deposits"),
    # кредиты вырезаны
    path("investments/", views.investments_view, name="investments"),
    path("cards/", views.cards_view, name="cards"),
    path("create-deposit/", views.create_deposit, name="create_deposit"),
    path("create-deposit-request/", views.create_deposit_request, name="create_deposit_request"),
    # кредиты вырезаны
    path("create-investment-request/", views.create_investment_request, name="create_investment_request"),
    path("create-card-request/", views.create_card_request, name="create_card_request"),
    path("create-card/", views.create_card, name="create_card"),
    path("card/<int:card_id>/block/", views.block_card, name="block_card"),
    path("card/<int:card_id>/unblock/", views.unblock_card, name="unblock_card"),
    path("card/<int:card_id>/pin/", views.change_card_pin, name="change_card_pin"),
    path("card/<int:card_id>/set-primary/", views.set_primary_card, name="set_primary_card"),
    path("card/unset-primary/", views.unset_primary_card, name="unset_primary_card"),
    
    # Новые банковские сервисы
    # кредиты вырезаны
    path("service/deposits/", views.deposits_service, name="deposits_service"),
    path("service/transfers/", views.transfers_service, name="transfers_service"),
    path("service/cards/", views.cards_service, name="cards_service"),
    path("service/investments/", views.investments_service, name="investments_service"),
    path("api/check-recipient-phone/", views.check_recipient_phone, name="check_recipient_phone"),
    
    
    # Старые маршруты для совместимости
    path("transfers/", views.transfers, name="transfers_old"),
    path("dashboard/", views.dashboard, name="dashboard"),
]

# Serve static files in development (DEBUG=True)
# In production, WhiteNoise handles static files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
