from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, PaymentMethod


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input pl-10',
            'placeholder': 'Enter your email'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-input pl-10',
            'placeholder': 'Enter your username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input pl-10',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input pl-10',
            'placeholder': 'Confirm your password'
        })


class CustomLoginForm(AuthenticationForm):
    """Styled login form."""
    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Username or Email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600',
            'placeholder': 'Password'
        })


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'date_of_birth', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600'
            })

        self.fields['date_of_birth'].widget.attrs.update({
            'type': 'date'
        })


class PaymentMethodForm(forms.ModelForm):
    """Form for adding a payment method."""
    class Meta:
        model = PaymentMethod
        fields = ['method_type', 'last_four', 'nickname', 'bank_name', 'account_type', 'card_brand', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(PaymentMethodForm, self).__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600'
            })

        self.fields['nickname'].required = False
        self.fields['bank_name'].required = False
        self.fields['account_type'].required = False
        self.fields['card_brand'].required = False
        self.fields['expiry_date'].required = False

    def clean(self):
        cleaned_data = super().clean()
        method_type = cleaned_data.get('method_type')

        if method_type == 'bank':
            if not cleaned_data.get('bank_name'):
                self.add_error('bank_name', 'Bank name is required for bank accounts')
            if not cleaned_data.get('account_type'):
                self.add_error('account_type', 'Account type is required for bank accounts')

        elif method_type == 'card':
            if not cleaned_data.get('card_brand'):
                self.add_error('card_brand', 'Card brand is required for credit/debit cards')
            if not cleaned_data.get('expiry_date'):
                self.add_error('expiry_date', 'Expiry date is required for credit/debit cards')

        return cleaned_data

