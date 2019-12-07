import json
import os

for i in [
    "DASH_KEY",
    "DB_HOST",
    "DB_USER",
    "DB_PASS",
    "DB_BASE",
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
]:
    if i in os.environ:
        vars()[i] = json.loads(os.environ[i])
    else:
        print(f"You must provide the environment variable {i} to start coldbrew-dashboard.")