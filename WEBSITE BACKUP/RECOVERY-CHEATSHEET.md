# Indian Creek Cycles Recovery Cheat Sheet

This is the practical reset guide for getting the project back into a working state.

Use this in order.

## 1. Log In First

### PythonAnywhere

- Hosting site: PythonAnywhere
- Username: `katie.garcia.c@gmail.com`
- Password: `indiancreeyckcyles123`

### Project Gmail

- Email: `indiancreekrentals@gmail.com`
- Password: `indiancreekcycles123`

## 2. Open the Right Place in PythonAnywhere

1. Log into PythonAnywhere.
2. From the top navigation, click `Consoles`.
3. Open a `Bash` console.
4. In the Bash console, go to the project:

```bash
cd ~/indian-creek-cycles
```

5. Check what branch you are on:

```bash
git branch --show-current
```

Important:

- Do not experiment in the live host repo unless you mean to affect the live site.
- The PythonAnywhere repo folder is the same folder the live site is using.

## 3. Update the Live Website from the Bash Console

From the PythonAnywhere Bash console:

```bash
cd ~/indian-creek-cycles
git branch --show-current
git pull origin <branch-name>
source .venv/bin/activate
python manage.py migrate
python manage.py check
python manage.py collectstatic --noinput
touch /var/www/www_indiancreekcycles_com_wsgi.py
```

That last command reloads the live site from the console.

If you prefer the website UI instead:

1. Click the `Web` tab in PythonAnywhere.
2. Find the web app.
3. Click `Reload`.

If the site is still wrong after this, check the error log:

```bash
tail -n 80 /var/log/www.indiancreekcycles.com.error.log
```

To watch new errors live:

```bash
tail -f /var/log/www.indiancreekcycles.com.error.log
```

Stop the live tail with:

```bash
Ctrl + C
```

## 4. Local Backups

A backup folder exists here:

- `WEBSITE BACKUP/`

It currently contains copies of:

- `WEBSITE BACKUP/db.sqlite3`
- `WEBSITE BACKUP/media/`
- `WEBSITE BACKUP/static/`

If you need to rebuild it again later:

```bash
mkdir -p backup
cp -R media backup/media
cp -R static backup/static
cp db.sqlite3 backup/db.sqlite3
```

## 5. Fix the Local `.env`

Real config file:

- `.env`

Template/reference:

- `.env.example`

From your local terminal:

```bash
cd "/Users/katiegarcia/Desktop/new project 4-16/indian-creek-cycles"
nano .env
```

Paste this for the local version:

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

Save and exit `nano`:

1. `Ctrl + O`
2. `Enter`
3. `Ctrl + X`

## 6. Fix the Host `.env`

From the PythonAnywhere Bash console:

```bash
cd ~/indian-creek-cycles
nano .env
```

Paste this for the host version:

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

Save and exit `nano`:

1. `Ctrl + O`
2. `Enter`
3. `Ctrl + X`

## 7. Fix `config/settings.py`

From the terminal in the project root:

```bash
nano config/settings.py
```

Use this env-loading pattern:

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

Delete this line if it appears later in the file:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Save and exit `nano`:

1. `Ctrl + O`
2. `Enter`
3. `Ctrl + X`

## 8. Check the App After `.env` or Settings Changes

Local:

```bash
source .venv/bin/activate
python manage.py check
python manage.py runserver
```

Host:

```bash
source .venv/bin/activate
python manage.py check
python manage.py collectstatic --noinput
```

Then reload the app from the PythonAnywhere `Web` tab.

## 9. Reservation Form Fix

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

- checked => enable input and set to `1` if it was `0`
- unchecked => reset to `0` and disable input

## 10. Reservation View Fix

File:

- `reservations/views.py`

Correct accessory quantity logic:

```python
requested_quantities[accessory.id] = requested_quantities.get(accessory.id, 0) + quantity
```

Wrong:

```python
requested_quantities[quantity_key] = quantity
```

Stock lookup should be:

```python
stock_lookup = Accessory.objects.in_bulk(requested_quantities.keys())
for accessory_id, quantity in requested_quantities.items():
    accessory = stock_lookup.get(accessory_id)
```

Waiver fallback should only redirect if the reservation really exists:

```python
if reservation and reservation.pk and Reservation.objects.filter(pk=reservation.pk).exists():
```

## 11. Email is Commented Out for Now

Email sending is intentionally disabled until live email is configured.

### `reservations/signals.py`

Keep the signal code, but comment out the send:

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

## 12. `reminder_sent` Migration

File:

- `reservations/models.py`

Should include:

```python
reminder_sent = models.BooleanField(default=False)
```

Migration:

- `reservations/migrations/0013_reservation_reminder_sent.py`

If live errors with:

```text
no such column: reservations_reservation.reminder_sent
```

run:

```bash
python manage.py migrate
```

## 13. Profile CSS Leak Fix

### `templates/base.html`

Do not load profile CSS globally:

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

## 14. Contact Page FAQ Answers

File:

- `templates/core/contact.html`

The FAQ answers should exist directly in the markup as regular paragraphs.

If they are hidden, check that `help.css` is not being loaded globally from `templates/base.html`.

`help.css` should only be loaded on:

- `templates/reservations/help.html`

## 15. About Page Content

File:

- `templates/core/about.html`

Should include:

- family biking image from `static/images/hero/family-biking-hero.jpg`
- original fictional Indian Creek team
- Website Project Team section with real contributors

## 16. Profile Email Draft Link

Files:

- `accounts/views.py`
- `templates/accounts/profile.html`

The profile email link should open a Gmail compose draft in a new tab with:

- recipient = the customer
- subject = `Indian Creek Cycles Reservation Follow-Up`
- body = prefilled support message
- Gmail account hint = `indiancreekcycles@gmail.com`

## 17. Admin Review Comments

Files:

- `core/views.py`
- `core/urls.py`
- `reviews/forms.py`
- `templates/admin_dashboard/admin_reviews.html`
- `templates/admin_dashboard/admin_review_comment.html`
- `templates/reviews/review_list.html`

Feature behavior:

- green `Comment` button if no admin comment exists
- red `Edit Comment` button if a comment already exists
- admin can revise the comment later
- public review list shows the admin response below the review

## 18. Unsigned Waivers Admin Tools

Files:

- `core/views.py`
- `templates/admin_dashboard/signed_waivers.html`

Expected behavior:

- show urgency labels like `Overdue`, `Due Today`, `Due Soon`, `Upcoming`
- include `Copy Waiver Link`
- include `View Customer`

## 19. Helpful Button / Review Card Layout

Files:

- `templates/reviews/review_list.html`
- `static/css/main.css`

Expected behavior:

- `Helpful` button belongs to the specific review card
- it should sit in the review header area, not float ambiguously between reviews

## 20. Local Workflow Rule

Best workflow:

1. Edit code on your Mac.
2. Commit and push from your Mac.
3. On PythonAnywhere, only:
   - pull
   - migrate
   - check
   - collectstatic
   - reload

Try not to do experimental branch work directly in the live PythonAnywhere repo.
