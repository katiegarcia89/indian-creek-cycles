import json
import os
import qrcode
import base64


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from io import BytesIO
from django.urls import reverse


# Local app models and forms
from .models import Reservation, ReservationAccessory, Waiver, PromoCode
from .forms import ReservationForm, WaiverForm, PromoCodeForm, ReservationCancelForm
from bikes.models import Accessory, Bike
from payments.models import Payment
from django.db.models import Count

from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, time
from locations.models import Location
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from django.utils import timezone
from reservations.models import Reservation

def _collect_accessory_items(form, post_data):
    """Build rental and purchase accessory line items from the reservation form."""
    line_items = []
    requested_quantities = {}
    errors = []

    field_map = [
        ('rental_accessories', 'rental', 'rental_quantity'),
        ('purchase_accessories', 'purchase', 'purchase_quantity'),
    ]

    for field_name, fulfillment_type, quantity_prefix in field_map:
        for accessory in form.cleaned_data.get(field_name, []):
            quantity_key = f'{quantity_prefix}_{accessory.id}'
            raw_quantity = post_data.get(quantity_key, '1')

            try:
                quantity = int(raw_quantity)
            except (TypeError, ValueError):
                errors.append(f'Quantity for {accessory.name} must be a whole number.')
                continue

            if quantity < 1:
                errors.append(f'Quantity for {accessory.name} must be at least 1.')
                continue

            unit_price = accessory.price if fulfillment_type == 'purchase' else (accessory.price_per_day or 0)
            if unit_price is None:
                errors.append(f'{accessory.name} does not have a valid {fulfillment_type} price.')
                continue

            requested_quantities[accessory.id] = requested_quantities.get(accessory.id, 0) + quantity
            line_items.append({
                'accessory': accessory,
                'fulfillment_type': fulfillment_type,
                'quantity': quantity,
                'price_at_time': unit_price,
            })

    if requested_quantities:
        stock_lookup = Accessory.objects.in_bulk(requested_quantities.keys())
        for accessory_id, quantity in requested_quantities.items():
            accessory = stock_lookup[accessory_id]
            if quantity > accessory.quantity_in_stock:
                errors.append(
                    f'Only {accessory.quantity_in_stock} {accessory.name} available.'
                )

    return line_items, errors


def check_availability(request):
    """AJAX endpoint to check bike availability for dates."""
    bike_id = request.GET.get('bike_id')
    date_str = request.GET.get('date')

    if not bike_id or not date_str:
        return JsonResponse({'error': 'Bike ID and date are required'}, status=400)

    try:
        bike = Bike.objects.get(id=bike_id)
        from datetime import datetime
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        available = bike.is_available_for_date(check_date)
        quantity = bike.get_available_quantity(check_date)

        return JsonResponse({
            'available': available,
            'quantity': quantity,
            'bike_name': bike.name
        })
    except Bike.DoesNotExist:
        return JsonResponse({'error': 'Bike not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

@login_required
def create_reservation(request, bike_slug):
    """Create a new reservation and block only dates already reserved for this bike."""

    bike = get_object_or_404(
        Bike,
        slug=bike_slug,
        is_maintenance=False
    )

    active_bookings = Reservation.objects.filter(
        bike=bike,
        status__in=['pending', 'confirmed', 'paid', 'active', 'completed']
    )

    booked_dates = []

    # Block today so users cannot reserve for the same day
    today = timezone.localtime(timezone.now()).date()
    booked_dates.append(today.strftime('%Y-%m-%d'))

    for booking in active_bookings:
        current_date = booking.rental_date

        while current_date <= booking.return_date:
            booked_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

    booked_dates_json = json.dumps(booked_dates)

    if request.method == 'POST':
        post_data = request.POST.copy()

        # Use the exact value your form/model expects.
        # If your choices use lowercase daily, keep this.
        post_data['rental_type'] = 'daily'

        location_id = post_data.get('pickup_location')

        if not location_id:
            messages.error(request, "Please select a Smart-Dock location.")
            form = ReservationForm(post_data, bike=bike)

            return render(request, 'reservations/create_reservation.html', {
                'form': form,
                'bike': bike,
                'booked_dates_json': booked_dates_json,
            })

        location = get_object_or_404(Location, id=location_id)

        if location.is_full:
            messages.error(request, f"{location.name} is currently at capacity.")
            form = ReservationForm(post_data, bike=bike)

            return render(request, 'reservations/create_reservation.html', {
                'form': form,
                'bike': bike,
                'booked_dates_json': booked_dates_json,
            })

        form = ReservationForm(post_data, bike=bike)

        if form.is_valid():
            rental_date = form.cleaned_data['rental_date']
            return_date = form.cleaned_data['return_date']

            overlapping_reservation = Reservation.objects.filter(
                bike=bike,
                status__in=['pending', 'confirmed', 'paid', 'active', 'completed'],
                rental_date__lte=return_date,
                return_date__gte=rental_date
            ).exists()

            if overlapping_reservation:
                messages.error(
                    request,
                    "This bike is already reserved for one or more of those dates."
                )

                return render(request, 'reservations/create_reservation.html', {
                    'form': form,
                    'bike': bike,
                    'booked_dates_json': booked_dates_json,
                })

            accessory_line_items, accessory_errors = _collect_accessory_items(form, post_data)

            if accessory_errors:
                for error in accessory_errors:
                    form.add_error(None, error)

                return render(request, 'reservations/create_reservation.html', {
                    'form': form,
                    'bike': bike,
                    'booked_dates_json': booked_dates_json,
                })

            try:
                with transaction.atomic():
                    reservation = form.save(commit=False)
                    reservation.user = request.user
                    reservation.bike = bike
                    reservation.pickup_location = location

                    reservation.rental_type = 'daily'
                    reservation.status = 'pending'

                    days = (return_date - rental_date).days
                    reservation.rental_duration = max(1, days)

                    reservation.save()

                    for item in accessory_line_items:
                        reservation.reservation_accessories.create(**item)

                    reservation.calculate_prices()
                    reservation.save()

                    messages.success(
                        request,
                        f'Reservation created for {bike.name} on {rental_date.strftime("%b %d")}.'
                    )

                    return redirect('waiver', reservation_id=reservation.id)

            except Exception as e:
                messages.error(request, f"System error: {e}")

        return render(request, 'reservations/create_reservation.html', {
            'form': form,
            'bike': bike,
            'booked_dates_json': booked_dates_json,
        })

    initial = {}

    if 'date' in request.GET:
        initial['rental_date'] = request.GET.get('date')
        initial['return_date'] = request.GET.get('date')

    form = ReservationForm(bike=bike, initial=initial)

    return render(request, 'reservations/create_reservation.html', {
        'form': form,
        'bike': bike,
        'booked_dates_json': booked_dates_json, 
    }
    return render(request, 'reservations/create_reservation.html', context)

def send_confirmation_email(reservation):
    logo_path = settings.BASE_DIR / 'static' / 'images' / 'logo' / 'logo-email.png'

    subject = f"Reservation Confirmed - {reservation.bike.name}"

    context = {
        'user': reservation.user,
        'reservation': reservation,
        'bike': reservation.bike,
    }

    html_content = render_to_string('emails/confirmation_email.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[reservation.user.email],
    )

    email.attach_alternative(html_content, "text/html")

    try:
        with open(logo_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<logo_image>')
            email.attach(img)
    except FileNotFoundError:
        print("Logo not found")

    # Email sending is temporarily disabled until live mail is configured.
    # email.send()
    # print(f"Reminder would send to {reservation.user.email} for {reservation.rental_date}")

    
@login_required
def waiver(request, reservation_id):
    """Waiver signing view."""
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if reservation.waiver_signed:
        messages.info(request, 'Waiver already signed. Proceeding to payment.')
        return redirect('payment', reservation_id=reservation.id)

    if request.method == 'POST':
        form = WaiverForm(request.POST)
        if form.is_valid():
            waiver_obj = form.save(commit=False)
            waiver_obj.user = request.user
            waiver_obj.reservation = reservation
            waiver_obj.save()

            # Update reservation status
            reservation.waiver_signed = True
            reservation.waiver_signed_at = timezone.now()
            reservation.save()

            messages.success(request, 'Waiver signed. Please proceed to payment.')
            return redirect('payment', reservation_id=reservation.id)
    else:
        initial = {
            'full_name': request.user.get_full_name(),
            'signature': request.user.get_full_name(),
            'emergency_contact_name': getattr(request.user, 'emergency_contact_name', ''),
            'emergency_contact_phone': getattr(request.user, 'emergency_contact_phone', ''),
        }
        form = WaiverForm(initial=initial)

    return render(request, 'reservations/waiver.html', {
        'form': form,
        'reservation': reservation,
        'bike': reservation.bike,
    })

@login_required
def reservation_detail(request, pk):
    """View reservation details."""
    reservation = get_object_or_404(
        Reservation.objects.select_related('bike', 'user'),
        pk=pk,
        user=request.user
    )

    context = {
        'reservation': reservation,
        'accessories': reservation.reservation_accessories.select_related('accessory').all(),
    }
    return render(request, 'reservations/reservation_detail.html', context)


@login_required
def my_reservations(request):
    """List all user reservations."""
    reservations = Reservation.objects.filter(
        user=request.user,
        status__in=['pending', 'confirmed', 'paid']
    ).select_related('bike').order_by('-created_at')

    context = {
        'reservations': reservations,
    }
    return render(request, 'reservations/my_reservations.html', context)


@login_required
def cancel_reservation(request, pk):
    """Cancel a reservation."""
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
        user=request.user
    )

    if reservation.status in ['completed', 'cancelled']:
        messages.error(request, 'This reservation cannot be cancelled.')
        return redirect('reservation_detail', pk=pk)

    if request.method == 'POST':
        form = ReservationCancelForm(request.POST)
        if form.is_valid():
            reservation.status = 'cancelled'
            reservation.admin_notes = form.cleaned_data.get('reason', '')
            reservation.save()

            messages.success(request, 'Your reservation has been cancelled.')
            return redirect('my_reservations')
    else:
        form = ReservationCancelForm()

    context = {
        'form': form,
        'reservation': reservation,
    }
    return render(request, 'reservations/cancel_reservation.html', context)


@login_required
def reservation_confirmation(request, pk):
    """Reservation confirmation page after payment."""
    reservation = get_object_or_404(
        Reservation.objects.select_related('bike', 'user'),
        pk=pk,
        user=request.user
    )

    try:
        payment = Payment.objects.get(reservation=reservation)
    except Payment.DoesNotExist:
        payment = None

    qr_url = f"{settings.SITE_URL}{reverse('unlock_bike', kwargs={'pk': reservation.id})}"
    print("EMAIL QR URL:", qr_url)
    context = {
        'reservation': reservation,
        'payment': payment,
        'accessories': reservation.reservation_accessories.select_related('accessory').all(),
        'qr_url': qr_url,
    }
    return render(request, 'reservations/reservation_confirmation.html', context)


@login_required
def unlock_bike(request, pk):
    try:
        reservation = Reservation.objects.select_related('bike', 'pickup_location').get(id=pk)
    except (Reservation.DoesNotExist, ValueError):
        messages.error(request, "Invalid page access.")
        return redirect('my_reservations')

    if reservation.user != request.user:
        return redirect('my_reservations')

    error_msg = None

    search_id = request.GET.get('search_id')
    if search_id:
        try:
            searched_res = Reservation.objects.get(id=search_id)

            if searched_res.status == 'cancelled':
                error_msg = "Reservation cancelled."
            elif searched_res.status == 'completed':
                error_msg = f"Reservation #{search_id} is already completed."
            elif searched_res.user != request.user:
                error_msg = "Reservation does not exist."
            else:
                return redirect('unlock_bike', pk=searched_res.id)

        except (Reservation.DoesNotExist, ValueError):
            error_msg = "Reservation does not exist."

    now = timezone.localtime(timezone.now())
    today = now.date()

    opening_time = time(8, 0)
    delivery_time = timezone.make_aware(
        datetime.combine(reservation.rental_date, opening_time)
    )
    is_early = now < delivery_time

    bike = reservation.bike
    pickup_location = reservation.pickup_location

    if pickup_location and "hub" in pickup_location.name.lower():
        messages.warning(
            request,
            "This reservation is for ICC Hub pickup. Smart Dock unlock is only available at dock locations."
        )
        return redirect('reservation_detail', pk=reservation.id)

    if reservation.status != 'active' and reservation.rental_date <= today:
        if bike.location != pickup_location:
            bike.location = pickup_location
            bike.status = 'available'
            bike.is_available = True
            bike.save()

    elif reservation.status == 'active':
        if bike.location is not None:
            bike.location = None
            bike.save()

    current_location = pickup_location

    all_locations = Location.objects.filter(
        is_active=True
    ).exclude(
        name__icontains="Hub"
    ).exclude(
        id=current_location.id if current_location else None
    ).order_by('station_number')

    context = {
        'reservation': reservation,
        'location': current_location,
        'all_locations': all_locations,
        'now': now,
        'is_early': is_early,
        'search_error': error_msg,
    }

    return render(request, 'reservations/unlock_interface.html', context)



def process_unlock(request, reservation_id):
    """
    Handles the actual database update when a user clicks 'Unlock'.
    Restores your original status checks and bike availability logic.
    """
    reservation = get_object_or_404(Reservation, id=reservation_id)
    today = timezone.now().date()
    
    # Check Status Compatibility
    if reservation.status not in ['booked', 'confirmed', 'paid']:
        if reservation.status == 'active':
            messages.info(request, "This rental is already active.")
        else:
            messages.warning(request, f"Current status ({reservation.status}) prevents unlock.")
        return redirect('unlock_bike', pk=reservation.id)

    # Check Date
    if reservation.rental_date > today:
        messages.warning(request, "It's too early for this reservation!")
        return redirect('unlock_bike', pk=reservation.id)

    # Update Bike Model
    bike = reservation.bike
    bike.status = 'in_use'
    bike.location = None 
    bike.is_available = False
    bike.save() 

    # Update Reservation Model
    reservation.status = 'active'
    reservation.save()

    messages.success(request, f"Bike {bike.name} unlocked! Enjoy your ride.")
    return redirect('unlock_bike', pk=reservation.id)


@login_required
def process_return(request, reservation_id):
    """
    Finalizes the rental return.
    Bike goes back to the trail dock, but it is NOT rentable yet.
    Dispatch must pick it up and return it to ICC Hub / In Shop before it becomes available again.
    """
    reservation = get_object_or_404(
        Reservation.objects.select_related('bike', 'pickup_location'),
        id=reservation_id,
        user=request.user
    )

    if reservation.status == 'completed':
        messages.info(request, "This return has already been processed.")
        return redirect('unlock_bike', pk=reservation.id)

    if reservation.status != 'active':
        messages.warning(request, "This bike can only be returned after it has been unlocked.")
        return redirect('unlock_bike', pk=reservation.id)

    bike = reservation.bike
    return_location = reservation.pickup_location

    if not return_location:
        messages.error(request, "Return failed: this reservation does not have a pickup dock.")
        return redirect('unlock_bike', pk=reservation.id)

    # Bike is physically back at the trail dock,
    # but it should NOT be rentable yet.
    bike.location = return_location
    bike.status = 'at_dock'
    bike.is_available = False
    bike.save()

    # Close the reservation
    reservation.status = 'completed'
    reservation.save()

    messages.success(
        request,
        f"Return successful! {bike.name} is locked at {return_location.name}. Dispatch pickup is required before it can be rented again."
    )

    return redirect('unlock_bike', pk=reservation.id)

def find_next_reservation(request):
    res_id = request.GET.get('res_id')
    if res_id:
        try:
            next_res = Reservation.objects.get(id=res_id, user=request.user)
           
            today = timezone.localtime(timezone.now()).date()
            yesterday = today - timedelta(days=1)
            
            if next_res.rental_date < yesterday:
                messages.error(request, f"Res #{res_id} was scheduled for {next_res.rental_date}, which has passed.")
                return redirect(request.META.get('HTTP_REFERER', '/'))
            
            if next_res.rental_date > today:
                 messages.error(request, f"Res #{res_id} is scheduled for {next_res.rental_date}. Please come back then!")
                 return redirect(request.META.get('HTTP_REFERER', '/'))

            return redirect('unlock_bike', pk=next_res.id)
            
        except Reservation.DoesNotExist:
            messages.error(request, "Reservation not found or belongs to another account.")
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


def confirm_pickup_location(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.method == "POST":
        location_id = request.POST.get('location_id')
        selected_location = get_object_or_404(Location, id=location_id)
        
        with transaction.atomic():
            reservation.pickup_location = selected_location
            reservation.save()
            
            bike = reservation.bike
            bike.location = selected_location
            bike.status = 'available' 
            bike.is_available = True 
            bike.save()
        
        return redirect('reservation_detail', pk=reservation.id)
    

def send_daily_reminders(request):

    today = timezone.now().date()

    reservations = Reservation.objects.filter(
        rental_date=today,
        status__in=['confirmed', 'paid'],
        reminder_sent=False
    )

    count = 0
    logo_path = settings.BASE_DIR / 'static' / 'images' / 'logo' / 'logo-email.png'

    for res in reservations:
        subject = f"Reminder: Your Ride Tomorrow at {res.pickup_location.name}"

        context = {
            'user': res.user,
            'reservation': res,
            'bike': res.bike,
        }

        html_content = render_to_string('emails/reminder_email.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[res.user.email],
        )

        email.attach_alternative(html_content, "text/html")

        try:
            with open(logo_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<logo_image>')
                email.attach(img)
        except FileNotFoundError:
            print("Logo not found")

        # Email sending is temporarily disabled until live mail is configured.
        # email.send()
        #
        # res.reminder_sent = True
        # res.save()
        #
        # count += 1

    return HttpResponse(f"Sent {count} reminder emails")


def help_page(request):
    locations = Location.objects.filter(is_active=True).order_by('station_number')

    return render(request, 'reservations/help.html', {
        'locations': locations
    })