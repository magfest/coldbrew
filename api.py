from server import app
from util import *

@app.route("/api/login")
@requires_roles('admin', 'user', 'anonymous')
def api_login():
    return False

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

@app.route("/api/accounts/activate", methods=['POST'])
@requires_roles('admin', 'user')
def api_accounts_activate():
    data = request.get_json(force=True)
    if not 'payment_type' in data.keys():
        return jsonify({"success": False, "error": "You must provide a payment type to activate an account."})
    if data['payment_type'] == "stripe":
        if not 'token' in data.keys():
            return jsonify({"success": False, "error": "You must provide a stripe credit card token to activate an account."})
        if not 'password' in data.keys():
            return jsonify({"success": False, "error": "You must provide a password to activate an account with stripe."})
        if not 'amount' in data.keys():
            return jsonify({"success": False, "error": "You must provide an authorized amount of money to activate an account."})
        if int(data['amount']) < 0:
            return jsonify({"success": False, "error": "You must provide a positive amount of money for your account."})
        if not 'account' in data.keys():
            return jsonify({"success": False, "error": "You must provide an account to be activated."})
        with Cursor() as cursor:
            cursor.execute("SELECT amount FROM transactions WHERE account = %s", (data['account'],))
            transactions = list(cursor.fetchall())
            total = decimal.Decimal(0) 
            for transaction in transactions:
                total += decimal.Decimal(transaction['amount']) / decimal.Decimal(100)
            cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['account'],))
            account = cursor.fetchone()
            if not pbkdf2_sha256.verify(data['password'], account['password']):
                return jsonify({"success": False, "error": "You are not authorized to link this account to stripe."})
            if account['payment_type'] != "stripe" and total != 0:
                return jsonify({"success": False, "error": "You cannot change payment types while a balance remains on your account."})
            if account['stripe_id']:
                stripe_id = account['stripe_id']
            else:
                stripe_id = payments.create_customer(account, data['token'])
            cursor.execute("UPDATE accounts SET stripe_id = %s, payment_type = %s WHERE id = %s", (stripe_id, "stripe", data['account']))
            ts = time.time()
            timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO transactions (account, amount, note, timestamp) VALUES (%s, %s, %s, %s)", (data['account'], data['amount'], "Stripe Transaction", timestamp))
        return jsonify({"success": True})
    elif data['payment_type'] == "cash":
        if not 'username' in data.keys():
            return jsonify({"success": False, "error": "You must provide an authorized username to activate an account with cash."})
        if not 'password' in data.keys():
            return jsonify({"success": False, "error": "You must provide an authorized password to activate an account with cash."})
        if not 'amount' in data.keys():
            return jsonify({"success": False, "error": "You must provide an authorized amount of money to activate an account."})
        if int(data['amount']) < 0:
            return jsonify({"success": False, "error": "You must provide a positive amount of money for your account."})
        if not 'account' in data.keys():
            return jsonify({"success": False, "error": "You must provide an account to be activated."})
        if not data['username'] in secrets.ADMINS:
            return jsonify({"success": False, "error": "You are not authorized to accept cash payments."})
        with Cursor() as cursor:
            cursor.execute("SELECT amount FROM transactions WHERE account = %s", (data['account'],))
            transactions = list(cursor.fetchall())
            total = decimal.Decimal(0) 
            for transaction in transactions:
                total += decimal.Decimal(transaction['amount']) / decimal.Decimal(100)
            cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['account'],))
            account = cursor.fetchone()
            if account['payment_type'] != "cash" and total != 0:
                return jsonify({"success": False, "error": "You cannot change payment types while a balance remains on your account."})
            cursor.execute("SELECT * FROM accounts WHERE name = %s", (data['username'],))
            authorized = cursor.fetchone()
            if not pbkdf2_sha256.verify(data['password'], authorized['password']):
                return jsonify({"success": False, "error": "You are not authorized to accept cash payments."})
            cursor.execute("UPDATE accounts SET payment_type = %s WHERE id = %s", ("cash", data['account']))
            ts = time.time()
            timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO transactions (account, amount, note, timestamp) VALUES (%s, %s, %s, %s)", (data['account'], data['amount'], "Cash Transaction", timestamp))
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
        cursor.execute("SELECT * FROM accounts WHERE name = %s", (data['name'],))
        authorized = cursor.fetchone()
        if not data['name'] in secrets.ADMINS:
            return jsonify({"success": False, "error": "You must be an admin to delete accounts."})
        cursor.execute("SELECT * FROM transactions WHERE account = %s ORDER BY timestamp", (data['account'],))
        transactions = cursor.fetchall()
        total = 0
        for transaction in transactions:
            total += transaction['amount']
        if total != 0:
            return jsonify({"success": False, "error": "You cannot delete accounts that currently have a balance."})
        if pbkdf2_sha256.verify(data['password'], authorized['password']):
            cursor.execute("DELETE FROM accounts WHERE id = %s", (data['account'],))
            cursor.execute("DELETE FROM transactions WHERE account = %s", (data['account'],))
        else:
            return jsonify({"success": False, "error": "Login Incorrect"})
    return jsonify({"success": True})

@app.route("/api/accounts/lookup", methods=['POST'])
def api_accounts_lookup():
    data = request.get_json(force=True)
    if not ('barcode' in data.keys() or 'id' in data.keys()):
        return jsonify({"success": False, "type": "invalid", "error": "You must provide a barcode or an id to lookup."})
    with Cursor() as cursor:
        if 'barcode' in data.keys():
            if data['barcode'] in barcode_cache.keys():
                attendee = barcode_cache[data['barcode']]
            else:
                uberdata = uber.lookup(data['barcode'])
                if "result" in uberdata.keys():
                    attendee = uberdata["result"]
                else:
                    return jsonify({"success": False, "type": "invalid", "error": "Could not locate badge in Uber."})
                barcode_cache[data['barcode']] = attendee
            if not attendee:
                return jsonify({"success": False, "type": "invalid", "error": "Badge not found in Uber."})
            badge = str(attendee["badge_num"])
            cursor.execute("SELECT * FROM accounts WHERE badge = %s", (badge,))
            account = cursor.fetchone()
            if not account:
                return jsonify({"success": False, "type": "unknown", "error": "You do not have a TechOps Coldbrew account."})
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
@requires_roles('admin')
def api_transactions():
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM transactions")
        transactions = list(cursor.fetchall())
    return jsonify(transactions)

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
        cursor.execute("SELECT amount FROM transactions WHERE account = %s", (data['account'],))
        transactions = cursor.fetchall()
        total = 0
        for transaction in transactions:
            total += transaction['amount']
        if total + data['amount'] < 0:
            return jsonify({"success": False, "error": "Insufficient Funds"})
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (data['account'],))
        account = cursor.fetchone()
        if account['payment_type'] == "stripe":
            # This account was paid using stripe
            if not payments.bill_coldbrew(account):
                return jsonify({"success": False, "error": "Failed to authorize transaction with Stripe."})
        elif account['payment_type'] == "cash":
            # This account paid in cash
            pass
        else:
            return jsonify({"success": False, "error": "No payment types available for this account."})
        cursor.execute("INSERT INTO transactions (account, amount, note, timestamp) VALUES (%s, %s, %s, %s)", (str(data['account']), str(data['amount']), data['note'], timestamp))
        return jsonify({"success": True})
