import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

sk_sendgrid = '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'
message = Mail(
    from_email='ss.xlr8@gmail.com',
    to_emails='dev.sovg@gmail.com',
    subject='Pizzeria Mar y Ana - Activar Cuenta',
    html_content='<strong>active su cuenta haciendo click <a href="www.google.com">aqui</a></strong>'
)
try:
    sg = SendGridAPIClient(sk_sendgrid)
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)