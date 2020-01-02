from email.message import EmailMessage
import smtplib
import secrets

def welcome(account):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(secrets.EMAIL_USER, secrets.EMAIL_PASS)
    body = """Dear {name},

Thanks for making a Nitro Coldbrew account!

8oz pours of coldbrew coffee are $2.50 each, and you'll be charged for your total consumption after the event.

To link your credit card to your coldbrew account please visit https://coldbrew.magevent.net/activate/stripe/{url}

This page will let you set a spending cap for your account. You will only be billed for your total consumption. We will send an email after the event to confirm your total before your card is charged.

Once you have added money to your account, you can use it by scanning your MAGFest badge at the kiosk, and pressing the 'accept' arrow for each pour. You can also check your balance at the kiosk by scanning your badge, and then pressing the 'exit' button.

We roughly expect to have enough coldbrew to last the event, but make no guarantees as to how long it'll last. As a reminder, setting a high limit doesn't guarantee you coffee, as it's first-come, first-served.

Thanks, and enjoy!
    """.format(name=account['name'], url=account['url'])
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = "Nitro Coldbrew"
    msg['From'] = secrets.EMAIL_FROM
    msg['To'] = account['email']
    server.send_message(msg)
    server.quit()
