from bs4 import BeautifulSoup
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader


def send_template_mail(template_name, context, to_email,
                       from_email=settings.DEFAULT_FROM_EMAIL, fail_silently=False,
                       auth_user=None, auth_password=None, connection=None):

    html = loader.render_to_string(template_name, context)
    soup = BeautifulSoup(html, "html5lib")

    subject = soup.title.string.extract()
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    message = soup.get_text(strip=True).replace('\n\n', '\n')

    send_mail(subject, message, from_email, [to_email],
              fail_silently=fail_silently, auth_user=auth_user,
              auth_password=auth_password, html_message=html)
