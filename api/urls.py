from django.urls import path
from . import views

urlpatterns = [
    # User related endpoints
    path('user/profile/', views.user_profile, name='api_user_profile'),
    path('user/wallet/', views.user_wallet, name='api_user_wallet'),

    # Transaction related endpoints
    path('transactions/', views.transactions_list, name='api_transactions_list'),
    path('transactions/<uuid:transaction_id>/', views.transaction_detail, name='api_transaction_detail'),

    # Payment requests
    path('payment-requests/', views.payment_requests_list, name='api_payment_requests_list'),
    path('payment-requests/<uuid:request_id>/', views.payment_request_detail, name='api_payment_request_detail'),

    # Payment operations
    path('send-money/', views.send_money, name='api_send_money'),
    path('request-money/', views.request_money, name='api_request_money'),
    path('pay-request/<uuid:request_id>/', views.pay_request, name='api_pay_request'),

    # Wallet operations
    path('fund-wallet/', views.fund_wallet, name='api_fund_wallet'),
    path('withdraw-funds/', views.withdraw_funds, name='api_withdraw_funds'),
]
