from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from .tokens import account_activation_token

def send_activation_email(request, user):
    subject = 'Activate your account'
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_link = request.build_absolute_uri(f"/activate/{uid}/{token}/")

    message = render_to_string('users/activation_email.html', {
        'user': user,
        'activation_link': activation_link,
    })

    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.send()