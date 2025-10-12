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
    path("services-management/", views.services_management, name="services_management"),
    path("connect-service/<int:service_id>/", views.connect_service, name="connect_service"),
    path("disconnect-service/<int:service_id>/", views.disconnect_service, name="disconnect_service"),
    path("my-services/", views.my_services, name="my_services"),
    
    # Дашборды
    path("operator1/", views.operator1_dashboard, name="operator1_dashboard"),
    path("operator2/", views.operator2_dashboard, name="operator2_dashboard"),
    path("client/", views.client_dashboard, name="client_dashboard"),
    # attack-dashboard отключен
    
    # Функционал оператора ДБО #1
    path("create-client/", views.create_client, name="create_client"),
    path("phishing-email/<int:email_id>/", views.phishing_email_view, name="phishing_email"),
    
    # Функционал оператора ДБО #2
    path("review-request/<int:request_id>/", views.review_service_request, name="review_service_request"),
    path("approve-request/<int:request_id>/", views.approve_service_request, name="approve_service_request"),
    
    # Функционал клиента
    path("create-service-request/", views.create_service_request, name="create_service_request"),
    path("search-services/", views.search_services, name="search_services"),
    # Публичный каталог услуг
    path("services/<int:service_id>/", views.service_detail, name="service_detail"),
    path("api/service-details/<int:service_id>/", views.get_service_details, name="get_service_details"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    
    # Банковские функции для клиентов
    path("client/accounts/", views.accounts_view, name="accounts"),
    path("client/accounts/create", views.create_bank_account, name="create_bank_account"),
    path("client/transfers/", views.transfers_view, name="transfers"),
    path("client/deposits/", views.deposits_view, name="deposits"),
    path("client/credits/", views.credits_view, name="credits"),
    
    # Банковские услуги
    path("deposits/", views.deposits_view, name="deposits"),
    path("credits/", views.credits_view, name="credits"),
    path("investments/", views.investments_view, name="investments"),
    path("cards/", views.cards_view, name="cards"),
    path("create-deposit/", views.create_deposit, name="create_deposit"),
    path("create-credit-request/", views.create_credit_request, name="create_credit_request"),
    path("create-investment-request/", views.create_investment_request, name="create_investment_request"),
    path("create-card-request/", views.create_card_request, name="create_card_request"),
    
    # Новые банковские сервисы
    path("service/accounts/", views.accounts_service, name="accounts_service"),
    path("service/credits/", views.credits_service, name="credits_service"),
    path("service/deposits/", views.deposits_service, name="deposits_service"),
    path("service/transfers/", views.transfers_service, name="transfers_service"),
    path("service/cards/", views.cards_service, name="cards_service"),
    path("service/investments/", views.investments_service, name="investments_service"),
    
    # Старые маршруты для совместимости
    path("accounts/", views.accounts, name="accounts_old"),
    path("transfers/", views.transfers, name="transfers_old"),
    path("dashboard/", views.dashboard, name="dashboard"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
