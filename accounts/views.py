from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy

from reservations.models import Reservation
from reviews.models import Review
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from django.db.models import Sum
from core.models import SavedTrail

def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f'Welcome to Indian Creek Cycles, {user.first_name}! Your account has been created.'
            )
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'title': 'Create Account'
    }
    return render(request, 'accounts/register.html', context)


def user_login(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'home')
                messages.success(request, f'Welcome back, {user.first_name or username}!')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
        'title': 'Sign In'
    }
    return render(request, 'accounts/login.html', context)


@login_required
def user_logout(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile(request):
    """User profile view with reservations, reviews, and saved trails."""

    # Handle form submission FIRST
    if request.method == "POST":
        user_profile = request.user

        # Upload images
        if request.FILES.get('avatar'):
            user_profile.avatar = request.FILES['avatar']

        if request.FILES.get('cover_photo'):
            user_profile.cover_photo = request.FILES['cover_photo']
            
            
        user_profile.profile_quote = request.POST.get("profile_quote")

        user_profile.save()

        return redirect('profile')  # ✅ prevents resubmitting form

    # Reservations
    reservations = Reservation.objects.filter(
        user=request.user
    ).select_related('bike').order_by('-created_at')[:5]

    # Reviews
    recent_reviews = Review.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    reviews = Review.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Totals
    total_spent = Reservation.objects.filter(
        user=request.user
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    reservation_count = Reservation.objects.filter(user=request.user).count()
    review_count = Review.objects.filter(user=request.user).count()

    # Saved trails
    saved_trails = SavedTrail.objects.filter(
        user=request.user
    ).select_related('trail')

    context = {
        'reservations': reservations,
        'reviews': reviews,
        'recent_reviews': recent_reviews,
        'reservation_count': reservation_count,
        'review_count': review_count,
        'total_spent': total_spent,
        'saved_trails': saved_trails,
        'is_profile_page': True,
    }

    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile view."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'title': 'Edit Profile'
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def rate_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if request.method == "POST":
        rating = request.POST.get("rating")

        if rating:
            reservation.rating = int(rating)
            reservation.save()

    return redirect('profile') 