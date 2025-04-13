from django.db import models
from django.contrib.auth.models import User
import uuid


class UserProfile(models.Model):
    """Extended user profile model for ProfitsVibe."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Wallet(models.Model):
    """User wallet for managing money."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet: ${self.balance}"

    def deposit(self, amount):
        """Add funds to wallet."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        self.save()
        return True

    def withdraw(self, amount):
        """Remove funds from wallet."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.save()
        return True

    def can_withdraw(self, amount):
        """Check if user has enough balance to withdraw."""
        return amount <= self.balance


class PaymentMethod(models.Model):
    """User's payment methods for funding their wallet."""
    METHOD_CHOICES = (
        ('bank', 'Bank Account'),
        ('card', 'Credit/Debit Card'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=10, choices=METHOD_CHOICES)
    is_default = models.BooleanField(default=False)
    last_four = models.CharField(max_length=4)  # Last 4 digits of card or account
    nickname = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # For bank accounts
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_type = models.CharField(max_length=20, blank=True, null=True)

    # For cards
    card_brand = models.CharField(max_length=20, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    # In production, you would store tokens from your payment processor
    # instead of actual card numbers or bank accounts
    token = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        if self.method_type == 'bank':
            return f"{self.bank_name} ****{self.last_four}"
        return f"{self.card_brand} ****{self.last_four}"
