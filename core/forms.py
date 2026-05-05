from django import forms
from django.contrib.auth import get_user_model
from bikes.models import Accessory
from reservations.models import PromoCode
from .models import ContactInquiry


User = get_user_model()


class ContactForm(forms.ModelForm):
    """Form for contact/reservation inquiries."""
    planned_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'inquiry_type', 'planned_date', 'group_size', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            'inquiry_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'group_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Number of riders'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Tell us about your inquiry...'
            }),
        }


class WeatherZipForm(forms.Form):
    """Form for weather ZIP code lookup."""
    zip_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ZIP code',
            'id': 'weather-zip-input'
        })
    )


class AccessoryForm(forms.ModelForm):
    """Form for admin accessory inventory management."""

    class Meta:
        model = Accessory
        fields = [
            'name',
            'description',
            'category',
            'price_per_day',
            'price',
            'quantity_in_stock',
            'image',
            'is_universal',
            'is_available',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Accessory name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe this accessory'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price_per_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'quantity_in_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'is_universal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class AdminPromoCodeForm(forms.ModelForm):
    """Form for managing promo code settings from the dashboard."""

    class Meta:
        model = PromoCode
        fields = [
            'code',
            'description',
            'discount_type',
            'discount_value',
            'minimum_order',
            'valid_from',
            'valid_until',
            'max_uses',
            'is_active',
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PROMOCODE'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What this promo is for'
            }),
            'discount_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'minimum_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'valid_until': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_uses': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_code(self):
        return self.cleaned_data['code'].upper()


class AdminUserForm(forms.ModelForm):
    """Form for staff-managed user profile and contact updates."""

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'is_active',
            'phone',
            'address',
            'city',
            'state',
            'zip_code',
            'date_of_birth',
            'emergency_contact_name',
            'emergency_contact_phone',
            'admin_notes',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Street address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ZIP code'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact phone'
            }),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Internal notes for staff only'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already registered to another account.')
        return email


class AdminStaffCreateForm(forms.ModelForm):
    """Simple staff-account form for the custom admin dashboard."""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'staff.email@example.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(555) 123-4567'
        })
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_superuser = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'phone',
            'is_active',
            'is_superuser',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


class AdminAccountCreateForm(forms.ModelForm):
    """Form for creating a regular user account from the admin dashboard."""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'customer.email@example.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(555) 123-4567'
        })
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'phone',
            'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
