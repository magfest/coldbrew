#!/usr/bin/python3
from flask import Flask, render_template, jsonify, send_from_directory, request, redirect
import datetime
import time
import uuid

app = Flask(__name__)

from util import *
from database import Cursor
import payments
import secrets
import emailsender
import slackimport
import uber
import api

payments.initialize_plan()

@app.context_processor
def inject_functions():
    return {"logged_in": logged_in, "is_admin": is_admin, "get_balance": get_balance, "format_dollars": format_dollars}

@app.context_processor
def inject_account():
    return {"account": get_account()}

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('base.html')

@app.route("/login", methods=['GET', 'POST'])
@requires_roles('admin', 'user', 'anonymous')
def loginpage():
    if logged_in():
        return redirect('/')
    return login()

@app.route("/logout", methods=['GET', 'POST'])
def logoutpage():
    return logout()

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')

@app.route("/accounts", methods=['GET', 'POST'])
@requires_roles('admin')
def accounts():
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts")
        accounts = list(cursor.fetchall())
        balances = {}
        for account in accounts:
            balances[account['id']] = format_dollars(get_balance(account['id']))
    return render_template('accounts.html', accounts=accounts, balances=balances)

@app.route("/accounts/<path:path>", methods=['GET', 'POST'])
@requires_roles('admin', 'user')
def accounts_details(path):
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts WHERE url = %s", (path,))
        account = cursor.fetchone()
        transactions, total = get_transactions(account['id'])
        return render_template('accounts-details.html', account=account, transactions=transactions, total=total)

@app.route("/transactions", methods=['GET', 'POST'])
@requires_roles('admin')
def transactions():
    transactions, total = get_transactions()
    return render_template('transactions.html', transactions=transactions)

@app.route("/activate/cash/<path:path>", methods=['GET', 'POST'])
@requires_roles('admin')
def activate_cash(path):
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts WHERE url = %s", (path,))
    account = cursor.fetchone()
    return render_template('activate-cash.html', managed_account=account)

@app.route("/activate/stripe/<path:path>", methods=['GET', 'POST'])
@requires_roles('admin', 'user')
def activate_stripe(path):
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM accounts WHERE url = %s", (path,))
    account = cursor.fetchone()
    return render_template('activate-stripe.html', managed_account=account, public_stripe_key=secrets.PUBLIC_STRIPE_KEY)

@app.route("/js/<path:path>")
def send_js(path):
    return send_from_directory("js", path)

if __name__ == "__main__":
    app.run()