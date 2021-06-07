from django.core.mail import EmailMultiAlternatives


def send_mail_with_attachments(
        subject, from_email, recipient_list, fail_silently=False, connection=None,
        html_message=None, attachments=None
):
    email = EmailMultiAlternatives(
        subject=subject,
        body=html_message,
        from_email=from_email,
        to=recipient_list,
        attachments=attachments,
        connection=connection,
    )
    email.attach_alternative(html_message, 'text/html')
    email.send(fail_silently=fail_silently)
