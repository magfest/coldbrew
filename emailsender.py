from email.message import EmailMessage
import smtplib
import secrets

def welcome(account):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(secrets.EMAIL_USER, secrets.EMAIL_PASS)
    body = """Dear {name},

You have created an account on the TechOps Nitro ColdBrew system. In order to recoup the cost of renting the kegs of coffee, we are charging for each cup of coldbrew.
We charging $2.00 per 12oz cup. We can either take this as cash or by credit card through stripe.

If you would like to pay by cash please talk to Robert Scullin (@rscullin on slack) or Mark Murnane (@bitbyt3r on slack).

If you would like to pay by credit card then please go here: https://coldbrew.magevent.net/activate/stripe/{url}
From that page you can enter your credit card information, as well as a cap on how much you wish to spend. This will not be charged to your card immediately. Instead, stripe will 
charge for however much you actually spent in one transaction at the end of the week.

Once you have added money to your account you can spend it by scanning your badge at the coldbrew kiosk and pressing the 'accept' arrow once per pour. You can also check your balance
at the kiosk by scanning your badge, then pressing the 'exit' button.

Thanks, and enjoy!
Mark
    """.format(name=account['name'], url=account['url'])
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = "TechOps Nitro Coldbrew"
    msg['From'] = secrets.EMAIL_FROM
    msg['To'] = account['email']
    server.send_message(msg)
    server.quit()