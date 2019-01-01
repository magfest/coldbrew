import requests
import secrets

def poured():
    requests.post(secrets.SLACK_URL, json={"text": "A Nitro Cold Brew was poured!"})

def postText(text):
    requests.post(secrets.SLACK_URL, json={"text": text})