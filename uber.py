import requests
import secrets

URL = "https://super2018.uber.magfest.org/uber/jsonrpc/"
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
    return resp.json()["result"]