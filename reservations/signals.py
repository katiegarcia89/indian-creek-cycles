from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from email.mime.image import MIMEImage
from .models import Reservation

@receiver(post_save, sender=Reservation)
def send_confirmation_on_save(sender, instance, created, **kwargs):
    if created:
        subject = f"Confirmation: Your Ride #{instance.id}"
        
        context = {
            'user': instance.user,
            'reservation': instance,
            'bike': instance.bike,
            'reservation_detail_url': f"{settings.SITE_URL}/reservations/detail/{instance.id}/",
        }
        
        html_content = render_to_string('emails/confirmation_email.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instance.user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.mixed_subtype = 'related'

        logo_path = settings.BASE_DIR / 'static' / 'images' / 'logo' / 'logo-email.png'
        
        try:
            with open(logo_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<logo_image>')
                img.add_header('Content-Disposition', 'inline', filename='logo-emails.png')
                email.attach(img)
        except FileNotFoundError:
            pass

        if instance.qr_code:
            try:
                with instance.qr_code.open('rb') as f:
                    qr_img = MIMEImage(f.read())
                    qr_img.add_header('Content-ID', '<reservation_qr>')
                    qr_img.add_header('Content-Disposition', 'inline', filename=f'reservation-qr-{instance.id}.png')
                    email.attach(qr_img)
            except FileNotFoundError:
                pass

        # Email sending is temporarily disabled until live mail is configured.
        # email.send(fail_silently=False)
