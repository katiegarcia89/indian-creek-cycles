import json
import os
from datetime import datetime, timedelta
from email.mime.image import MIMEImage

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Local app models and forms
from .models import Reservation, ReservationAccessory, Waiver, PromoCode
from .forms import ReservationForm, WaiverForm, PromoCodeForm, ReservationCancelForm
from bikes.models import Accessory, Bike
from payments.models import Payment
from locations.models import Location
from datetime import time


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
    """Create a new reservation and digitally station the bike at the dock."""
    bike = get_object_or_404(Bike, slug=bike_slug, is_available=True)

    if bike.is_maintenance:
        messages.error(request, 'This bike is currently under maintenance.')
        return redirect('bike_detail', slug=bike_slug)

    active_bookings = Reservation.objects.filter(
        bike=bike,
        status__in=['pending', 'confirmed', 'paid', 'active']
    ).exclude(status='cancelled')

    booked_dates = []
    for booking in active_bookings:
        current_date = booking.rental_date
        while current_date <= booking.return_date:
            booked_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
    
    booked_dates_json = json.dumps(booked_dates)

    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['rental_type'] = 'daily' 
        
        location_id = post_data.get('pickup_location')
        
        if not location_id:
            messages.error(request, "Please select a Smart-Dock location.")
            form = ReservationForm(post_data, bike=bike)
            return render(request, 'reservations/create_reservation.html', {
                'form': form, 'bike': bike, 'booked_dates_json': booked_dates_json
            })

        location = get_object_or_404(Location, id=location_id)
        
        if location.is_full:
            messages.error(request, f"{location.name} is currently at capacity.")
            form = ReservationForm(post_data, bike=bike)
            return render(request, 'reservations/create_reservation.html', {
                'form': form, 'bike': bike, 'booked_dates_json': booked_dates_json
            })

        form = ReservationForm(post_data, bike=bike)
        
        if form.is_valid():
            accessory_line_items, accessory_errors = _collect_accessory_items(form, post_data)
            if accessory_errors:
                for error in accessory_errors:
                    form.add_error(None, error)
                context = {
                    'form': form,
                    'bike': bike,
                    'booked_dates_json': booked_dates_json,
                }
                return render(request, 'reservations/create_reservation.html', context)

            try:
                with transaction.atomic():
                    reservation = form.save(commit=False)
                    reservation.user = request.user
                    reservation.bike = bike
                    reservation.pickup_location = location 
                    
                    rental_date = form.cleaned_data['rental_date']
                    return_date = form.cleaned_data['return_date']
                    
                    # Force it to 'daily' on the object too
                    reservation.rental_type = 'daily'
                    
                    days = (return_date - rental_date).days
                    reservation.rental_duration = max(1, days)

                    reservation.save()
                    
                    # --- ACCESSORY RENTAL / PURCHASE LOGIC ---
                    for item in accessory_line_items:
                        reservation.reservation_accessories.create(**item)
                    
                    reservation.calculate_prices()
                    reservation.save()
                    
                    # --- SMART-DOCK LOGIC ---
                    from django.utils import timezone
                    today = timezone.now().date()

                    if rental_date == today:
                        # Move the bike to the dock only if the rental starts TODAY
                        bike.location = location
                        bike.save()
                        
                        # Update the location count immediately
                        location.current_bikes = location.bikes.count()
                        location.save()
                        
                        msg = f'Reservation created for {bike.name}. It is waiting at {location.name}.'
                    else:
                        # Do NOT move the bike. Keep it in its current state (or set to None)
                        # so it doesn't take up a slot in the trailhead grid.
                        bike.location = None 
                        bike.save()
                        
                        msg = f'Reservation created for {bike.name} on {rental_date.strftime("%b %d")}.'

                    messages.success(request, msg)
                    return redirect('waiver', reservation_id=reservation.id)
                
            except Exception as e:
                messages.error(request, f"System error: {e}")
        else:
            context = {
                'form': form,
                'bike': bike,
                'booked_dates_json': booked_dates_json, 
            }
            return render(request, 'reservations/create_reservation.html', context)

    else:
        initial = {}
        if 'date' in request.GET:
            initial['rental_date'] = request.GET.get('date')
            initial['return_date'] = request.GET.get('date')
        form = ReservationForm(bike=bike, initial=initial)

    context = {
        'form': form,
        'bike': bike,
        'booked_dates_json': booked_dates_json, 
    }
    return render(request, 'reservations/create_reservation.html', context)


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
        user=request.user
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

    context = {
        'reservation': reservation,
        'payment': payment,
        'accessories': reservation.reservation_accessories.select_related('accessory').all(),
    }
    return render(request, 'reservations/reservation_confirmation.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time
from .models import Reservation, Location

def unlock_bike(request, pk):
    # 1. FETCH THE 'ANCHOR' RESERVATION (The one in the URL)
    try:
        # We use this to keep the page loaded even if search fails
        current_res = Reservation.objects.get(id=pk)
    except (Reservation.DoesNotExist, ValueError):
        # ONLY redirect if the URL itself is invalid
        messages.error(request, "Invalid page access.")
        return redirect('my_reservations')
    
    display_res = current_res
    error_msg = None

    # 2. HANDLE THE SEARCH (The ?search_id= part)
    search_id = request.GET.get('search_id')
    if search_id:
        try:
            searched_res = Reservation.objects.get(id=search_id)
            
            # Validation - If these fail, we do NOT redirect. 
            # We stay on the current page and set the error_msg.
            if searched_res.status == 'cancelled':
                error_msg = "Reservation cancelled."
            elif searched_res.status == 'completed':
                error_msg = f"Reservation #{search_id} is already completed."
            elif searched_res.user != request.user:
                error_msg = "Reservation does not exist." # Security: Don't tell them it belongs to someone else
            else:
                # SUCCESS: Only redirect if it's a valid, viewable reservation
                return redirect('unlock_bike', pk=searched_res.id)
        
        except (Reservation.DoesNotExist, ValueError):
            # FAIL: Stay right here on the current page (current_res)
            error_msg = "Reservation does not exist."

    # 3. Security Check for the Anchor
    if display_res.user != request.user:
        return redirect('my_reservations')

    # 4. Restored Logic for Timing & Stations
    now = timezone.localtime(timezone.now())
    opening_time = time(8, 0) 
    delivery_time = timezone.make_aware(
        datetime.combine(display_res.rental_date, opening_time)
    )
    is_early = now < delivery_time

    location = display_res.pickup_location or Location.objects.all().first()
    all_stations = list(Location.objects.filter(is_active=True).exclude(name__icontains="Hub").order_by('station_number'))
    
    try:
        current_idx = all_stations.index(location)
    except (ValueError, AttributeError):
        current_idx = 0
    sorted_locations = all_stations[current_idx:] + all_stations[:current_idx]

    context = {
        'reservation': display_res,
        'location': sorted_locations[0] if sorted_locations else None,
        'all_locations': sorted_locations[1:] if len(sorted_locations) > 1 else [],
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


def process_return(request, reservation_id):
    """
    Finalizes the reservation and docks the bike back at its location.
    """
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if reservation.status == 'completed':
        messages.info(request, "This return has already been processed.")
        return redirect('unlock_bike', pk=reservation.id)

    bike = reservation.bike
    return_location = reservation.pickup_location 
    
    # Dock the bike
    bike.status = 'available'
    bike.location = return_location 
    bike.is_available = True  
    bike.save()
    
    # Finalize Reservation
    reservation.status = 'completed'
    reservation.save()
    
    messages.success(request, f"Return Successful! {bike.name} is locked at {return_location.name}.")
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
    """
    Finds all confirmed reservations for tomorrow and sends a 
    branded HTML email with the specific background logo.
    """
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    reservations = Reservation.objects.filter(
        rental_date=tomorrow, 
        status__in=['confirmed', 'paid']
    )
    
    count = 0
    logo_path = r'C:\CIS264\IndianCreekCycle\indian-creek-cycles\indian-creek-cycles\static\images\logo\logo-email.png'

    for res in reservations:
        subject = f"Reminder: Your Ride Tomorrow at {res.pickup_location.name}"
        
        context = {
            'user': res.user,
            'reservation': res,
            'bike': res.bike,
            'request': request,
        }
        
        html_content = render_to_string('emails/reminder_email.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email='rentals@indiancreekcycles.com',
            to=[res.user.email],
        )
        
        email.attach_alternative(html_content, "text/html")
        email.mixed_subtype = 'related' 

        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                img = MIMEImage(logo_data)
                img.add_header('Content-ID', '<logo_image>')
                img.add_header('Content-Disposition', 'inline', filename='logo-email.png')
                email.attach(img)
        except FileNotFoundError:
            print(f"ERROR: Logo not found at: {logo_path}")

        email.send()
        count += 1
        
    if count > 0:
        messages.success(request, f"Successfully sent {count} reminder emails!")
    else:
        messages.info(request, "No confirmed rentals found for tomorrow.")

    return redirect('admin_reservations')


def help_page(request):

    return render(request, 'reservations/help.html')

