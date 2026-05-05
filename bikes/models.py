from django.db import models
from django.urls import reverse

class BikeCategory(models.Model):
    """Model for bike categories."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Bike Category'
        verbose_name_plural = 'Bike Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('bike_category', kwargs={'slug': self.slug})


class BikeSize(models.Model):
    """Model for bike sizes with descriptions using numerical standards."""
    size_inches = models.PositiveIntegerField(unique=True)
    description = models.TextField(help_text="Description of who this size fits")
    recommended_height = models.CharField(max_length=100, help_text="Recommended rider height range")
    recommended_age = models.CharField(max_length=100, blank=True, help_text="Recommended age range")
    
    class Meta:
        ordering = ['size_inches']
    
    def __str__(self):
        return f"{self.size_inches}\""


class Bike(models.Model):
    """Model for bikes in inventory."""
    BIKE_TYPES = [
        ('adult', 'Adult Bike'),
        ('kids', 'Kids Bike'),
        ('mountain', 'Mountain Bike'),
        ('tandem', 'Tandem Bike'),  
    ]

    STATUS_CHOICES = [
        ('maintenance', 'At Dock'), 
        ('in_use', 'On Trail'),     
        ('available', 'In Shop')    
    ]

    # Core identification
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    
    # --- INDIVIDUAL IDENTIFIER ---
    serial_number = models.CharField(
        max_length=50, 
        unique=True, 
        null=True, 
        blank=True, 
        help_text="Unique ID for this physical unit (e.g., ICC-101)"
    )

    category = models.ForeignKey(
        BikeCategory,
        on_delete=models.CASCADE,
        related_name='bikes'
    )
    bike_type = models.CharField(max_length=20, choices=BIKE_TYPES)
    size = models.ForeignKey(
        BikeSize,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bikes'
    )
    description = models.TextField()
    features = models.TextField(help_text="List key features, one per line")
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='bikes/', blank=True, null=True)
    
    is_available = models.BooleanField(default=True)
    is_maintenance = models.BooleanField(default=False, help_text="Bike is under maintenance")
    maintenance_note = models.TextField(blank=True, help_text="Reason for maintenance")
    
    location = models.ForeignKey(
        'locations.Location', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='bikes'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='available'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        if self.serial_number:
            return f"{self.name} [{self.serial_number}] ({self.size})"
        return f"{self.name} ({self.size})"
    
    def get_absolute_url(self):
        return reverse('bike_detail', kwargs={'slug': self.slug})
    
    # --- INDIVIDUAL AVAILABILITY LOGIC ---
    def get_available_quantity(self, date=None):
        """Returns 1 if this specific bike is available, 0 if not."""
        from reservations.models import Reservation
        import datetime

        # 1. PHYSICAL CHECK: If bike is disabled or under maintenance
        if not self.is_available or self.is_maintenance:
            return 0
        
        # 2. IMMEDIATE RENTAL CHECK: If someone wants it TODAY
        # If the bike is 'at_dock', it's not physically ready at the shop.
        current_date = datetime.date.today()
        if date == current_date and self.status == 'at_dock':
            return 0

        # 3. SCHEDULE CHECK: Look for future date conflicts
        if date:
            is_reserved = Reservation.objects.filter(
                bike=self,
                status__in=['pending', 'confirmed', 'paid', 'active'],
                # This checks if the requested date falls between the rental and return dates
                rental_date__lte=date,
                return_date__gte=date
            ).exists()
            
            return 0 if is_reserved else 1
            
        return 1
    
    def is_available_for_date(self, date):
        """Check if this specific bike is free for a specific date."""
        return self.get_available_quantity(date) > 0
    
    @property
    def is_in_stock(self):
        """Check if the physical unit is currently rent-ready."""
        return self.is_available and not self.is_maintenance
    
    @property
    def display_price(self):
        return f"${self.price_per_day}/day"
    
    @property
    def display_status(self):
        if self.location and "Hub" in self.location.name:
            return "In Shop"
        if self.status == 'in_use':
            return "On Trail"
        return "At Dock"
    
class Accessory(models.Model):
    """Model for bike accessories."""
    ACCESSORY_CATEGORIES = [
        ('safety', 'Safety'),
        ('comfort', 'Comfort'),
        ('storage', 'Storage'),
        ('electronics', 'Electronics'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00) 
    description = models.TextField()
    category = models.CharField(max_length=20, choices=ACCESSORY_CATEGORIES, default='other')
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='accessories/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_universal = models.BooleanField(
        default=False,
        help_text="Show this accessory for every bike reservation."
    )
    quantity_in_stock = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Accessory'
        verbose_name_plural = 'Accessories'
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def display_price(self):
        """Return formatted price."""
        if self.price_per_day:
            return f"${self.price_per_day}/day"
        return f"${self.price}"


class BikeAccessory(models.Model):
    """Model linking bikes with compatible accessories."""
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, related_name='compatible_accessories')
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE, related_name='compatible_bikes')
    is_recommended = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Bike Accessory'
        verbose_name_plural = 'Bike Accessories'
        unique_together = ['bike', 'accessory']
