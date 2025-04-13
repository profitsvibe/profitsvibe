from django.contrib import admin
from .models import UserProfile, Wallet, PaymentMethod


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_id', 'phone_number', 'is_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    list_filter = ('is_verified', 'created_at')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'currency', 'last_updated')
    search_fields = ('user__username', 'user__email')
    list_filter = ('currency',)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'is_default', 'last_four', 'created_at')
    search_fields = ('user__username', 'user__email', 'nickname')
    list_filter = ('method_type', 'is_default', 'created_at')
