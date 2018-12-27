import requests
import secrets

URL = secrets.UBER_URL
KEY = secrets.UBER_KEY

headers = {
    "X-Auth-Token": KEY,
}

def lookup (barcode):
    data = {
        "method": "barcode.lookup_attendee_from_barcode",
        "params": [barcode,]
    }
    resp = requests.post(URL, json=data, headers=headers)
    print(resp.text)
    return resp.json()["result"]