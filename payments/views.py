from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from reservations.models import Reservation, PromoCode
from .models import Payment
from .forms import PaymentForm, SimulatedPaymentForm
from reservations.utils import send_confirmation_email

@login_required
def payment(request, reservation_id):
    """Payment processing view."""
    reservation = get_object_or_404(
        Reservation.objects.select_related('bike', 'user'),
        id=reservation_id,
        user=request.user
    )
    
    if hasattr(reservation, 'calculate_prices'):
        reservation.calculate_prices()
    
    # Check if already paid
    if reservation.status == 'paid':
        messages.info(request, 'This reservation has already been paid.')
        return redirect('reservation_confirmation', pk=reservation.id)
    
    # Check if waiver is signed
    if not reservation.waiver_signed:
        messages.warning(request, 'Please sign the waiver before proceeding to payment.')
        return redirect('waiver', reservation_id=reservation.id)
    
    # Get accessories for the template
    accessories = reservation.reservation_accessories.select_related('accessory').all()
    
    if request.method == 'POST':
        form = SimulatedPaymentForm(request.POST, reservation=reservation)
        if form.is_valid():
            with transaction.atomic():
                # Re-calculate inside the transaction to prevent any last-second changes
                if hasattr(reservation, 'calculate_prices'):
                    reservation.calculate_prices()

                payment_method = form.cleaned_data['payment_method']
                promo_code_str = form.cleaned_data.get('promo_code', '')
                purchase_items = reservation.reservation_accessories.select_related('accessory').filter(
                    fulfillment_type='purchase'
                )

                for item in purchase_items:
                    accessory = item.accessory
                    if item.quantity > accessory.quantity_in_stock:
                        messages.error(
                            request,
                            f'Only {accessory.quantity_in_stock} {accessory.name} available to purchase.'
                        )
                        return redirect('payment', reservation_id=reservation.id)
                
                # Calculate discount
                discount_amount = 0
                if promo_code_str:
                    try:
                        promo = PromoCode.objects.get(code=promo_code_str.upper(), is_active=True)
                        if promo.is_valid():
                            discount_amount = promo.calculate_discount(reservation.subtotal, reservation=reservation)
                            if discount_amount > 0:
                                promo.current_uses += 1
                                promo.save(update_fields=['current_uses'])
                    except PromoCode.DoesNotExist:
                        pass
                
                # Create payment record
                payment = Payment.objects.create(
                    reservation=reservation,
                    subtotal=reservation.subtotal,
                    tax_amount=reservation.tax_amount,
                    discount_amount=discount_amount,
                    total_amount=max(0, reservation.total_price - discount_amount), 
                    payment_method=payment_method,
                    status='completed',
                    card_last_four='4242',
                    card_brand='Visa',
                    promo_code=promo_code_str,
                    processed_at=timezone.now(),
                    notes='Simulated payment for demonstration purposes.'
                )

                for item in purchase_items:
                    accessory = item.accessory
                    accessory.quantity_in_stock -= item.quantity
                    if accessory.quantity_in_stock <= 0:
                        accessory.quantity_in_stock = 0
                        accessory.is_available = False
                    accessory.save(update_fields=['quantity_in_stock', 'is_available'])
                
                # Update reservation status
                reservation.status = 'paid'
                reservation.save()
                
                try:
                    send_confirmation_email(reservation)
                except Exception as e:
                    print(f"Email failed: {e}")
    
                messages.success(
                    request,
                    f'Payment successful! Your reservation is confirmed.'
                )
                return redirect('reservation_confirmation', pk=reservation.id)
    else:
        form = SimulatedPaymentForm(reservation=reservation)
    
    context = {
        'form': form,
        'reservation': reservation,
        'accessories': accessories,
        'bike': reservation.bike,
    }
    return render(request, 'payments/payment.html', context)

@login_required
def payment_confirmation(request, payment_id):
    """Payment confirmation/receipt view."""
    payment = get_object_or_404(
        Payment.objects.select_related('reservation', 'reservation__bike', 'reservation__user'),
        id=payment_id
    )
    
    # Ensure user owns this payment
    if payment.reservation.user != request.user:
        messages.error(request, 'You do not have permission to view this payment.')
        return redirect('home')
    
    context = {
        'payment': payment,
        'reservation': payment.reservation,
    }
    return render(request, 'payments/payment_confirmation.html', context)


@login_required
def payment_history(request):
    """View payment history."""
    payments = Payment.objects.filter(
        reservation__user=request.user
    ).select_related('reservation', 'reservation__bike').order_by('-created_at')
    
    context = {
        'payments': payments,
    }
    return render(request, 'payments/payment_history.html', context)


@login_required
def apply_promo_code(request, reservation_id):
    """Apply promo code to reservation."""
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        user=request.user
    )
    
    if request.method == 'POST':
        code = request.POST.get('promo_code', '').upper()
        
        try:
            promo = PromoCode.objects.get(code=code, is_active=True)
            if promo.is_valid():
                discount = promo.calculate_discount(reservation.subtotal)
                messages.success(
                    request,
                    f'Promo code applied! You saved ${discount:.2f}.'
                )
            else:
                messages.error(request, 'This promo code has expired or reached its limit.')
        except PromoCode.DoesNotExist:
            messages.error(request, 'Invalid promo code.')
    
    return redirect('payment', reservation_id=reservation_id)
