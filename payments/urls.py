from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('send-money/', views.send_money, name='send_money'),
    path('request-money/', views.request_money, name='request_money'),
    path('fund-wallet/', views.fund_wallet, name='fund_wallet'),
    path('withdraw-funds/', views.withdraw_funds, name='withdraw_funds'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),
    path('payment-requests/', views.payment_requests, name='payment_requests'),
    path('pay-request/<uuid:request_id>/', views.pay_request, name='pay_request'),
    path('decline-request/<uuid:request_id>/', views.decline_request, name='decline_request'),
    path('cancel-request/<uuid:request_id>/', views.cancel_request, name='cancel_request'),
]
