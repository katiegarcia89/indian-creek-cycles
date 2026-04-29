from django.db import models
from django.conf import settings

class ContactInquiry(models.Model):
    """Model for contact/reservation inquiries."""
    INQUIRY_TYPES = [
        ('general', 'General Inquiry'),
        ('reservation', 'Reservation Inquiry'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPES, default='general')
    planned_date = models.DateField(null=True, blank=True)
    group_size = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Contact Inquiry'
        verbose_name_plural = 'Contact Inquiries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.inquiry_type} - {self.created_at.strftime('%Y-%m-%d')}"


class Trail(models.Model):
    """Model for bike trails."""
    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('difficult', 'Difficult'),
        ('expert', 'Expert'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    length_miles = models.DecimalField(max_digits=5, decimal_places=2)
    estimated_time = models.CharField(max_length=50, help_text="Estimated time to complete")
    estimated_minutes = models.PositiveIntegerField(default=90, help_text="Estimated time in minutes for filtering")
    location_name = models.CharField(max_length=200, blank=True, help_text="Trailhead, park, or neighborhood")
    address = models.CharField(max_length=255, blank=True, help_text="General location or street address")
    terrain = models.CharField(max_length=200, help_text="Type of terrain")
    highlights = models.TextField(help_text="Key highlights of the trail")
    image = models.ImageField(upload_to='trails/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SiteSetting(models.Model):
    """Model for site-wide settings."""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.key

class SavedTrail(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trail = models.ForeignKey('Trail', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trail')

    def __str__(self):
        return f"{self.user} saved {self.trail}"