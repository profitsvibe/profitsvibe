from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction

from .models import UserProfile, PaymentMethod
from .forms import UserRegistrationForm, UserProfileForm, PaymentMethodForm

def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect to dashboard if logged in
    else:
        return render(request, 'home.html')  # Show marketing home page if not logged in

def register(request):
    """Register a new user."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                # UserProfile and Wallet are created automatically via signals

                # Log the user in
                login(request, user)
                messages.success(request, f"Welcome to ProfitsVibe, {user.username}! Your account has been created.")
                return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    """Display and edit user profile."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def settings(request):
    """User settings page."""
    return render(request, 'accounts/settings.html')


@login_required
def payment_methods(request):
    """View and manage payment methods."""
    payment_methods = PaymentMethod.objects.filter(user=request.user)

    return render(request, 'accounts/payment_methods.html', {
        'payment_methods': payment_methods
    })


@login_required
def add_payment_method(request):
    """Add a new payment method."""
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save(commit=False)
            payment_method.user = request.user

            # Check if this is the first payment method for the user
            if PaymentMethod.objects.filter(user=request.user).count() == 0:
                payment_method.is_default = True

            payment_method.save()
            messages.success(request, "Payment method added successfully.")
            return redirect('payment_methods')
    else:
        form = PaymentMethodForm()

    return render(request, 'accounts/add_payment_method.html', {
        'form': form
    })


@login_required
def remove_payment_method(request, method_id):
    """Remove a payment method."""
    payment_method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)

    # If this is the default payment method, find another one to make default
    if payment_method.is_default:
        other_method = PaymentMethod.objects.filter(user=request.user).exclude(id=method_id).first()
        if other_method:
            other_method.is_default = True
            other_method.save()

    payment_method.delete()
    messages.success(request, "Payment method removed successfully.")
    return redirect('payment_methods')


@login_required
def set_default_payment_method(request, method_id):
    """Set a payment method as default."""
    with transaction.atomic():
        # Set all payment methods as non-default
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)

        # Set the selected payment method as default
        payment_method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)
        payment_method.is_default = True
        payment_method.save()

    messages.success(request, f"{payment_method} set as your default payment method.")
    return redirect('payment_methods')

@login_required
def dashboard(request):
    # Get the user's wallet
    try:
        wallet = request.user.wallet  # Adjust this according to your model relationships
    except:
        wallet = {"balance": "0.00", "currency": "USD"}  # Fallback for testing

    # Get transactions (adjust queries based on your model structure)
    sent_transactions = []  # Replace with actual query
    received_transactions = []  # Replace with actual query
    pending_requests = []  # Replace with actual query

    context = {
        'wallet': wallet,
        'sent_transactions': sent_transactions,
        'received_transactions': received_transactions,
        'pending_requests': pending_requests,
    }

    return render(request, 'payments/dashboard.html', context)


