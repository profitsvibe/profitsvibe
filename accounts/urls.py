from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from accounts.views import home_view

urlpatterns = [
    path('', home_view, name='home'),
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Password management
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),

    # User profile
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('payment-methods/', views.payment_methods, name='payment_methods'),
    path('add-payment-method/', views.add_payment_method, name='add_payment_method'),
    path('remove-payment-method/<int:method_id>/', views.remove_payment_method, name='remove_payment_method'),
    path('set-default-payment-method/<int:method_id>/', views.set_default_payment_method, name='set_default_payment_method'),
]
