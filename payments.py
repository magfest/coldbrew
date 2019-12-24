import time
import stripe
import secrets

stripe.api_key = secrets.STRIPE_KEY

def initialize_plan():
    try:
        stripe.Plan.retrieve("weekly-coldbrew")
    except:
        stripe.Plan.create(
            id="weekly-coldbrew",
            currency='usd',
            interval='week',
            product={
                "id": "coldbrew",
                "name": "8oz ColdBrew Coffee",
                "type": "service"
            },
            nickname="Weekly ColdBrew",
            amount=250,
            usage_type="metered"
        )

def create_customer(account, token):
    customer = stripe.Customer.create(
        description=account['name'],
        email=account['email'],
        metadata={
            "accountid": account['id'],
            "badgenum": account['badge']
        },
        source=token
    )

    subscription = stripe.Subscription.create(
        customer=customer,
        items=[
            {
                "plan": "weekly-coldbrew"
            }
        ]
    )
    print(subscription)
    print(subscription['items']['data'][0]['id'])
    return subscription['items']['data'][0]['id']

def bill_coldbrew(account, method="immediate"):
    if method == "immediate":
        charge = stripe.Charge.create(
            amount=250,
            currency='usd',
            customer=account['id'],
        )
        return True
    elif method == "subscription":
        stripe.UsageRecord.create(
            quantity=1,
            timestamp=int(time.time()),
            subscription_item=account['stripe_id'],
            action='increment'
        )
        return True
    return False
