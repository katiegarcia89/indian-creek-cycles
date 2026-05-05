# reservations/utils.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
import qrcode
from io import BytesIO
import base64

def send_confirmation_email(reservation):
    subject = f"Reservation Confirmed - {reservation.bike.name}"

    qr_url = f"{settings.SITE_URL}{reverse('unlock_bike', kwargs={'pk': reservation.id})}"

    qr = qrcode.make(qr_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'user': reservation.user,
        'reservation': reservation,
        'bike': reservation.bike,
        'reservation_detail_url': f"{settings.SITE_URL}/reservations/detail/{reservation.id}/",
        'qr_base64': qr_base64,
    }

    html_content = render_to_string('emails/confirmation_email.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()