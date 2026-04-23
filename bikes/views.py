from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count
from .models import Bike, BikeCategory, BikeSize, Accessory
from locations.models import Location 
from django.http import HttpResponse

def bike_list(request):
    """List all available bikes."""
    bikes = Bike.objects.filter(
        is_available=True, 
        is_maintenance=False
    ).select_related('category', 'size')
    
    category_slug = request.GET.get('category')
    if category_slug:
        bikes = bikes.filter(category__slug=category_slug)
    
    bike_type = request.GET.get('type')
    if bike_type:
        bikes = bikes.filter(bike_type=bike_type)
    
    size = request.GET.get('size')
    if size:
        bikes = bikes.filter(size__size_inches=size)
    
    search = request.GET.get('search')
    if search:
        bikes = bikes.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(features__icontains=search)
        )
    
    date_str = request.GET.get('date')
    if date_str:
        try:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            available_bikes = []
            for bike in bikes:
                if bike.is_available_for_date(check_date):
                    available_bikes.append(bike)
            bikes = available_bikes
        except ValueError:
            pass
    
    categories = BikeCategory.objects.filter(is_active=True)
    sizes = BikeSize.objects.all()
    
    context = {
        'bikes': bikes,
        'categories': categories,
        'sizes': sizes,
        'bike_types': Bike.BIKE_TYPES,
        'selected_category': category_slug,
        'selected_type': bike_type,
        'selected_size': size,
        'search_query': search,
        'check_date': date_str,
    }
    return render(request, 'bikes/bike_list.html', context)


def bike_detail(request, slug):
    """Bike detail view."""
    bike = get_object_or_404(
        Bike.objects.select_related('category', 'size'),
        slug=slug
    )
    
    accessories = Accessory.objects.filter(
        compatible_bikes__bike=bike,
        is_available=True
    )[:6]
    
    similar_bikes = Bike.objects.filter(
        category=bike.category,
        is_available=True
    ).exclude(id=bike.id)[:4]
    
    features = [f.strip() for f in bike.features.split('\n') if f.strip()]
    
    context = {
        'bike': bike,
        'accessories': accessories,
        'similar_bikes': similar_bikes,
        'features': features,
    }
    return render(request, 'bikes/bike_detail.html', context)

def kids_bikes(request):
    """View kids bikes."""
    bikes = Bike.objects.filter(
        bike_type='kids',
        is_available=True,
        is_maintenance=False
    ).select_related('category', 'size')
    
    context = {
        'bikes': bikes,
        'title': 'Kids Bikes',
        'description': 'Safe and fun bikes for young riders.',
    }
    return render(request, 'bikes/bike_type_list.html', context)

def bike_category(request, slug):
    """View bikes by category."""
    category = get_object_or_404(BikeCategory, slug=slug, is_active=True)
    bikes = Bike.objects.filter(
        category=category,
        is_available=True,
        is_maintenance=False
    ).select_related('size')
    
    context = {
        'category': category,
        'bikes': bikes,
    }
    return render(request, 'bikes/bike_list.html', context) 

# In bikes/views.py
def adult_bikes(request):  
    """View adult bikes."""
    bikes = Bike.objects.filter(
        bike_type='adult',
        is_available=True,
        is_maintenance=False
    ).select_related('category', 'size')
    
    context = {
        'bikes': bikes,
        'title': 'Adult Bikes',
        'description': 'Premium bikes for adult riders of all skill levels.',
    }
    return render(request, 'bikes/bike_type_list.html', context)


def kids_bikes(request):
    """View kids bikes."""
    bikes = Bike.objects.filter(
        bike_type='kids',
        is_available=True,
        is_maintenance=False  
    ).select_related('category', 'size')
    
    context = {
        'bikes': bikes,
        'title': 'Kids Bikes',
        'description': 'Safe and fun bikes for young riders.',
    }
    return render(request, 'bikes/bike_type_list.html', context)


def mountain_bikes(request):
    """View mountain bikes."""
    bikes = Bike.objects.filter(
        bike_type='mountain',
        is_available=True,
        is_maintenance=False  
    ).select_related('category', 'size')
    
    context = {
        'bikes': bikes,
        'title': 'Mountain Bikes',
        'description': 'Rugged bikes built for off-road adventures.',
    }
    return render(request, 'bikes/bike_type_list.html', context)

def add_accessory(request, accessory_id):
    # basic placeholder for now
    return HttpResponse(f"Accessory {accessory_id} added")

def accessories_list(request):
    """List all accessories."""
    accessories = Accessory.objects.filter(is_available=True)
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        accessories = accessories.filter(category=category)
    
    context = {
        'accessories': accessories,
        'categories': Accessory.ACCESSORY_CATEGORIES,
        'selected_category': category,
    }
    return render(request, 'bikes/accessories.html', context)


def bike_sizes_guide(request):
    """Bike sizing guide page."""
    sizes = BikeSize.objects.all()
    
    context = {
        'sizes': sizes,
    }
    return render(request, 'bikes/size_guide.html', context)


def admin_inventory_summary(request):
    # This counts how many of EACH SPECIFIC NAME you have
    inventory = Bike.objects.values('name', 'category__name', 'price_per_day').annotate(
        count=Count('id'),
        available=Count('id', filter=Q(is_available=True, is_maintenance=False)),
        needs_repair=Count('id', filter=Q(is_maintenance=True))
    ).order_by('category__name', 'name')

    return render(request, "admin_dashboard/inventory.html", {"inventory": inventory})


def fleet_dispatch(request):
    from locations.models import Location
    
    # Get EVERY active location so the driver can see the whole system status
    all_locations = Location.objects.filter(is_active=True).order_by('name')
    
    # Filter only those that physically have bikes for the task cards
    tasks = [l for l in all_locations if l.needs_pickup_dispatch]
    
    return render(request, 'admin_dashboard/fleet_dispatch.html', {
        'all_locations_list': all_locations,  # This fills the "Live Dock Status"
        'locations_needing_pickup': tasks     # This fills the "Active Pickup Tasks"
    })

def confirm_pickup(request, location_id):
    # Find the trailhead and the Hub
    trailhead = get_object_or_404(Location, id=location_id)
    hub = Location.objects.get(name__icontains="Hub") # Or "Main Shop"
    
    # Get all bikes currently at this trailhead
    bikes_to_move = Bike.objects.filter(location=trailhead)
    
    # Move them back to the Hub
    for bike in bikes_to_move:
        bike.location = hub
        bike.save()
        
    return redirect('fleet_dispatch')


# Add this to your bikes/views.py
def add_accessory(request, accessory_id):
    """Add an accessory to the session cart before the reservation is created."""
    # Ensure the accessory actually exists
    accessory = get_object_or_404(Accessory, id=accessory_id)
    
    # Simple session-based cart
    cart = request.session.get('accessory_cart', [])
    if accessory_id not in cart:
        cart.append(accessory_id)
        request.session['accessory_cart'] = cart
        
    # Redirect back to the accessories list page
    return redirect('accessories')


