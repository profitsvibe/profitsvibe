from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from decimal import Decimal

from .models import Transaction, PaymentRequest, TransactionFee
from .forms import SendMoneyForm, RequestMoneyForm, FundWalletForm
from accounts.models import Wallet


@login_required
def dashboard(request):
    """User dashboard showing recent transactions and balance."""
    # Get user transactions (both sent and received)
    sent_transactions = Transaction.objects.filter(
        sender=request.user
    ).order_by('-created_at')[:5]

    received_transactions = Transaction.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:5]

    # Get pending payment requests
    pending_requests = PaymentRequest.objects.filter(
        payer=request.user,
        status='pending'
    ).order_by('-created_at')

    # Get user's wallet balance
    wallet = request.user.wallet

    context = {
        'sent_transactions': sent_transactions,
        'received_transactions': received_transactions,
        'pending_requests': pending_requests,
        'wallet': wallet,
    }

    return render(request, 'payments/dashboard.html', context)


@login_required
def send_money(request):
    """View for sending money to another user."""
    if request.method == 'POST':
        form = SendMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            recipient_email = form.cleaned_data['recipient_email']
            description = form.cleaned_data['description']

            # Check if user has sufficient funds
            sender_wallet = request.user.wallet
            if not sender_wallet.can_withdraw(amount):
                messages.error(request, "Insufficient funds in your wallet.")
                return redirect('send_money')

            # Find recipient by email (if they exist in our system)
            try:
                recipient = User.objects.get(email=recipient_email)
                recipient_exists = True
            except User.DoesNotExist:
                recipient = None
                recipient_exists = False

            # Calculate transaction fee (example: 2% for simplicity)
            fee_percentage = Decimal('0.02')
            fee_amount = amount * fee_percentage
            net_amount = amount - fee_amount

            with db_transaction.atomic():
                # Create transaction
                transaction = Transaction.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    recipient_email=recipient_email,
                    amount=amount,
                    description=description,
                    transaction_type='payment',
                    status='pending'
                )

                # Create fee record
                TransactionFee.objects.create(
                    transaction=transaction,
                    amount=fee_amount,
                    percentage=fee_percentage,
                    description="ProfitsVibe Service Fee"
                )

                # Process the payment
                try:
                    # Deduct amount from sender
                    sender_wallet.withdraw(amount)

                    # If recipient exists in our system, add money to their wallet
                    if recipient_exists:
                        recipient_wallet = recipient.wallet
                        recipient_wallet.deposit(net_amount)
                        transaction.status = 'completed'
                    else:
                        # For non-registered users, we'll send an email with a claim link
                        # (This would be implemented in a real system)
                        transaction.status = 'completed'  # Mark completed even if recipient is external

                        # Send email to recipient
                        send_mail(
                            f"{request.user.get_full_name()} sent you ${amount}",
                            f"You received ${amount} from {request.user.get_full_name()}.\n\n"
                            f"Message: {description}\n\n"
                            f"Sign up at ProfitsVibe.com to claim your money!",
                            settings.EMAIL_HOST_USER,
                            [recipient_email],
                            fail_silently=False,
                        )

                    transaction.save()
                    messages.success(request, f"Successfully sent ${amount} to {recipient_email}")
                    return redirect('dashboard')

                except ValueError as e:
                    transaction.status = 'failed'
                    transaction.save()
                    messages.error(request, str(e))
                    return redirect('send_money')
    else:
        form = SendMoneyForm()

    return render(request, 'payments/send_money.html', {'form': form})


@login_required
def request_money(request):
    """View for requesting money from another user."""
    if request.method == 'POST':
        form = RequestMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payer_email = form.cleaned_data['payer_email']
            description = form.cleaned_data['description']
            due_date = form.cleaned_data.get('due_date')  # Optional

            # Check if payer exists in our system
            try:
                payer = User.objects.get(email=payer_email)
            except User.DoesNotExist:
                payer = None

            # Create payment request
            payment_request = PaymentRequest.objects.create(
                requester=request.user,
                payer=payer,
                payer_email=payer_email,
                amount=amount,
                description=description,
                due_date=due_date,
                status='pending'
            )

            # Send email notification to payer
            send_mail(
                f"{request.user.get_full_name()} requested ${amount} from you",
                f"{request.user.get_full_name()} is requesting ${amount} from you.\n\n"
                f"Reason: {description}\n\n"
                f"{'Due date: ' + due_date.strftime('%B %d, %Y') if due_date else ''}\n\n"
                f"Log in to ProfitsVibe.com to pay this request.",
                settings.EMAIL_HOST_USER,
                [payer_email],
                fail_silently=False,
            )

            messages.success(request, f"Money request for ${amount} sent to {payer_email}")
            return redirect('dashboard')
    else:
        form = RequestMoneyForm()

    return render(request, 'payments/request_money.html', {'form': form})


@login_required
def fund_wallet(request):
    """View for adding funds to user's wallet."""
    if request.method == 'POST':
        form = FundWalletForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']

            # In a real application, you would integrate with a payment processor
            # such as Stripe or PayPal here to process the actual payment

            # For demonstration purposes, we'll create a deposit transaction
            # and add the funds directly
            with db_transaction.atomic():
                # Create transaction record
                transaction = Transaction.objects.create(
                    sender=request.user,
                    amount=amount,
                    description=f"Wallet funding from {payment_method}",
                    transaction_type='deposit',
                    status='pending'
                )

                # Simulate payment processing
                # In a real app, this would happen after payment confirmation from the processor
                try:
                    # Add funds to wallet
                    request.user.wallet.deposit(amount)
                    transaction.status = 'completed'
                    transaction.save()

                    messages.success(request, f"Successfully added ${amount} to your wallet")
                    return redirect('dashboard')
                except ValueError as e:
                    transaction.status = 'failed'
                    transaction.save()
                    messages.error(request, str(e))
                    return redirect('fund_wallet')
    else:
        form = FundWalletForm(user=request.user)

    return render(request, 'payments/fund_wallet.html', {'form': form})


@login_required
def transaction_history(request):
    """View for displaying user's transaction history."""
    # Get all user transactions
    sent_transactions = Transaction.objects.filter(
        sender=request.user
    ).order_by('-created_at')

    received_transactions = Transaction.objects.filter(
        recipient=request.user
    ).order_by('-created_at')

    # Combine and sort by date
    all_transactions = list(sent_transactions) + list(received_transactions)
    all_transactions.sort(key=lambda x: x.created_at, reverse=True)

    return render(request, 'payments/transaction_history.html', {
        'transactions': all_transactions
    })


@login_required
def payment_requests(request):
    """View for managing payment requests."""
    # Get received requests
    received_requests = PaymentRequest.objects.filter(
        payer=request.user
    ).order_by('-created_at')

    # Get sent requests
    sent_requests = PaymentRequest.objects.filter(
        requester=request.user
    ).order_by('-created_at')

    return render(request, 'payments/payment_requests.html', {
        'received_requests': received_requests,
        'sent_requests': sent_requests
    })


@login_required
def pay_request(request, request_id):
    """View for paying a money request."""
    payment_request = get_object_or_404(
        PaymentRequest,
        request_id=request_id,
        payer=request.user,
        status='pending'
    )

    # Check if user has sufficient funds
    if not request.user.wallet.can_withdraw(payment_request.amount):
        messages.error(request, "Insufficient funds in your wallet.")
        return redirect('payment_requests')

    with db_transaction.atomic():
        # Create transaction
        transaction = Transaction.objects.create(
            sender=request.user,
            recipient=payment_request.requester,
            amount=payment_request.amount,
            description=f"Payment for request: {payment_request.description}",
            transaction_type='payment',
            status='pending'
        )

        try:
            # Process the payment
            request.user.wallet.withdraw(payment_request.amount)
            payment_request.requester.wallet.deposit(payment_request.amount)

            # Update transaction and request status
            transaction.status = 'completed'
            transaction.save()

            payment_request.mark_as_paid(transaction)

            # Send notification to requester
            send_mail(
                f"{request.user.get_full_name()} paid your request for ${payment_request.amount}",
                f"{request.user.get_full_name()} has paid your request for ${payment_request.amount}.\n\n"
                f"Reason: {payment_request.description}\n\n"
                f"The funds have been added to your ProfitsVibe wallet.",
                settings.EMAIL_HOST_USER,
                [payment_request.requester.email],
                fail_silently=False,
            )

            messages.success(
                request,
                f"You've successfully paid ${payment_request.amount} to {payment_request.requester.get_full_name()}"
            )
        except ValueError as e:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, str(e))

    return redirect('payment_requests')


@login_required
def decline_request(request, request_id):
    """View for declining a money request."""
    payment_request = get_object_or_404(
        PaymentRequest,
        request_id=request_id,
        payer=request.user,
        status='pending'
    )

    payment_request.mark_as_declined()

    # Notify the requester
    send_mail(
        f"{request.user.get_full_name()} declined your request for ${payment_request.amount}",
        f"{request.user.get_full_name()} has declined your request for ${payment_request.amount}.\n\n"
        f"Reason: {payment_request.description}",
        settings.EMAIL_HOST_USER,
        [payment_request.requester.email],
        fail_silently=False,
    )

    messages.success(request, "Payment request has been declined.")
    return redirect('payment_requests')


@login_required
def cancel_request(request, request_id):
    """View for cancelling a money request you've sent."""
    payment_request = get_object_or_404(
        PaymentRequest,
        request_id=request_id,
        requester=request.user,
        status='pending'
    )

    payment_request.status = 'cancelled'
    payment_request.save()

    # Notify the payer if they're a registered user
    if payment_request.payer:
        send_mail(
            f"{request.user.get_full_name()} cancelled their request for ${payment_request.amount}",
            f"{request.user.get_full_name()} has cancelled their request for ${payment_request.amount}.\n\n"
            f"Reason: {payment_request.description}",
            settings.EMAIL_HOST_USER,
            [payment_request.payer.email],
            fail_silently=False,
        )

    messages.success(request, "Your payment request has been cancelled.")
    return redirect('payment_requests')


@login_required
def withdraw_funds(request):
    """View for withdrawing funds to a bank account."""
    # This would be implemented with a form and bank account verification in a real app
    # For demonstration purposes, this is a simplified version
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        account_id = request.POST.get('account_id')

        # Check if user has sufficient funds
        if not request.user.wallet.can_withdraw(amount):
            messages.error(request, "Insufficient funds in your wallet.")
            return redirect('withdraw_funds')

        with db_transaction.atomic():
            # Create transaction record
            transaction = Transaction.objects.create(
                sender=request.user,
                amount=amount,
                description="Withdrawal to bank account",
                transaction_type='withdrawal',
                status='pending'
            )

            # In a real app, you would initiate an ACH transfer or similar
            # For demonstration, we'll just deduct from the wallet
            try:
                request.user.wallet.withdraw(amount)
                transaction.status = 'completed'
                transaction.save()

                messages.success(request, f"Withdrawal of ${amount} initiated. Funds should arrive in 1-3 business days.")
                return redirect('dashboard')
            except ValueError as e:
                transaction.status = 'failed'
                transaction.save()
                messages.error(request, str(e))
                return redirect('withdraw_funds')

    # Get user's bank accounts
    bank_accounts = request.user.payment_methods.filter(method_type='bank')

    return render(request, 'payments/withdraw_funds.html', {
        'bank_accounts': bank_accounts,
        'wallet': request.user.wallet
    })
