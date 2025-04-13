from django import forms
from django.core.validators import MinValueValidator, EmailValidator
from decimal import Decimal
from django.contrib.auth.models import User
from datetime import date, timedelta
from .models import PaymentRequest, Transaction
from accounts.models import PaymentMethod


class SendMoneyForm(forms.Form):
    """Form for sending money to another user."""
    recipient_email = forms.EmailField(
        label="Recipient Email",
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Enter recipient email'
        })
    )

    amount = forms.DecimalField(
        label="Amount ($)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Amount to send',
            'step': '0.01',
            'min': '0.01'
        })
    )

    description = forms.CharField(
        label="Description (optional)",
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'What is this payment for?'
        })
    )

    def clean_recipient_email(self):
        """Validate that user is not sending money to themselves."""
        email = self.cleaned_data['recipient_email']
        if self.initial.get('user') and self.initial.get('user').email == email:
            raise forms.ValidationError("You cannot send money to yourself.")
        return email


class RequestMoneyForm(forms.Form):
    """Form for requesting money from another user."""
    payer_email = forms.EmailField(
        label="Email Address",
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Enter email address'
        })
    )

    amount = forms.DecimalField(
        label="Amount ($)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Amount to request',
            'step': '0.01',
            'min': '0.01'
        })
    )

    description = forms.CharField(
        label="What is this for?",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Reason for the request'
        })
    )

    due_date = forms.DateField(
        label="Due Date (optional)",
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'type': 'date'
        })
    )

    def clean_payer_email(self):
        """Validate that user is not requesting money from themselves."""
        email = self.cleaned_data['payer_email']
        if self.initial.get('user') and self.initial.get('user').email == email:
            raise forms.ValidationError("You cannot request money from yourself.")
        return email

    def clean_due_date(self):
        """Validate that due date is not in the past."""
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < date.today():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date


class FundWalletForm(forms.Form):
    """Form for adding funds to user's wallet."""
    AMOUNT_CHOICES = [
        (Decimal('10.00'), '$10.00'),
        (Decimal('25.00'), '$25.00'),
        (Decimal('50.00'), '$50.00'),
        (Decimal('100.00'), '$100.00'),
        (Decimal('250.00'), '$250.00'),
        (Decimal('500.00'), '$500.00'),
    ]

    amount = forms.DecimalField(
        label="Amount to Add",
        widget=forms.Select(choices=AMOUNT_CHOICES, attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600'
        })
    )

    payment_method = forms.ModelChoiceField(
        label="Payment Method",
        queryset=None,
        empty_label="Add a new payment method",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600'
        })
    )

    # Fields for adding a new payment method (would be shown/hidden with JavaScript)
    new_method_type = forms.ChoiceField(
        label="Payment Method Type",
        choices=PaymentMethod.METHOD_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500'
        })
    )

    # Card fields
    card_number = forms.CharField(
        label="Card Number",
        required=False,
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'XXXX XXXX XXXX XXXX'
        })
    )

    expiry_date = forms.CharField(
        label="Expiry Date (MM/YY)",
        required=False,
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'MM/YY'
        })
    )

    cvv = forms.CharField(
        label="CVV",
        required=False,
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'XXX'
        })
    )

    # Bank account fields
    bank_name = forms.CharField(
        label="Bank Name",
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Enter bank name'
        })
    )

    account_number = forms.CharField(
        label="Account Number",
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Enter account number'
        })
    )

    routing_number = forms.CharField(
        label="Routing Number",
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Enter routing number'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(FundWalletForm, self).__init__(*args, **kwargs)

        if self.user:
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=self.user)

    def clean(self):
        """Validate that either an existing payment method is selected or new details are provided."""
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        new_method_type = cleaned_data.get('new_method_type')

        if not payment_method and not new_method_type:
            raise forms.ValidationError("Please select a payment method or add a new one.")

        # If adding a new card, validate card fields
        if new_method_type == 'card':
            card_number = cleaned_data.get('card_number')
            expiry_date = cleaned_data.get('expiry_date')
            cvv = cleaned_data.get('cvv')

            if not card_number or not expiry_date or not cvv:
                raise forms.ValidationError("Please fill in all card details.")

        # If adding a new bank account, validate bank fields
        elif new_method_type == 'bank':
            bank_name = cleaned_data.get('bank_name')
            account_number = cleaned_data.get('account_number')
            routing_number = cleaned_data.get('routing_number')

            if not bank_name or not account_number or not routing_number:
                raise forms.ValidationError("Please fill in all bank account details.")

        return cleaned_data


class WithdrawFundsForm(forms.Form):
    """Form for withdrawing funds to a bank account."""
    amount = forms.DecimalField(
        label="Amount to Withdraw ($)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Amount to withdraw',
            'step': '0.01',
            'min': '0.01'
        })
    )

    bank_account = forms.ModelChoiceField(
        label="Bank Account",
        queryset=None,
        empty_label=None,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.max_amount = kwargs.pop('max_amount', Decimal('0.00'))
        super(WithdrawFundsForm, self).__init__(*args, **kwargs)

        if self.user:
            self.fields['bank_account'].queryset = PaymentMethod.objects.filter(
                user=self.user,
                method_type='bank'
            )

    def clean_amount(self):
        """Validate that withdrawal amount is not greater than available balance."""
        amount = self.cleaned_data['amount']
        if amount > self.max_amount:
            raise forms.ValidationError(f"You can withdraw at most ${self.max_amount}.")
        return amount
