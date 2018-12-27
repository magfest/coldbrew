#!/usr/bin/python3
from flask import Flask, render_template, jsonify, send_from_directory, request
from passlib.hash import pbkdf2_sha256
import datetime
import decimal
import time

from database import Cursor
import uber

app = Flask(__name__)

barcode_cache = {}

@app.route("/")
def home():
    return render_template('base.html')

@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')

@app.route("/accounts")
def accounts():
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts")
        accounts = list(cursor.fetchall())
        cursor.execute("SELECT * FROM transactions")
        transactions = list(cursor.fetchall())
        balances = {}
        decimal.getcontext().prec = 2
        for account in accounts:
            balances[account['id']] = decimal.Decimal(0) 
        for transaction in transactions:
            balances[transaction['account']] += decimal.Decimal(transaction['amount']) / decimal.Decimal(100)
        print(accounts)
        print(balances)
    return render_template('accounts.html', accounts=accounts, balances=balances)

@app.route("/transactions")
def transactions():
    with Cursor() as cursor:
        cursor.execute("SELECT transactions.id, transactions.amount, accounts.badge, accounts.name, accounts.email, transactions.note, transactions.timestamp FROM transactions LEFT JOIN accounts ON transactions.account = accounts.id ORDER BY transactions.timestamp")
        transactions = list(cursor.fetchall())
    print(transactions)
    for transaction in transactions:
        transaction['amount'] = int(transaction['amount']) / 100
        if transaction['amount'] > 0:
            transaction['amount'] = "$%.2f" % float(transaction['amount'])
        else:
            transaction['amount'] = "-$%.2f" % abs(float(transaction['amount']))
    return render_template('transactions.html', transactions=transactions)

@app.route("/api/accounts")
def api_accounts():
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts")
        accounts = list(cursor.fetchall())
    return jsonify(accounts)

@app.route("/api/accounts/create", methods=['POST'])
def api_accounts_create():
    data = request.get_json(force=True)
    print(data)
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
        cursor.execute("INSERT INTO accounts (badge, name, email, password) VALUES (%s, %s, %s, %s)", (data['badge'], data['name'], data['email'], password_hash))
        if cursor.rowcount == 1:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "An unknown database error occurred."})

@app.route("/api/accounts/lookup", methods=['POST'])
def api_accounts_lookup():
    data = request.get_json(force=True)
    if not ('barcode' in data.keys() or 'id' in data.keys()):
        return jsonify({"success": False, "error": "You must provide a barcode or an id to lookup."})
    with Cursor() as cursor:
        if 'barcode' in data.keys():
            if data['barcode'] in barcode_cache.keys():
                print("Retrieving barcode from cache")
                attendee = barcode_cache[data['barcode']]
            else:
                print("Fetching barcode from uber")
                attendee = uber.lookup(data['barcode'])
                barcode_cache[data['barcode']] = attendee
            if not attendee:
                return jsonify({"success": False, "error": "Badge not found in Uber."})
            badge = str(attendee["badge_num"])
            cursor.execute("SELECT * FROM accounts WHERE badge = %s", (badge,))
            account = cursor.fetchone()
            if not account:
                return jsonify({"success": False, "error": "You do not have a TechOps Coldbrew account."})
            cursor.execute("SELECT amount FROM transactions WHERE account = %s", (account['id'],))
        else:
            cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['id'],))
            account = cursor.fetchone()
            cursor.execute("SELECT amount FROM transactions WHERE account = %s", (data['id'],))
        transactions = list(cursor.fetchall())
        total = decimal.Decimal(0) 
        for transaction in transactions:
            total += decimal.Decimal(transaction['amount']) / decimal.Decimal(100)
    return jsonify({"success": True, "funds": "%.2f" % total, "account": account})

    
@app.route("/api/transactions")
def api_transactions():
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM transactions")
        transactions = list(cursor.fetchall())
    return jsonify(transactions)

@app.route("/api/transactions/create", methods=['POST'])
def api_transactions_create():
    data = request.get_json(force=True)
    if not 'account' in data.keys():
        return jsonify({"success": False, "error": "You must provide the id of an account to charge."})
    if not 'amount' in data.keys():
        return jsonify({"success": False, "error": "You must provide the amount of the transaction."})
    with Cursor() as cursor:
        cursor.execute("SELECT amount FROM transactions WHERE account = %s", (data['account'],))
        transactions = cursor.fetchall()
        total = 0
        for transaction in transactions:
            total += transaction['amount']
        if total + data['amount'] < 0:
            return jsonify({"success": False, "error": "Insufficient Funds"})
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO transactions (account, amount, note, timestamp) VALUES (%s, %s, %s, %s)", (str(data['account']), str(data['amount']), data['note'], timestamp))
    return jsonify({"success": True})

@app.route("/js/<path:path>")
def send_js(path):
    return send_from_directory("js", path)

if __name__ == "__main__":
    app.run()
