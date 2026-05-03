# Recovery Cheat Sheet

This is the quick reset guide for the Indian Creek Cycles project.

## 1. `.env`

Real config file:

- `.env`

Template/reference:

- `.env.example`

### Local `.env`

```env
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
OPENWEATHER_API_KEY=your-openweather-api-key-here
SITE_URL=http://127.0.0.1:8000
DEFAULT_FROM_EMAIL=indiancreekcycles@gmail.com

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

### Host `.env`

```env
DEBUG=False
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,indiancreekcycles.com,www.indiancreekcycles.com,kgarci11.pythonanywhere.com
OPENWEATHER_API_KEY=your-openweather-api-key-here
SITE_URL=https://www.indiancreekcycles.com
DEFAULT_FROM_EMAIL=indiancreekcycles@gmail.com

EMAIL_BACKEND=django.core.mail.backends.dummy.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

### Backup `.env`

```bash
cp .env .env.backup
```

Restore:

```bash
cp .env.backup .env
```

## 2. `config/settings.py`

File:

- `config/settings.py`

Use this pattern:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host.strip()]
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000').rstrip('/')

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'rentals@indiancreekcycles.com')
```

Delete this if it exists later in the file:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## 3. Reservation form template

File:

- `templates/reservations/create_reservation.html`

Accessory quantity inputs should:

- default to `value="0"`
- use `min="0"`
- be `disabled`
- use `data-accessory-choice="{{ accessory.id_for_label }}"`

Example:

```html
<input
    type="number"
    name="rental_quantity_{{ accessory.data.value }}"
    value="0"
    min="0"
    class="accessory-quantity-input"
    data-accessory-choice="{{ accessory.id_for_label }}"
    disabled
>
```

JS behavior should be:

- checked => enable input, set to `1` if it was `0`
- unchecked => reset to `0` and disable input

## 4. Reservation view

File:

- `reservations/views.py`

### Accessory quantity logic

Correct:

```python
requested_quantities[accessory.id] = requested_quantities.get(accessory.id, 0) + quantity
```

Wrong:

```python
requested_quantities[quantity_key] = quantity
```

### Stock lookup

```python
stock_lookup = Accessory.objects.in_bulk(requested_quantities.keys())
for accessory_id, quantity in requested_quantities.items():
    accessory = stock_lookup.get(accessory_id)
```

### Waiver fallback

Only redirect if the reservation really exists:

```python
if reservation and reservation.pk and Reservation.objects.filter(pk=reservation.pk).exists():
```

## 5. Email is commented out for now

### `reservations/signals.py`

Keep the signal code, but comment out the actual send:

```python
# Email sending is temporarily disabled until live mail is configured.
# email.send(fail_silently=False)
```

### `reservations/views.py`

In `send_confirmation_email`:

```python
# Email sending is temporarily disabled until live mail is configured.
# email.send()
```

In `send_daily_reminders`:

```python
# Email sending is temporarily disabled until live mail is configured.
# email.send()
#
# res.reminder_sent = True
# res.save()
#
# count += 1
```

## 6. `reminder_sent`

File:

- `reservations/models.py`

Should include:

```python
reminder_sent = models.BooleanField(default=False)
```

Migration:

- `reservations/migrations/0013_reservation_reminder_sent.py`

If live errors with `no such column: reservations_reservation.reminder_sent`, run:

```bash
python manage.py migrate
```

## 7. Profile CSS leak fix

### `templates/base.html`

Do **not** load:

```html
<link rel="stylesheet" href="{% static 'css/profile.css' %}">
```

### `templates/accounts/profile.html`

Load it only on the profile page:

```django
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/profile.css' %}">
{% endblock %}
```

## 8. Reservation confirmation summary text

Files:

- `static/css/main.css`
- `static/css/reservations.css`

Keep this:

```css
.summary-header h2,
.summary-header .summary-label,
.summary-header .summary-id {
    color: white;
}
```

## 9. Bike detail recommended accessories

File:

- `templates/bikes/bike_detail.html`

Recommended Accessories should be a simple list, not fake clickable buttons.

Use:

```django
<ul class="feature-list">
    {% for accessory in accessories %}
    <li class="feature-item">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <span>
            {{ accessory.name }}
            <span style="color: #636e72; font-size: 0.9rem;">{{ accessory.display_price }}</span>
        </span>
    </li>
    {% endfor %}
</ul>
```

## 10. Footer quick links

File:

- `templates/base.html`

Quick Links should include:

- Browse Bikes
- Trails
- Accessories
- Ride Guide
- Reviews
- About
- Contact

Not account/admin-only links.

## 11. Deploy checklist

On the host:

```bash
git pull origin <branch>
source .venv/bin/activate
python manage.py migrate
python manage.py check
python manage.py collectstatic --noinput
```

Then reload the app in the PythonAnywhere Web tab.

## 12. Git workflow rule

Best practice:

- edit on your Mac
- commit on your Mac
- push from your Mac
- pull/deploy on the host

Avoid hand-editing app code on the host unless it is a true emergency.
