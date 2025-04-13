from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import UserProfile, Wallet, PaymentMethod
from payments.models import Transaction, PaymentRequest, TransactionFee


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model with User data."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'profile_id', 'phone_number', 'date_of_birth',
                  'profile_picture', 'is_verified', 'created_at', 'updated_at']


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model."""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Wallet
        fields = ['username', 'balance', 'currency', 'last_updated']


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for PaymentMethod model."""
    class Meta:
        model = PaymentMethod
        fields = ['id', 'method_type', 'is_default', 'last_four', 'nickname',
                  'bank_name', 'account_type', 'card_brand', 'expiry_date', 'created_at']


class TransactionFeeSerializer(serializers.ModelSerializer):
    """Serializer for TransactionFee model."""
    class Meta:
        model = TransactionFee
        fields = ['amount', 'percentage', 'description']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    fee = TransactionFeeSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ['transaction_id', 'sender', 'sender_name', 'recipient',
                  'recipient_name', 'recipient_email', 'amount', 'description',
                  'transaction_type', 'status', 'created_at', 'updated_at', 'fee']

    def get_sender_name(self, obj):
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.username
        return None

    def get_recipient_name(self, obj):
        if obj.recipient:
            return obj.recipient.get_full_name() or obj.recipient.username
        return obj.recipient_email


class PaymentRequestSerializer(serializers.ModelSerializer):
    """Serializer for PaymentRequest model."""
    requester_name = serializers.SerializerMethodField()
    payer_name = serializers.SerializerMethodField()
    transaction = TransactionSerializer(read_only=True)

    class Meta:
        model = PaymentRequest
        fields = ['request_id', 'requester', 'requester_name', 'payer',
                  'payer_name', 'payer_email', 'amount', 'description',
                  'status', 'created_at', 'updated_at', 'due_date', 'transaction']

    def get_requester_name(self, obj):
        if obj.requester:
            return obj.requester.get_full_name() or obj.requester.username
        return None

    def get_payer_name(self, obj):
        if obj.payer:
            return obj.payer.get_full_name() or obj.payer.username
        return obj.payer_email
