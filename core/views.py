import requests
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from .models import SavedTrail
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Local app models and forms
from bikes.models import Accessory, Bike, BikeCategory
from reviews.models import Review
from reservations.models import PromoCode, Reservation, Waiver
from payments.models import Payment
from .models import Trail
from .forms import AccessoryForm, AdminPromoCodeForm, AdminUserForm, ContactForm, WeatherZipForm


def home(request):
    """Homepage view with featured content."""
    # Get featured bikes (available bikes, limited to 6)
    featured_bikes = Bike.objects.filter(
        is_available=True,
        is_maintenance=False
    ).select_related('category')[:6]
    
    # Get featured reviews for carousel
    featured_reviews = Review.objects.filter(
        is_approved=True,
        is_featured=True
    ).select_related('user')[:6]
    
    # Get featured trails
    featured_trails = Trail.objects.filter(is_featured=True)[:3]
    
    # Get bike categories
    categories = BikeCategory.objects.all()
    
    # Get bike counts by category
    adult_count = Bike.objects.filter(category__slug='adult-bikes', is_available=True).count()
    kids_count = Bike.objects.filter(category__slug='kids-bikes', is_available=True).count()
    mountain_count = Bike.objects.filter(category__slug='mountain-bikes', is_available=True).count()
    tandem_count = Bike.objects.filter(category__slug='tandem-bikes', is_available=True).count()
    
    # Weather form
    weather_form = WeatherZipForm()
    
    context = {
        'featured_bikes': featured_bikes,
        'featured_reviews': featured_reviews,
        'featured_trails': featured_trails,
        'categories': categories,
        'weather_form': weather_form,
        'adult_count': adult_count,
        'kids_count': kids_count,
        'mountain_count': mountain_count,
        'tandem_count': tandem_count,
    }
    return render(request, 'core/home.html', context)


def about(request):
    """About page view."""
    return render(request, 'core/about.html')


def trails(request):
    """Trails listing page."""
    all_trails = Trail.objects.all()
    
    difficulty = request.GET.get('difficulty')
    distance = request.GET.get('distance')
    time = request.GET.get('time')
    location = request.GET.get('location')

    if difficulty:
        all_trails = all_trails.filter(difficulty=difficulty)

    if distance == 'short':
        all_trails = all_trails.filter(length_miles__lt=5)
    elif distance == 'medium':
        all_trails = all_trails.filter(length_miles__gte=5, length_miles__lte=8)
    elif distance == 'long':
        all_trails = all_trails.filter(length_miles__gt=8)

    if time == 'under_1':
        all_trails = all_trails.filter(estimated_minutes__lte=60)
    elif time == '1_2':
        all_trails = all_trails.filter(estimated_minutes__gt=60, estimated_minutes__lte=120)
    elif time == 'over_2':
        all_trails = all_trails.filter(estimated_minutes__gt=120)

    if location:
        all_trails = all_trails.filter(location_name=location)

    if request.user.is_authenticated:
        saved_trails = SavedTrail.objects.filter(user=request.user)
        saved_trail_ids = saved_trails.values_list('trail_id', flat=True)
    else:
        saved_trail_ids = []
        
    locations = (
        Trail.objects.exclude(location_name='')
        .order_by('location_name')
        .values_list('location_name', flat=True)
        .distinct()
    )
    
    context = {
        'trails': all_trails,
        'difficulty_choices': Trail.DIFFICULTY_LEVELS,
        'selected_difficulty': difficulty,
        'selected_distance': distance,
        'selected_time': time,
        'selected_location': location,
        'locations': locations,
        'saved_trail_ids': saved_trail_ids, 
    }
    return render(request, 'core/trails.html', context)


def contact(request):
    """Contact page with form."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Thank you for your inquiry! We will get back to you within 24 hours.'
            )
            return redirect('contact')
    else:
        form = ContactForm()
    
    context = {
        'form': form,
    }
    return render(request, 'core/contact.html', context)


@require_http_methods(['GET'])
def weather_api(request):
    """API endpoint to fetch weather data by ZIP code."""
    zip_code = request.GET.get('zip_code', '')
    
    if not zip_code:
        return JsonResponse({'error': 'ZIP code is required'}, status=400)
    
    api_key = settings.OPENWEATHER_API_KEY
    
    # If no API key is configured, return mock data for demo
    if not api_key:
        # Return mock weather data for demonstration
        return JsonResponse({
            'location': f'Indian Creek Area ({zip_code})',
            'temperature': 72,
            'feels_like': 74,
            'condition': 'Partly Cloudy',
            'description': 'Great conditions for biking!',
            'humidity': 65,
            'wind_speed': 8,
            'icon': '02d',
            'forecast_url': f'https://weather.com/weather/today/l/{zip_code}',
            'mock': True
        })
    
    try:
        # Call OpenWeather API
        url = f'https://api.openweathermap.org/data/2.5/weather'
        params = {
            'zip': f'{zip_code},us',
            'appid': api_key,
            'units': 'imperial'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            return JsonResponse(
                {'error': data.get('message', 'Failed to fetch weather data')},
                status=response.status_code
            )
        
        # Format weather data
        weather_data = {
            'location': data['name'],
            'temperature': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'condition': data['weather'][0]['main'],
            'description': data['weather'][0]['description'].title(),
            'humidity': data['main']['humidity'],
            'wind_speed': round(data['wind']['speed']),
            'icon': data['weather'][0]['icon'],
            'forecast_url': f'https://weather.com/weather/today/l/{zip_code}',
        }
        
        return JsonResponse(weather_data)
        
    except requests.RequestException as e:
        return JsonResponse(
            {'error': f'Failed to fetch weather data: {str(e)}'},
            status=500
        )


def handler404(request, exception):
    """Custom 404 handler."""
    return render(request, 'core/404.html', status=404)


def handler500(request):
    """Custom 500 handler."""
    return render(request, 'core/500.html', status=500)


######admin dashboard


User = get_user_model()


@staff_member_required
def admin_dashboard(request):
    recent_reservations = Reservation.objects.select_related("user", "bike").order_by("-created_at")[:8]
    total_reservations = Reservation.objects.count()
    active_reservations = Reservation.objects.filter(
        status__in=["pending", "confirmed", "paid", "active"]
    ).count()

    total_bikes = Bike.objects.count()
    available_bikes = Bike.objects.filter(
        is_available=True,
        is_maintenance=False
    ).count()
    maintenance_bikes = Bike.objects.filter(
        is_maintenance=True
    ).count()
    
    total_payments = Payment.objects.count()
    completed_payments = Payment.objects.filter(status__iexact="completed").count()

    total_reviews = Review.objects.count()
    pending_reviews = Review.objects.filter(is_approved=False).count()
    latest_reviews = Review.objects.select_related("user").order_by("-created_at")[:5]

    signed_waivers = Waiver.objects.count()
    unsigned_active_waivers = Reservation.objects.filter(
        status__in=["pending", "confirmed", "paid", "active"],
        waiver_signed=False,
    ).count()
    staff_count = User.objects.filter(is_staff=True).count()

    context = {
        "total_bikes": total_bikes,
        "available_bikes": available_bikes,
        "maintenance_bikes": maintenance_bikes,
        "total_reservations": total_reservations,
        "active_reservations": active_reservations,
        "total_payments": total_payments,
        "completed_payments": completed_payments,
        "total_reviews": total_reviews,
        "pending_reviews": pending_reviews,
        "recent_reservations": recent_reservations,
        "latest_reviews": latest_reviews,
        "signed_waivers": signed_waivers,
        "unsigned_active_waivers": unsigned_active_waivers,
        "staff_count": staff_count,
    }

    return render(request, "admin_dashboard/admin.html", context)

User = get_user_model()


@staff_member_required
def admin_staff(request):
    staff_members = User.objects.filter(is_staff=True).order_by(
        "-is_superuser",
        "-is_active",
        "last_name",
        "first_name",
        "username",
    )
    active_staff_count = staff_members.filter(is_active=True).count()
    superuser_count = staff_members.filter(is_superuser=True).count()

    return render(
        request,
        "admin_dashboard/admin_staff.html",
        {
            "staff_members": staff_members,
            "staff_count": staff_members.count(),
            "active_staff_count": active_staff_count,
            "superuser_count": superuser_count,
        },
    )


@staff_member_required
def admin_users(request):
    users = User.objects.annotate(
        reservation_count=Count("reservations", distinct=True),
        waiver_count=Count("waivers", distinct=True),
        payment_count=Count("reservations__payment", distinct=True),
        review_count=Count("reviews", distinct=True),
        account_type_order=Case(
            When(is_superuser=True, then=Value(1)),
            When(is_staff=True, then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        ),
    )

    total_users = users.count()
    customer_count = users.filter(is_staff=False).count()
    active_user_count = users.filter(is_active=True).count()

    sort = request.GET.get("sort", "joined")
    direction = request.GET.get("direction", "desc")
    if direction not in ["asc", "desc"]:
        direction = "desc"
    next_direction = "asc" if direction == "desc" else "desc"

    sort_options = {
        "name": ["last_name", "first_name", "username"],
        "username": ["username"],
        "account_type": ["account_type_order", "last_name", "first_name", "username"],
        "reservations": ["reservation_count", "last_name", "first_name", "username"],
        "waivers": ["waiver_count", "last_name", "first_name", "username"],
        "payments": ["payment_count", "last_name", "first_name", "username"],
        "reviews": ["review_count", "last_name", "first_name", "username"],
        "email": ["email", "last_name", "first_name", "username"],
        "phone": ["phone", "last_name", "first_name", "username"],
        "address": ["address", "city", "state", "zip_code", "last_name", "first_name", "username"],
        "emergency_contact": ["emergency_contact_name", "emergency_contact_phone", "last_name", "first_name", "username"],
        "active": ["is_active", "last_name", "first_name", "username"],
        "admin_notes": ["admin_notes", "last_name", "first_name", "username"],
        "last_active": ["last_login", "last_name", "first_name", "username"],
        "joined": ["date_joined"],
    }
    order_fields = sort_options.get(sort, sort_options["joined"])
    if direction == "desc":
        order_fields = [f"-{field}" for field in order_fields]
    users = users.order_by(*order_fields)

    return render(
        request,
        "admin_dashboard/admin_users.html",
        {
            "users": users,
            "total_users": total_users,
            "customer_count": customer_count,
            "active_user_count": active_user_count,
            "sort": sort,
            "direction": direction,
            "next_direction": next_direction,
        },
    )


@staff_member_required
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = AdminUserForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save()
            messages.success(request, f"{updated_user.get_full_name()} was updated.")
            return redirect("admin_users")
    else:
        form = AdminUserForm(instance=user)

    return render(
        request,
        "admin_dashboard/admin_user_form.html",
        {
            "form": form,
            "managed_user": user,
        },
    )


@staff_member_required
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, "You cannot delete or deactivate your own account from here.")
        return redirect("admin_users")

    has_history = (
        user.reservations.exists()
        or user.waivers.exists()
        or user.reviews.exists()
        or user.review_votes.exists()
        or user.is_staff
        or user.is_superuser
    )

    if has_history:
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.warning(
            request,
            f"{user.get_full_name()} has account history or staff access, so the account was deactivated instead of deleted.",
        )
        return redirect("admin_users")

    display_name = user.get_full_name()
    user.delete()
    messages.success(request, f"{display_name} was deleted.")
    return redirect("admin_users")


@staff_member_required
def admin_promos(request):
    now = timezone.now()
    promo_codes = PromoCode.objects.annotate(
        status_order=Case(
            When(
                Q(is_active=True)
                & Q(valid_from__lte=now)
                & Q(valid_until__gte=now)
                & (Q(max_uses__isnull=True) | Q(current_uses__lt=F("max_uses"))),
                then=Value(1),
            ),
            default=Value(2),
            output_field=IntegerField(),
        ),
        eligibility_order=Case(
            When(code__iexact="WELCOME20", then=Value(1)),
            When(code__iexact="WEEKEND15", then=Value(2)),
            When(code__iexact="TANDEM25", then=Value(3)),
            When(code__iexact="KIDSFREE", then=Value(4)),
            When(code__iexact="HAPPYBIRTHDAY", then=Value(5)),
            When(code__iexact="FAMILY10", then=Value(6)),
            When(code__iexact="SPRINGRIDE", then=Value(7)),
            When(code__iexact="SUNNYRIDE", then=Value(8)),
            When(code__iexact="SEASONSTART", then=Value(9)),
            When(code__iexact="EGGRIDE", then=Value(10)),
            When(code__iexact="WEEKDAYRIDE", then=Value(11)),
            When(code__iexact="RIDETOGETHER", then=Value(12)),
            default=Value(13),
            output_field=IntegerField(),
        )
    )
    active_promos = promo_codes.filter(is_active=True).count()
    expired_promos = sum(1 for promo in promo_codes if not promo.is_valid())
    total_uses = sum(promo.current_uses for promo in promo_codes)

    sort = request.GET.get("sort", "code")
    direction = request.GET.get("direction", "asc")
    if direction not in ["asc", "desc"]:
        direction = "asc"
    next_direction = "asc" if direction == "desc" else "desc"

    sort_options = {
        "code": ["code"],
        "status": ["status_order", "code"],
        "discount": ["discount_type", "discount_value", "code"],
        "minimum": ["minimum_order", "code"],
        "usage": ["current_uses", "code"],
        "description": ["description", "code"],
        "eligibility": ["eligibility_order", "code"],
        "valid_dates": ["valid_from", "valid_until", "code"],
    }
    order_fields = sort_options.get(sort, sort_options["code"])
    if direction == "desc":
        order_fields = [f"-{field}" for field in order_fields]
    promo_codes = promo_codes.order_by(*order_fields)

    return render(
        request,
        "admin_dashboard/admin_promos.html",
        {
            "promo_codes": promo_codes,
            "total_promos": promo_codes.count(),
            "active_promos": active_promos,
            "expired_promos": expired_promos,
            "total_uses": total_uses,
            "sort": sort,
            "direction": direction,
            "next_direction": next_direction,
        },
    )


@staff_member_required
def admin_add_promo(request):
    if request.method == "POST":
        form = AdminPromoCodeForm(request.POST)
        if form.is_valid():
            promo = form.save()
            messages.success(request, f"{promo.code} was added.")
            return redirect("admin_promos")
    else:
        form = AdminPromoCodeForm()

    return render(
        request,
        "admin_dashboard/admin_promo_form.html",
        {
            "form": form,
            "page_title": "Add Promo Code",
            "submit_label": "Add Promo Code",
        },
    )


@staff_member_required
def admin_edit_promo(request, promo_id):
    promo = get_object_or_404(PromoCode, id=promo_id)

    if request.method == "POST":
        form = AdminPromoCodeForm(request.POST, instance=promo)
        if form.is_valid():
            promo = form.save()
            messages.success(request, f"{promo.code} was updated.")
            return redirect("admin_promos")
    else:
        form = AdminPromoCodeForm(instance=promo)

    return render(
        request,
        "admin_dashboard/admin_promo_form.html",
        {
            "form": form,
            "promo": promo,
            "page_title": "Edit Promo Code",
            "submit_label": "Save Changes",
        },
    )


@staff_member_required
def toggle_promo_status(request, promo_id):
    promo = get_object_or_404(PromoCode, id=promo_id)
    promo.is_active = not promo.is_active
    promo.save(update_fields=["is_active"])

    messages.success(request, f"{promo.code} is now {'active' if promo.is_active else 'inactive'}.")
    return redirect("admin_promos")


@staff_member_required
@require_POST
def delete_promo(request, promo_id):
    promo = get_object_or_404(PromoCode, id=promo_id)
    code = promo.code

    if promo.current_uses > 0:
        promo.is_active = False
        promo.save(update_fields=["is_active"])
        messages.warning(request, f"{code} has usage history, so it was deactivated instead of deleted.")
        return redirect("admin_promos")

    promo.delete()
    messages.success(request, f"{code} was deleted.")
    return redirect("admin_promos")


@staff_member_required
def admin_bikes(request):
    # 1. Fetch every individual bike for the table rows
    bikes = Bike.objects.select_related("category", "size").order_by(
        "category__name", 
        "name", 
        "serial_number"
    )
    
    # 2. Generate the summary data for the top "Stats Cards"
    # This groups bikes by category and counts their status
    category_counts = Bike.objects.values('category__name').annotate(
        total=Count('id'),
        available=Count('id', filter=Q(is_available=True, is_maintenance=False)),
        maintenance=Count('id', filter=Q(is_maintenance=True))
    )

    # 3. Package both lists into the context dictionary
    context = {
        "bikes": bikes,
        "category_counts": category_counts,
    }
    
    # 4. Render the page
    return render(request, "admin_dashboard/admin_bikes.html", context)


@staff_member_required
def admin_accessories(request):
    accessories = Accessory.objects.order_by("category", "name")
    total_accessories = accessories.count()
    available_accessories = accessories.filter(is_available=True).count()
    low_stock_accessories = accessories.filter(quantity_in_stock__lte=3).count()

    context = {
        "accessories": accessories,
        "total_accessories": total_accessories,
        "available_accessories": available_accessories,
        "low_stock_accessories": low_stock_accessories,
    }
    return render(request, "admin_dashboard/admin_accessories.html", context)


@staff_member_required
def admin_add_accessory(request):
    if request.method == "POST":
        form = AccessoryForm(request.POST, request.FILES)
        if form.is_valid():
            accessory = form.save()
            messages.success(request, f"{accessory.name} was added.")
            return redirect("admin_accessories")
    else:
        form = AccessoryForm()

    return render(
        request,
        "admin_dashboard/admin_accessory_form.html",
        {
            "form": form,
            "page_title": "Add Accessory",
            "submit_label": "Add Accessory",
        },
    )


@staff_member_required
def admin_edit_accessory(request, accessory_id):
    accessory = get_object_or_404(Accessory, id=accessory_id)

    if request.method == "POST":
        form = AccessoryForm(request.POST, request.FILES, instance=accessory)
        if form.is_valid():
            accessory = form.save()
            messages.success(request, f"{accessory.name} was updated.")
            return redirect("admin_accessories")
    else:
        form = AccessoryForm(instance=accessory)

    return render(
        request,
        "admin_dashboard/admin_accessory_form.html",
        {
            "form": form,
            "accessory": accessory,
            "page_title": "Edit Accessory",
            "submit_label": "Save Changes",
        },
    )


@staff_member_required
@require_POST
def update_accessory_stock(request, accessory_id):
    accessory = get_object_or_404(Accessory, id=accessory_id)

    try:
        quantity = int(request.POST.get("quantity_in_stock", accessory.quantity_in_stock))
    except (TypeError, ValueError):
        messages.error(request, "Stock quantity must be a whole number.")
        return redirect("admin_accessories")

    if quantity < 0:
        messages.error(request, "Stock quantity cannot be negative.")
        return redirect("admin_accessories")

    accessory.quantity_in_stock = quantity
    accessory.save(update_fields=["quantity_in_stock"])
    messages.success(request, f"{accessory.name} stock updated to {quantity}.")
    return redirect("admin_accessories")


@staff_member_required
@require_POST
def delete_accessory(request, accessory_id):
    accessory = get_object_or_404(Accessory, id=accessory_id)
    accessory_name = accessory.name

    if accessory.reservation_accessories.exists():
        accessory.is_available = False
        accessory.save(update_fields=["is_available"])
        messages.warning(
            request,
            f"{accessory_name} has reservation history, so it was hidden instead of deleted.",
        )
        return redirect("admin_accessories")

    accessory.delete()
    messages.success(request, f"{accessory_name} was deleted.")
    return redirect("admin_accessories")


@staff_member_required
def toggle_accessory_availability(request, accessory_id):
    accessory = get_object_or_404(Accessory, id=accessory_id)
    accessory.is_available = not accessory.is_available
    accessory.save(update_fields=["is_available"])

    messages.success(request, f"{accessory.name} availability updated.")
    return redirect("admin_accessories")


@staff_member_required
def toggle_bike_availability(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)

    bike.is_available = not bike.is_available
    if not bike.is_available:
        bike.is_maintenance = False
    bike.save()

    messages.success(request, f"{bike.name} availability updated.")
    return redirect("admin_bikes")


@staff_member_required
def toggle_bike_maintenance(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)

    bike.is_maintenance = not bike.is_maintenance
    if bike.is_maintenance:
        bike.is_available = False
    bike.save()

    messages.success(request, f"{bike.name} maintenance status updated.")
    return redirect("admin_bikes")


@staff_member_required
def admin_reservations(request):
    reservations = Reservation.objects.select_related("user", "bike").order_by("-created_at")
    return render(request, "admin_dashboard/admin_reservations.html", {"reservations": reservations})


@staff_member_required
def update_reservation_status(request, reservation_id, new_status):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    allowed_statuses = ["pending", "confirmed", "paid", "completed", "cancelled"]
    if new_status in allowed_statuses:
        reservation.status = new_status
        reservation.save()
        messages.success(request, f"Reservation #{reservation.id} updated to {new_status}.")
    else:
        messages.error(request, "Invalid reservation status.")

    return redirect("admin_reservations")


@staff_member_required
def admin_reviews(request):
    reviews = Review.objects.select_related("user", "bike").order_by("-created_at")
    return render(request, "admin_dashboard/admin_reviews.html", {"reviews": reviews})


@staff_member_required
def approve_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = True
    review.save()
    messages.success(request, f"Review #{review.id} approved.")
    return redirect("admin_reviews")


@staff_member_required
def unapprove_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = False
    review.save()
    messages.success(request, f"Review #{review.id} marked unapproved.")
    return redirect("admin_reviews")


@staff_member_required
def admin_payments(request):
    payments = Payment.objects.select_related("reservation", "reservation__user", "reservation__bike").order_by("-created_at")
    return render(request, "admin_dashboard/admin_payments.html", {"payments": payments})

@staff_member_required
def refund_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    if payment.status == "completed":
        payment.status = "refunded"
        payment.save()
        messages.success(request, f"Payment #{payment.id} marked as refunded.")
    else:
        messages.error(request, f"Only completed payments can be refunded. Current status: {payment.status}")

    return redirect("admin_payments")


@staff_member_required
def void_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    if payment.status in ["pending", "processing"]:
        payment.status = "failed"
        payment.save()
        messages.success(request, f"Payment #{payment.id} was voided.")
    else:
        messages.error(request, f"Only pending or processing payments can be voided. Current status: {payment.status}")

    return redirect("admin_payments")

@staff_member_required
def admin_waivers(request):
    signed_waivers = Waiver.objects.select_related(
        "user",
        "reservation",
        "reservation__bike",
    ).order_by("-date_signed")
    unsigned_active_reservations = Reservation.objects.select_related(
        "user",
        "bike",
    ).filter(
        status__in=["pending", "confirmed", "paid", "active"],
        waiver_signed=False,
    ).order_by("rental_date", "created_at")

    return render(
        request,
        "admin_dashboard/signed_waivers.html",
        {
            "signed_waivers": signed_waivers,
            "unsigned_active_reservations": unsigned_active_reservations,
            "signed_waiver_count": signed_waivers.count(),
            "unsigned_active_waiver_count": unsigned_active_reservations.count(),
        },
    )

@login_required
def toggle_saved_trail(request, trail_id):
    trail = get_object_or_404(Trail, id=trail_id)

    saved, created = SavedTrail.objects.get_or_create(
        user=request.user,
        trail=trail
    )

    if not created:
        saved.delete()
        is_saved = False
    else:
        is_saved = True

    return JsonResponse({'saved': is_saved})


def trail_detail(request, id):
    trail = get_object_or_404(Trail, id=id)
    return render(request, 'trails/trail_detail.html', {
        'trail': trail
    })