from flask import Flask, render_template, jsonify, send_from_directory, request
from datetime import datetime

from passlib.hash import pbkdf2_sha256
from server import app
from util import *
import emailsender
import payments
import random
import string
import slack
import uber

@app.route("/api/logout")
@requires_roles('admin', 'user')
def api_logout():
    return False

@app.route("/api/accounts")
@requires_roles('admin')
def api_accounts():
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts")
        accounts = list(cursor.fetchall())
    return jsonify(accounts)

@app.route("/api/accounts/activate/cash", methods=['POST'])
@requires_roles('admin')
def api_accounts_activate_cash():
    data = request.get_json(force=True)
    if int(data['amount']) + get_balance(data['managed_account']) < 0:
        return jsonify({"success": False, "error": "Account balance cannot go negative."})
    data['amount'] = int(data['amount']) * 100
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['managed_account'],))
        managed_account = cursor.fetchone()
        if managed_account['payment_type'] != "cash":
            if get_balance(managed_account['id']):
                return jsonify({"success": False, "error": "You cannot change payment types while a balance remains on your account."})
            cursor.execute("UPDATE accounts SET payment_type = %s WHERE id = %s", ("cash", managed_account['id']))
        slack.postText("Added {} to {} using cash.".format(format_dollars(data['amount']), managed_account['name']))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO transactions (account, amount, note, timestamp) VALUES (%s, %s, %s, %s)", (managed_account['id'], data['amount'], "Cash Transaction", timestamp))
    return jsonify({"success": True})

@app.route("/api/accounts/activate/stripe", methods=['POST'])
@requires_roles('admin', 'user')
def api_accounts_activate_stripe():
    data = request.get_json(force=True)
    if int(data['amount']) + get_balance(data['managed_account']) < 0:
        return jsonify({"success": False, "error": "Your overall balance cannot go negative."})
    data['amount'] = int(data['amount']) * 100
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['managed_account'],))
        managed_account = cursor.fetchone()
        if managed_account['payment_type'] != "stripe":
            if get_balance(managed_account['id']):
                return jsonify({"success": False, "error": "You cannot change payment types while a balance remains on your account."})
            cursor.execute("UPDATE accounts SET payment_type = %s WHERE id = %s", ("stripe", managed_account['id']))
        if managed_account['stripe_id']:
            stripe_id = managed_account['stripe_id']
        else:
            stripe_id = payments.create_customer(managed_account, data['token'])
            cursor.execute("UPDATE accounts SET stripe_id = %s WHERE id = %s", (stripe_id, managed_account['id']))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO transactions (account, amount, note, timestamp) VALUES (%s, %s, %s, %s)", (managed_account['id'], data['amount'], "Stripe Transaction", timestamp))
    slack.postText("Changed stripe spend limit for {} by {}.".format(managed_account['name'], format_dollars(data['amount'])))
    return jsonify({"success": True})

def account_create(data):
    for field in ['name', 'email', 'badge', 'password']:
        if field in data.keys():
            if data[field]:
                continue
        return jsonify({"success": False, "error": "You must provide {} {}.".format("an" if field == "email" else "a", field)})
    try:
        assert int(data['badge']) >= 0
    except:
        return jsonify({"success": False, "error": "Badge must be an integer that is greater than or equal to 0."})
    if data['password'] is None:
        password_hash = ""
    elif len(data['password']) < 8:
        return jsonify({"success": False, "error": "Password must be at least 8 characters long."})
    else:
        password_hash = pbkdf2_sha256.hash(data['password'])
    with Cursor() as cursor:
        cursor.execute("SELECT badge FROM accounts WHERE badge = %s", (data['badge'],))
        if cursor.fetchall():
            return jsonify({"success": False, "error": "An account already exists for this badge id."})
        cursor.execute("SELECT badge FROM accounts WHERE name = %s", (data['name'],))
        if cursor.fetchall():
            return jsonify({"success": False, "error": "An account already exists for this name."})
        url = str(uuid.uuid4())
        barcode = "^" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        cursor.execute("INSERT INTO accounts (badge, name, email, password, url, volunteer_barcode) VALUES (%s, %s, %s, %s, %s, %s)", (data['badge'], data['name'], data['email'], password_hash, url, barcode))
        if cursor.rowcount == 1:
            cursor.execute("SELECT * FROM accounts WHERE badge = %s", (data['badge'],))
            account = cursor.fetchone()
            emailsender.welcome(account)
            slack.postText("Created new account {}".format(account['name']))
            return jsonify({"success": True, "account": account})
        else:
            return jsonify({"success": False, "error": "An unknown database error occurred."})

@app.route("/api/accounts/create", methods=['POST'])
@requires_roles('admin')
def api_accounts_create():
    data = request.get_json(force=True)
    return account_create(data)

@app.route("/api/accounts/delete", methods=['POST'])
@requires_roles('admin')
def api_accounts_delete():
    data = request.get_json(force=True)
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['managed_account'],))
        account = cursor.fetchone()
        if get_balance(data['managed_account']) and account['payment_type'] == "cash":
            return jsonify({"success": False, "error": "You cannot delete accounts that currently have a cash balance."})
        cursor.execute("DELETE FROM accounts WHERE id = %s", (data['managed_account'],))
        cursor.execute("DELETE FROM transactions WHERE account = %s", (data['managed_account'],))
    return jsonify({"success": True})

@app.route("/api/accounts/lookup", methods=['POST'])
def api_accounts_lookup():
    data = request.get_json(force=True)
    with Cursor() as cursor:
        uberdata = uber.lookup(data['barcode'])
        found = True
        if not "result" in uberdata.keys():
            found = False
        elif not uberdata["result"]:
            found = False
        if not found:
            cursor.execute("SELECT * FROM accounts where volunteer_barcode = %s", (data['barcode'],))
            account = cursor.fetchone()
            if not account:
                return jsonify({"success": False, "type": "invalid", "error": "Badge not found in Uber."})
        else:
            badge = str(uberdata["result"]["badge_num"])
            cursor.execute("SELECT * FROM accounts WHERE badge = %s", (badge,))
            account = cursor.fetchone()
        if not account:
            resp = account_create({
                "name": uberdata["result"]["first_name"] + " " + uberdata["result"]["last_name"],
                "email": uberdata["result"]["email"],
                "badge": uberdata["result"]["badge_num"],
                "password": None
            })
            if resp.get_json()['success']:
                return jsonify({"success": False, "type": "unknown", "error": "Email sent."})
            return jsonify({"success": False, "type": "invalid", "error": "Failed to register new account."})
        funds = format_dollars(get_balance(account['id']))
    return jsonify({"success": True, "funds": funds, "account": account})

@app.route("/api/transactions")
@requires_roles('admin')
def api_transactions():
    return jsonify(get_transactions())

@app.route("/api/pour", methods=['POST'])
def api_pour():
    data = request.get_json(force=True)
    if not 'secret' in data.keys():
        return jsonify({"success": False, "error": "You must provide a secret key to authorize pours."})
    if data['secret'].lower() != secrets.DASH_KEY.lower():
        return jsonify({"success": False, "error": "You must provide a secret key to authorize pours."})
    if not 'account' in data.keys():
        return jsonify({"success": False, "error": "You must provide the id of an account to charge."})
    with Cursor() as cursor:
        if get_balance(data['account']) + data['amount'] < 0:
            return jsonify({"success": False, "error": "Insufficient Funds"})
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['account'],))
        account = cursor.fetchone()
        if account['payment_type'] == "stripe":
            if not payments.bill_coldbrew(account):
                return jsonify({"success": False, "error": "Failed to authorize transaction with Stripe."})
        cursor.execute("INSERT INTO transactions (account, amount, note, timestamp) VALUES (%s, %s, %s, %s)", (str(data['account']), str(data['amount']), data['note'], timestamp))
        slack.postText("{} poured a drink.".format(account['name']))
        return jsonify({"success": True})

@app.route("/api/tapstate", methods=['GET', 'POST'])
def api_tapstate():
    if request.method == 'POST':
        data = request.get_json(force=True)
        with Cursor() as cursor:
            cursor.execute("INSERT INTO tapstate (tap, state, timestamp) VALUES (%s, %s, %s)", (str(data['pin']), bool(data['state']), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        if data['state']:
            slack.postText("Drink poured from tap #{}".format(data['pin']))
        return jsonify({"success": True})
    elif request.method == 'GET':
        with Cursor() as cursor:
            cursor.execute("SELECT * FROM tapstate WHERE id IN (SELECT MAX(id) FROM tapstate GROUP BY tap)")
            tapstate = cursor.fetchall()
        return jsonify(tapstate)

@app.route("/api/report", methods=['POST'])
def api_report():
    slack.postText("Drink reported stolen!")
    return jsonify({"success": True})
