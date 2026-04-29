import random
import string
import qrcode

from io import BytesIO
from decimal import Decimal
from datetime import timedelta
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.files import File
from bikes.models import Bike, Accessory
from locations.models import Location  
from django.utils import timezone

class ReservationAccessory(models.Model):
    """Through model for reservation accessories with rental or purchase intent."""
    FULFILLMENT_CHOICES = [
        ('rental', 'Rental'),
        ('purchase', 'Purchase'),
    ]

    reservation = models.ForeignKey(
        'Reservation', 
        on_delete=models.CASCADE, 
        related_name='reservation_accessories'
    )
    accessory = models.ForeignKey(
        Accessory, 
        on_delete=models.CASCADE, 
        related_name='reservation_accessories'
    )
    fulfillment_type = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES, default='rental')
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Reservation Accessory'
        verbose_name_plural = 'Reservation Accessories'
        unique_together = ['reservation', 'accessory', 'fulfillment_type']

    def __str__(self):
        return f"{self.quantity}x {self.accessory.name} ({self.get_fulfillment_type_display()}) for Reservation #{self.reservation.id}"

    def get_total(self):
        """Helper to get the cost of this line item."""
        price = self.price_at_time or Decimal('0.00')
        if self.fulfillment_type == 'rental' and self.reservation_id:
            duration = self.reservation.rental_duration or 1
            return price * self.quantity * duration
        return price * self.quantity

    def save(self, *args, **kwargs):
        if not self.price_at_time:
            if self.fulfillment_type == 'purchase':
                self.price_at_time = getattr(self.accessory, 'price', Decimal('0.00'))
            else:
                self.price_at_time = getattr(self.accessory, 'price_per_day', None) or Decimal('0.00')
        
        super().save(*args, **kwargs)
        
        if self.reservation:
            self.reservation.calculate_prices()
            self.reservation.save(update_fields=['accessories_price', 'subtotal', 'tax_amount', 'total_price'])

class Reservation(models.Model):
    """Model for bike reservations with Smart-Dock integration."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    RENTAL_TYPES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]

    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, related_name='reservations')
    pickup_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    
    # Security & Smart-Dock Fields
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    unlock_code = models.CharField(max_length=10, blank=True)
    
    # Rental Details
    rental_type = models.CharField(max_length=20, choices=RENTAL_TYPES, default='daily')
    rental_date = models.DateField()
    return_date = models.DateField()
    rental_duration = models.PositiveIntegerField(default=1, help_text="Duration in hours or days")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Pricing Fields
    bike_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    accessories_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Administrative & Legal
    waiver_signed = models.BooleanField(default=False)
    waiver_signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    special_requests = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reservation #{self.id} - {self.user.username} - {self.bike.name}"

    @property
    def duration_display(self):
        """Returns a formatted string for the duration (e.g., '3 Days')."""
        duration = self.rental_duration or 1
        unit = "Hour" if self.rental_type == 'hourly' else "Day"
        plural = "s" if duration > 1 else ""
        return f"{duration} {unit}{plural}"
    
    special_requests = models.TextField(blank=True, null=True, help_text="Customer requests from checkout.")
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for logistics/maintenance staff.")
    def calculate_prices(self):
            """Handles all the math for the reservation and its accessories."""
            if self.rental_type == 'hourly':
                rate = getattr(self.bike, 'price_per_hour', Decimal('0.00'))
                self.bike_price = rate * Decimal(str(self.rental_duration))
            else:
                # FIX IS HERE: Removing the +1 from the days calculation
                rate = getattr(self.bike, 'price_per_day', Decimal('0.00'))
                days = (self.return_date - self.rental_date).days 
                self.bike_price = rate * Decimal(str(max(1, days)))

            # Accessory math stays separate
            if self.pk:
                self.accessories_price = sum(
                    ra.get_total() for ra in self.reservation_accessories.all()
                )
            else:
                self.accessories_price = Decimal('0.00')

            # Totals
            self.subtotal = self.bike_price + self.accessories_price
            self.tax_amount = (self.subtotal * Decimal('0.07')).quantize(Decimal('0.01'))
            self.total_price = self.subtotal + self.tax_amount
            
    def generate_qr_code(self):
        """Generates a QR code pointing to the specific unlock URL for this reservation."""
        qr_url = f"{settings.SITE_URL}{reverse('unlock_bike', kwargs={'pk': self.id})}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        canvas = BytesIO()
        img.save(canvas, format='PNG')
        
        self.qr_code.save(f'qr_res_{self.id}.png', File(canvas), save=False)

    def save(self, *args, **kwargs):
        today = timezone.now().date()
        
        if self.rental_date < today - timedelta(days=1):
            pass 
            
        if not self.unlock_code:
            self.unlock_code = ''.join(random.choices(string.digits, k=6))
        
        self.calculate_prices()
        super().save(*args, **kwargs)

        # Generate QR code if it hasn't been created yet
        if not self.qr_code:
            self.generate_qr_code()
            # Update only the qr_code field to avoid re-running the whole save method
            super().save(update_fields=['qr_code'])
    
class Waiver(models.Model):
    """Model for rental waivers."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='waivers'
    )
    reservation = models.OneToOneField(
        'Reservation',  
        on_delete=models.CASCADE,
        related_name='waiver'
    )
    full_name = models.CharField(max_length=200)
    signature = models.CharField(max_length=200, help_text="Digital signature (typed name)")
    date_signed = models.DateTimeField(auto_now_add=True)
    acknowledged_risks = models.BooleanField(default=False)
    acknowledged_equipment = models.BooleanField(default=False)
    acknowledged_rules = models.BooleanField(default=False)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['-date_signed']

    def __str__(self):
        return f"Waiver for {self.full_name} - Reservation #{self.reservation.id}"


class PromoCode(models.Model):
    """Model for promotional codes."""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    current_uses = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-valid_from']

    def __str__(self):
        return self.code

    @property
    def discount_display(self):
        if self.code.upper() == 'HAPPYBIRTHDAY':
            return 'Free bike rental'
        if self.discount_type == 'percentage':
            return f'{self.discount_value}% off'
        return f'${self.discount_value} off'

    @property
    def rule_summary(self):
        rules = {
            'WELCOME20': 'First rental only.',
            'WEEKEND15': 'Rental must start or end on Saturday or Sunday.',
            'TANDEM25': 'Tandem bike rentals only.',
            'KIDSFREE': 'Kids bike rental with a child or youth helmet rental.',
            'HAPPYBIRTHDAY': 'Birthday month only. Discounts the bike rental, not accessories.',
            'SPRINGRIDE': 'Spring seasonal promo, valid March through May.',
            'SUNNYRIDE': 'Nice-weather campaign promo.',
            'SEASONSTART': 'Early season promo with limited redemptions.',
            'EGGRIDE': 'Short-term Easter spring event promo.',
            'WEEKDAYRIDE': 'Monday through Thursday rentals only.',
            'RIDETOGETHER': 'Requires at least 2 bikes.',
            'FAMILY10': 'Minimum order only.',
        }
        return rules.get(self.code.upper(), 'Standard minimum order, date, active status, and usage limit rules.')

    def is_valid(self):
        """Check if promo code is currently valid."""
        from django.utils import timezone
        now = timezone.now()

        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True

    def get_business_rule_error(self, reservation):
        """Return a customer-facing message when a code-specific rule is not met."""
        if not reservation:
            return None

        code = self.code.upper()
        bike = reservation.bike
        user = reservation.user

        if code == 'WELCOME20':
            previous_paid_rentals = user.reservations.exclude(id=reservation.id).filter(
                status__in=['paid', 'active', 'completed']
            ).exists()
            if previous_paid_rentals:
                return 'WELCOME20 is only available for your first rental.'

        if code == 'WEEKEND15':
            if reservation.rental_date.weekday() not in [5, 6] and reservation.return_date.weekday() not in [5, 6]:
                return 'WEEKEND15 is only available for rentals that start or end on Saturday or Sunday.'

        if code == 'TANDEM25':
            category_slug = getattr(getattr(bike, 'category', None), 'slug', '')
            if category_slug != 'tandem-bikes' and 'tandem' not in bike.name.lower():
                return 'TANDEM25 is only available for tandem bike rentals.'

        if code == 'KIDSFREE':
            category_slug = getattr(getattr(bike, 'category', None), 'slug', '')
            if category_slug != 'kids-bikes' and bike.bike_type != 'kids':
                return 'KIDSFREE is only available with a kids bike rental.'

            has_child_helmet = reservation.reservation_accessories.filter(
                accessory__name__in=['Helmet - Child', 'Helmet - Youth'],
                fulfillment_type='rental',
            ).exists()
            if not has_child_helmet:
                return 'KIDSFREE requires a child or youth helmet rental.'

        if code == 'HAPPYBIRTHDAY':
            birthday = getattr(user, 'date_of_birth', None)
            if not birthday:
                return 'Add your date of birth to use HAPPYBIRTHDAY.'

            if birthday.month != reservation.rental_date.month:
                return 'HAPPYBIRTHDAY is available during your birthday month.'

        if code == 'WEEKDAYRIDE':
            current_date = reservation.rental_date
            while current_date <= reservation.return_date:
                if current_date.weekday() > 3:
                    return 'WEEKDAYRIDE is only available for Monday through Thursday rentals.'
                current_date += timedelta(days=1)

        if code == 'RIDETOGETHER':
            bike_count = getattr(reservation, 'bike_count', 1)
            if bike_count < 2:
                return 'RIDETOGETHER requires at least 2 bikes.'

        return None

    def calculate_discount(self, subtotal, reservation=None):
        """Calculate discount amount."""
        subtotal = Decimal(subtotal)

        if subtotal < self.minimum_order:
            return Decimal('0.00')

        if reservation and self.get_business_rule_error(reservation):
            return Decimal('0.00')

        if self.code.upper() == 'HAPPYBIRTHDAY' and reservation:
            return min(reservation.bike_price, reservation.total_price).quantize(Decimal('0.01'))

        if self.discount_type == 'percentage':
            discount = subtotal * (self.discount_value / Decimal('100'))
        else:
            discount = min(self.discount_value, subtotal)

        return discount.quantize(Decimal('0.01'))
