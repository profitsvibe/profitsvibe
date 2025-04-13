from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime


class Transaction(models.Model):
    """Model for all financial transactions on ProfitsVibe."""
    TRANSACTION_TYPES = (
        ('payment', 'Payment'),
        ('request', 'Request'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions', null=True, blank=True)
    recipient_email = models.EmailField(null=True, blank=True)  # For non-registered users
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} - ${self.amount}"

    def is_p2p_payment(self):
        """Check if this is a peer-to-peer payment."""
        return self.transaction_type == 'payment' and self.recipient is not None

    def mark_as_completed(self):
        """Mark transaction as completed."""
        self.status = 'completed'
        self.save()

    def mark_as_failed(self):
        """Mark transaction as failed."""
        self.status = 'failed'
        self.save()


class PaymentRequest(models.Model):
    """Model for requesting money from other users."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    )

    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_requests_sent')
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_requests_received', null=True, blank=True)
    payer_email = models.EmailField(null=True, blank=True)  # For non-registered users
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateField(null=True, blank=True)

    # If the request was paid, link to the transaction
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Request: {self.requester.username} from {self.payer_email or self.payer.username} - ${self.amount}"

    def mark_as_paid(self, transaction):
        """Mark request as paid."""
        self.status = 'paid'
        self.transaction = transaction
        self.save()

    def mark_as_declined(self):
        """Mark request as declined."""
        self.status = 'declined'
        self.save()

    def is_overdue(self):
        """Check if request is overdue."""
        if self.due_date and self.status == 'pending':
            return datetime.now().date() > self.due_date
        return False


class TransactionFee(models.Model):
    """Model for tracking fees charged on transactions."""
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='fee')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # The percentage rate that was applied
    description = models.CharField(max_length=100, default="Transaction Fee")

    def __str__(self):
        return f"Fee for {self.transaction.transaction_id}: ${self.amount}"


class NotificationSetting(models.Model):
    """User settings for transaction notifications."""
    NOTIFICATION_METHODS = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('none', 'No Notification'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    payment_received = models.CharField(max_length=10, choices=NOTIFICATION_METHODS, default='email')
    payment_sent = models.CharField(max_length=10, choices=NOTIFICATION_METHODS, default='email')
    request_received = models.CharField(max_length=10, choices=NOTIFICATION_METHODS, default='email')
    request_updated = models.CharField(max_length=10, choices=NOTIFICATION_METHODS, default='email')
    balance_low = models.CharField(max_length=10, choices=NOTIFICATION_METHODS, default='email')

    def __str__(self):
        return f"Notification Settings for {self.user.username}"
