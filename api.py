from flask import Flask, render_template, jsonify, send_from_directory, request
from datetime import datetime

from server import app
from util import *
import emailsender
import payments
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
    if int(data['amount']) < 0:
        return jsonify({"success": False, "error": "You must provide a positive amount of money for your account."})
    data['amount'] = int(data['amount']) * 100
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['managed_account'],))
        managed_account = cursor.fetchone()
        if managed_account['payment_type'] != "cash":
            if get_balance(managed_account['id']):
                return jsonify({"success": False, "error": "You cannot change payment types while a balance remains on your account."})
            cursor.execute("UPDATE accounts SET payment_type = %s WHERE id = %s", ("cash", managed_account['id']))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO transactions (account, amount, note, timestamp) VALUES (%s, %s, %s, %s)", (managed_account['id'], data['amount'], "Cash Transaction", timestamp))
    return jsonify({"success": True})

@app.route("/api/accounts/activate/stripe", methods=['POST'])
@requires_roles('admin', 'user')
def api_accounts_activate_stripe():
    data = request.get_json(force=True)
    if int(data['amount']) < 0:
        return jsonify({"success": False, "error": "You must provide a positive amount of money for your account."})
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
    return jsonify({"success": True})

@app.route("/api/accounts/create", methods=['POST'])
@requires_roles('admin')
def api_accounts_create():
    data = request.get_json(force=True)
    for field in ['name', 'email', 'badge', 'password']:
        if field in data.keys():
            if data[field]:
                continue
        return jsonify({"success": False, "error": "You must provide {} {}.".format("an" if field == "email" else "a", field)})
    try:
        assert int(data['badge']) >= 0
    except:
        return jsonify({"success": False, "error": "Badge must be an integer that is greater than or equal to 0."})
    if len(data['password']) < 8:
        return jsonify({"success": False, "error": "Password must be at least 8 characters long."})
    password_hash = pbkdf2_sha256.hash(data['password'])
    with Cursor() as cursor:
        cursor.execute("SELECT badge FROM accounts WHERE badge = %s", (data['badge'],))
        if cursor.fetchall():
            return jsonify({"success": False, "error": "An account already exists for this badge id."})
        cursor.execute("SELECT badge FROM accounts WHERE name = %s", (data['name'],))
        if cursor.fetchall():
            return jsonify({"success": False, "error": "An account already exists for this name."})
        url = str(uuid.uuid4())
        cursor.execute("INSERT INTO accounts (badge, name, email, password, url) VALUES (%s, %s, %s, %s, %s)", (data['badge'], data['name'], data['email'], password_hash, url))
        if cursor.rowcount == 1:
            cursor.execute("SELECT * FROM accounts WHERE badge = %s", (data['badge'],))
            account = cursor.fetchone()
            emailsender.welcome(account)
            return jsonify({"success": True, "account": account})
        else:
            return jsonify({"success": False, "error": "An unknown database error occurred."})

@app.route("/api/accounts/delete", methods=['POST'])
@requires_roles('admin')
def api_accounts_delete():
    data = request.get_json(force=True)
    with Cursor() as cursor:
        if get_balance(data['managed_account']):
            return jsonify({"success": False, "error": "You cannot delete accounts that currently have a balance."})
        cursor.execute("DELETE FROM accounts WHERE id = %s", (data['managed_account'],))
        cursor.execute("DELETE FROM transactions WHERE account = %s", (data['managed_account'],))
    return jsonify({"success": True})

@app.route("/api/accounts/lookup", methods=['POST'])
def api_accounts_lookup():
    data = request.get_json(force=True)
    with Cursor() as cursor:
        uberdata = uber.lookup(data['barcode'])
        if not "result" in uberdata.keys():
            return jsonify({"success": False, "type": "invalid", "error": "Could not locate badge in Uber."})
        if not uberdata["result"]:
            return jsonify({"success": False, "type": "invalid", "error": "Badge not found in Uber."})
        badge = str(uberdata["result"]["badge_num"])
        cursor.execute("SELECT * FROM accounts WHERE badge = %s", (badge,))
        account = cursor.fetchone()
        if not account:
            return jsonify({"success": False, "type": "unknown", "error": "You do not have a TechOps Coldbrew account."})
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
        slack.poured()
        return jsonify({"success": True})

@app.route("/api/tapstate", methods=['GET', 'POST'])
def api_tapstate():
    data = request.get_json(force=True)
    print("Pin {} went {}".format(data["pin"], "high" if data["state"] else "low"))
    return jsonify({"success": True})