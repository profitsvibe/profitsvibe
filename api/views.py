from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from decimal import Decimal

from payments.models import Transaction, PaymentRequest, TransactionFee
from accounts.models import Wallet
from .serializers import (UserProfileSerializer, WalletSerializer,
                          TransactionSerializer, PaymentRequestSerializer)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get the current user's profile."""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_wallet(request):
    """Get the current user's wallet."""
    wallet = request.user.wallet
    serializer = WalletSerializer(wallet)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transactions_list(request):
    """Get a list of the current user's transactions."""
    # Get transactions where user is sender or recipient
    sent = Transaction.objects.filter(sender=request.user)
    received = Transaction.objects.filter(recipient=request.user)

    # Combine and sort by date
    transactions = list(sent) + list(received)
    transactions.sort(key=lambda x: x.created_at, reverse=True)

    # Apply filters if provided
    transaction_type = request.query_params.get('type')
    if transaction_type:
        transactions = [t for t in transactions if t.transaction_type == transaction_type]

    status_filter = request.query_params.get('status')
    if status_filter:
        transactions = [t for t in transactions if t.status == status_filter]

    # Paginate results (simple implementation)
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    start = (page - 1) * page_size
    end = start + page_size

    paginated_transactions = transactions[start:end]
    serializer = TransactionSerializer(paginated_transactions, many=True)

    return Response({
        'count': len(transactions),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_detail(request, transaction_id):
    """Get details of a specific transaction."""
    # Only allow viewing transactions where the user is sender or recipient
    transaction = get_object_or_404(
        Transaction,
        transaction_id=transaction_id,
        sender=request.user
    ) if Transaction.objects.filter(transaction_id=transaction_id, sender=request.user).exists() else get_object_or_404(
        Transaction,
        transaction_id=transaction_id,
        recipient=request.user
    )

    serializer = TransactionSerializer(transaction)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_requests_list(request):
    """Get a list of the current user's payment requests."""
    # Get requests where user is requester or payer
    sent = PaymentRequest.objects.filter(requester=request.user)
    received = PaymentRequest.objects.filter(payer=request.user)

    # Apply filters if provided
    request_type = request.query_params.get('type')
    if request_type == 'sent':
        requests = sent
    elif request_type == 'received':
        requests = received
    else:
        # Combine and sort by date
        requests = list(sent) + list(received)
        requests.sort(key=lambda x: x.created_at, reverse=True)

    status_filter = request.query_params.get('status')
    if status_filter:
        requests = [r for r in requests if r.status == status_filter]

    # Paginate results (simple implementation)
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    start = (page - 1) * page_size
    end = start + page_size

    paginated_requests = requests[start:end]
    serializer = PaymentRequestSerializer(paginated_requests, many=True)

    return Response({
        'count': len(requests),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_request_detail(request, request_id):
    """Get details of a specific payment request."""
    # Only allow viewing requests where the user is requester or payer
    payment_request = get_object_or_404(
        PaymentRequest,
        request_id=request_id,
        requester=request.user
    ) if PaymentRequest.objects.filter(request_id=request_id, requester=request.user).exists() else get_object_or_404(
        PaymentRequest,
        request_id=request_id,
        payer=request.user
    )

    serializer = PaymentRequestSerializer(payment_request)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_money(request):
    """API endpoint for sending money to another user."""
    recipient_email = request.data.get('recipient_email')
    amount = Decimal(request.data.get('amount', '0'))
    description = request.data.get('description', '')

    # Validate input
    if not recipient_email:
        return Response({'error': 'Recipient email is required'}, status=status.HTTP_400_BAD_REQUEST)

    if amount <= 0:
        return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user has sufficient funds
    sender_wallet = request.user.wallet
    if not sender_wallet.can_withdraw(amount):
        return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)

    # Find recipient by email (if they exist in our system)
    try:
        recipient = User.objects.get(email=recipient_email)
        recipient_exists = True
    except User.DoesNotExist:
        recipient = None
        recipient_exists = False

    # Check if sender is trying to send money to themselves
    if recipient_exists and recipient.id == request.user.id:
        return Response({'error': 'Cannot send money to yourself'}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate transaction fee (example: 2% for simplicity)
    fee_percentage = Decimal('0.02')
    fee_amount = amount * fee_percentage
    net_amount = amount - fee_amount

    with transaction.atomic():
        # Create transaction
        transaction_obj = Transaction.objects.create(
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
            transaction=transaction_obj,
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
                transaction_obj.status = 'completed'
            else:
                # For non-registered users, we'll mark as completed and send an email with a claim link
                transaction_obj.status = 'completed'

                # Email logic would be implemented here in a real system

            transaction_obj.save()

            serializer = TransactionSerializer(transaction_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            transaction_obj.status = 'failed'
            transaction_obj.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_money(request):
    """API endpoint for requesting money from another user."""
    payer_email = request.data.get('payer_email')
    amount = Decimal(request.data.get('amount', '0'))
    description = request.data.get('description', '')
    due_date = request.data.get('due_date')

    # Validate input
    if not payer_email:
        return Response({'error': 'Payer email is required'}, status=status.HTTP_400_BAD_REQUEST)

    if amount <= 0:
        return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if payer exists in our system
    try:
        payer = User.objects.get(email=payer_email)
        payer_exists = True
    except User.DoesNotExist:
        payer = None
        payer_exists = False

    # Check if requester is trying to request money from themselves
    if payer_exists and payer.id == request.user.id:
        return Response({'error': 'Cannot request money from yourself'}, status=status.HTTP_400_BAD_REQUEST)

    # Create payment request
    payment_request = PaymentRequest.objects.create(
        requester=request.user,
        payer=payer if payer_exists else None,
        payer_email=payer_email,
        amount=amount,
        description=description,
        due_date=due_date,
        status='pending'
    )

    # Email notification would be sent here in a real system

    serializer = PaymentRequestSerializer(payment_request)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_request(request, request_id):
    """API endpoint for paying a money request."""
    payment_request = get_object_or_404(
        PaymentRequest,
        request_id=request_id,
        payer=request.user,
        status='pending'
    )

    # Check if user has sufficient funds
    if not request.user.wallet.can_withdraw(payment_request.amount):
        return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # Create transaction
        transaction_obj = Transaction.objects.create(
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
            transaction_obj.status = 'completed'
            transaction_obj.save()

            payment_request.mark_as_paid(transaction_obj)

            # Email notification would be sent here in a real system

            serializer = TransactionSerializer(transaction_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            transaction_obj.status = 'failed'
            transaction_obj.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fund_wallet(request):
    """API endpoint for adding funds to user's wallet."""
    amount = Decimal(request.data.get('amount', '0'))
    payment_method_id = request.data.get('payment_method_id')

    # Validate input
    if amount <= 0:
        return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    # In a real app, payment processing would happen here

    # For demonstration, we'll just add the funds directly
    with transaction.atomic():
        # Create transaction record
        transaction_obj = Transaction.objects.create(
            sender=request.user,
            amount=amount,
            description=f"Wallet funding",
            transaction_type='deposit',
            status='pending'
        )

        try:
            # Add funds to wallet
            request.user.wallet.deposit(amount)
            transaction_obj.status = 'completed'
            transaction_obj.save()

            serializer = TransactionSerializer(transaction_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            transaction_obj.status = 'failed'
            transaction_obj.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_funds(request):
    """API endpoint for withdrawing funds to a bank account."""
    amount = Decimal(request.data.get('amount', '0'))
    bank_account_id = request.data.get('bank_account_id')

    # Validate input
    if amount <= 0:
        return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user has sufficient funds
    if not request.user.wallet.can_withdraw(amount):
        return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)

    # In a real app, bank transfer processing would happen here

    # For demonstration, we'll just deduct from the wallet
    with transaction.atomic():
        # Create transaction record
        transaction_obj = Transaction.objects.create(
            sender=request.user,
            amount=amount,
            description="Withdrawal to bank account",
            transaction_type='withdrawal',
            status='pending'
        )

        try:
            # Deduct from wallet
            request.user.wallet.withdraw(amount)
            transaction_obj.status = 'completed'
            transaction_obj.save()

            serializer = TransactionSerializer(transaction_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            transaction_obj.status = 'failed'
            transaction_obj.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
