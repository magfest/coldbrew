import json
import os

for i in [
    "DASH_KEY",
    "DATABASE_URL",
    "DEFAULT_ADMIN",
    "EMAIL_FROM",
    "EMAIL_USER",
    "EMAIL_PASS",
    "STRIPE_KEY",
    "PUBLIC_STRIPE_KEY",
    "SLACK_URL",
    "UBER_URL",
    "UBER_KEY",
    "ADMINS",
    "PRICE",
]:
    if i in os.environ:
        if i in ["ADMINS", "DEFAULT_ADMIN"]:
            vars()[i] = json.loads(os.environ[i])
        else:
            vars()[i] = os.environ[i]
    else:
        print(f"You must provide the environment variable {i} to start coldbrew-dashboard.")