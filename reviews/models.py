from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from reservations.models import Reservation


from bikes.models import Bike


class Review(models.Model):
    """Model for customer reviews."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    bike = models.ForeignKey(
        Bike,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True
    )
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='review',
        null=True,
        blank=True
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True)
    admin_response_date = models.DateTimeField(null=True, blank=True)
    
    # Helpful votes
    helpful_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.rating} stars - {self.title[:50]}"
    
    @property
    def rating_stars(self):
        """Return list of stars for template rendering."""
        return range(self.rating)
    
    @property
    def empty_stars(self):
        """Return list of empty stars."""
        return range(5 - self.rating)
    
    @property
    def rating_label(self):
        """Return text label for rating."""
        labels = {
            1: 'Poor',
            2: 'Fair',
            3: 'Good',
            4: 'Very Good',
            5: 'Excellent'
        }
        return labels.get(self.rating, '')


class ReviewImage(models.Model):
    """Model for review images."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='reviews/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Image for Review #{self.review.id}"


class ReviewHelpfulVote(models.Model):
    """Model for tracking helpful votes on reviews."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_votes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']
    
    def __str__(self):
        return f"{self.user.username} found Review #{self.review.id} helpful"
