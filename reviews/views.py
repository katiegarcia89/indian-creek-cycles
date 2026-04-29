from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from bikes.models import Bike
from reservations.models import Reservation
from .models import Review, ReviewHelpfulVote
from .forms import ReviewForm, ReviewImageFormSet


def review_list(request):
    """List all approved reviews."""
    reviews = Review.objects.filter(is_approved=True).select_related('user', 'bike')
    
    # Filter by rating
    rating = request.GET.get('rating')
    if rating:
        reviews = reviews.filter(rating=rating)
    
    # Filter by bike
    bike_id = request.GET.get('bike')
    if bike_id:
        reviews = reviews.filter(bike_id=bike_id)
    
    # Sort
    sort = request.GET.get('sort', 'newest')
    if sort == 'newest':
        reviews = reviews.order_by('-created_at')
    elif sort == 'oldest':
        reviews = reviews.order_by('created_at')
    elif sort == 'highest':
        reviews = reviews.order_by('-rating')
    elif sort == 'lowest':
        reviews = reviews.order_by('rating')
    elif sort == 'helpful':
        reviews = reviews.order_by('-helpful_count')
    
    # Statistics
    stats = Review.objects.filter(is_approved=True).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    # Rating distribution
    rating_distribution = Review.objects.filter(is_approved=True).values('rating').annotate(
        count=Count('id')
    ).order_by('-rating')
    
    # Featured reviews
    featured_reviews = Review.objects.filter(
        is_approved=True,
        is_featured=True
    ).select_related('user')[:3]
    
    # All bikes for filter
    bikes = Bike.objects.filter(is_available=True)
    
    context = {
        'reviews': reviews,
        'stats': stats,
        'rating_distribution': rating_distribution,
        'featured_reviews': featured_reviews,
        'bikes': bikes,
        'selected_rating': rating,
        'selected_bike': bike_id,
        'sort': sort,
    }
    return render(request, 'reviews/review_list.html', context)


@login_required
def submit_review(request):
    bike_id = request.GET.get('bike')
    reservation_id = request.GET.get('reservation')

    bike = None
    reservation = None

    if reservation_id:
        reservation = get_object_or_404(
            Reservation,
            id=reservation_id,
            user=request.user
        )
        bike = reservation.bike

    elif bike_id:
        bike = get_object_or_404(Bike, id=bike_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        formset = ReviewImageFormSet(request.POST, request.FILES)

        # ✅ validate BOTH together
        if form.is_valid() and formset.is_valid():

            # prevent duplicate reviews
            if reservation and Review.objects.filter(
                reservation=reservation,
                user=request.user
            ).exists():
                messages.warning(request, "You already reviewed this ride.")
                return redirect('profile')

            review = form.save(commit=False)
            review.user = request.user

            # connect properly BEFORE saving
            if reservation:
                review.reservation = reservation
                review.bike = reservation.bike
            elif bike:
                review.bike = bike

            review.is_approved = False
            review.save()

            # attach images
            formset.instance = review
            formset.save()

            messages.success(request, "Review submitted!")
            return redirect('profile' if reservation else 'reviews')

    else:
        form = ReviewForm()
        formset = ReviewImageFormSet()

    return render(request, 'reviews/submit_review.html', {
        'form': form,
        'formset': formset,
        'bike': bike,
        'reservation': reservation,
    })
    
@login_required
def edit_review(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        formset = ReviewImageFormSet(request.POST, request.FILES, instance=review)

        if form.is_valid() and formset.is_valid():
            review = form.save(commit=False)

            review.user = request.user
            review.is_approved = False  # 🔥 force re-approval

            review.save()

            formset.instance = review
            formset.save()

            messages.success(
                request,
                "Your review was updated and is pending approval."
            )

            return redirect('profile' if review.reservation else 'reviews')

        else:
            messages.error(request, "Please fix the errors below.")

    else:
        form = ReviewForm(instance=review)
        formset = ReviewImageFormSet(instance=review)

    return render(request, 'reviews/submit_review.html', {
        'form': form,
        'formset': formset,
        'review': review,
    })


@login_required
def delete_review(request, pk):
    """Delete a review."""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    
    if request.method == 'POST':
        next_url = request.POST.get('next')  # 👈 get where to go next

        review.delete()
        messages.success(request, 'Your review has been deleted.')

        return redirect(next_url if next_url else 'reviews')  # 👈 smart redirect
    
    context = {
        'review': review,
    }
    return render(request, 'reviews/delete_review.html', context)


@login_required
@require_http_methods(['POST'])
def mark_helpful(request, pk):
    """Mark a review as helpful."""
    review = get_object_or_404(Review, pk=pk, is_approved=True)
    
    # Check if user already voted
    vote, created = ReviewHelpfulVote.objects.get_or_create(
        review=review,
        user=request.user
    )
    
    if created:
        review.helpful_count += 1
        review.save()
        return JsonResponse({
            'success': True,
            'helpful_count': review.helpful_count,
            'message': 'Thank you for your feedback!'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'You already marked this review as helpful.'
        })


def review_detail(request, pk):
    """View a single review."""
    review = get_object_or_404(
        Review.objects.select_related('user', 'bike'),
        pk=pk,
        is_approved=True
    )
    
    # Check if user has voted
    user_voted = False
    if request.user.is_authenticated:
        user_voted = ReviewHelpfulVote.objects.filter(
            review=review,
            user=request.user
        ).exists()
    
    context = {
        'review': review,
        'user_voted': user_voted,
    }
    return render(request, 'reviews/review_detail.html', context)
