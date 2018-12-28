from email.message import EmailMessage
import smtplib
import secrets

def welcome(account):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(secrets.EMAIL_USER, secrets.EMAIL_PASS)
    body = """Dear {name},

Thanks for making a TechOps Nitro Coldbrew account!

8oz pours of coldbrew coffee are $2 each, and you'll be charged for your total consumption after the event. If you'd like to pay in cash (we prefer you don't, though, as it's a hassle), please talk to Robert Scullin (@rscullin on Slack) or Mark Murnane (@bitbyt3r on Slack).

If you would like to link your credit card via Stripe, please visit https://coldbrew.magevent.net/activate/stripe/{url} while on Event Wifi or a MAG laptop. From that page, you can enter your CC info, as well as set an upper limit -- you won't be charged this value, but serves as a way of self-limiting yourself. After the event ends (or we run out), we'll charge you for what you actually consumed.

Once you have added money to your account, you can use it by scanning your MAGFest badge at the kiosk, and pressing the 'accept' arrow for each pour. You can also check your balance at the kiosk by scanning your badge, and then pressing the 'exit' button.

We roughly expect to have enough coldbrew to last the event, but make no guarantees as to how long it'll last. As a reminder, setting a high limit doesn't guarantee you coffee, as it's first-come, first-served.

Thanks, and enjoy!
    """.format(name=account['name'], url=account['url'])
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = "TechOps Nitro Coldbrew"
    msg['From'] = secrets.EMAIL_FROM
    msg['To'] = account['email']
    server.send_message(msg)
    server.quit()