from datetime import datetime, timedelta
from flask import request, render_template, make_response, g
from passlib.hash import pbkdf2_sha256
from functools import wraps
import uuid

from database import Cursor
import secrets

def get_balance(account):
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM transactions WHERE account = %s", (account,))
        transactions = cursor.fetchall()
        total = 0
        for transaction in transactions:
            total += transaction['amount']
    return total

def format_dollars(cents):
    if cents >= 0:
        return "$%.2f" % (cents / 100)
    return "-$%.2f" % abs(cents / 100)

def get_transactions(account=None):
    with Cursor() as cursor:
        if account:
            cursor.execute("SELECT * FROM accounts WHERE id = %s", (account,))
            account = cursor.fetchone()
            cursor.execute("SELECT transactions.id, transactions.amount, accounts.id as 'account', accounts.badge, accounts.name, accounts.email, transactions.note, transactions.timestamp FROM transactions LEFT JOIN accounts ON transactions.account = accounts.id WHERE transactions.account = %s ORDER BY transactions.timestamp", (account['id'],))
        else:
            cursor.execute("SELECT transactions.id, transactions.amount, accounts.id as 'account', accounts.badge, accounts.name, accounts.email, transactions.note, transactions.timestamp FROM transactions LEFT JOIN accounts ON transactions.account = accounts.id ORDER BY transactions.timestamp")
        transactions = cursor.fetchall()
        total = {}
        for transaction in transactions:
            if not transaction['account'] in total.keys():
                total[transaction['account']] = 0
            total[transaction['account']] += transaction['amount']
            transaction['amount'] = format_dollars(transaction['amount'])
            transaction['total'] = format_dollars(total[transaction['account']])
        grand_total = None
        if transactions:
            grand_total = format_dollars(total[transactions[0]['account']]) 
    return transactions, grand_total

def check_session():
    account = request.cookies.get('account')
    session = request.cookies.get('session')
    with Cursor() as cursor:
        cursor.execute("SELECT * FROM sessions WHERE sessionkey = %s AND account = %s", (session, account))
        sessions = cursor.fetchall()
        cursor.execute("DELETE FROM sessions WHERE sessionkey = %s AND account = %s", (session, account))
        for session in sessions:
            if session['expiration'] > datetime.now():
                cursor.execute("INSERT INTO sessions (account, sessionkey, expiration) VALUES (%s, %s, %s)", (account, session['sessionkey'], (datetime.now()+timedelta(hours=24)).strftime('%Y-%m-%d %H-%M-%S')))
                return True
    return False

def clear_session():
    if check_session():
        with Cursor() as cursor:
            account = request.cookies.get('account')
            session = request.cookies.get('session')
            cursor.execute("DELETE FROM sessions WHERE sessionkey = %s AND account = %s", (session, account))

def get_account():
    account = request.cookies.get('account')
    with Cursor() as cursor:
        cursor.execute("SELECT * from accounts WHERE id = %s", (account,))
        return cursor.fetchone()

def check_login():
    if request.method == 'POST':
        username = request.values.get('username')
        password = request.values.get('password')
    elif request.method == 'GET':
        username = request.args.get('username')
        password = request.args.get('password')
    if username and password:
        with Cursor() as cursor:
            cursor.execute("SELECT * FROM accounts WHERE name = %s", (username,))
            account = cursor.fetchone()
            if pbkdf2_sha256.verify(password, account['password']):
                session = str(uuid.uuid4())
                expiration = (datetime.now()+timedelta(hours=24)).strftime('%Y-%m-%d %H-%M-%S')
                cursor.execute("INSERT INTO sessions (account, sessionkey, expiration) VALUES (%s, %s, %s)", (account['id'], session, expiration))
                return account, [("account".encode('UTF-8'), str(account['id']).encode('UTF-8')), ("session".encode('UTF-8'), session.encode('UTF-8'))]
    return None, []

def get_current_user_role():
    account, cookies = check_login()
    if account:
        if account['name'] in secrets.ADMINS:
            return 'admin', cookies
        return 'user', cookies
    if check_session():
        account = get_account()
        if account['name'] in secrets.ADMINS:
            return 'admin', cookies
        return 'user', cookies
    return 'anonymous', cookies

def login():
    return render_template('login.html')

def logout():
    g.logged_in = False
    response = make_response(render_template('logout.html'))
    response.set_cookie("session".encode('UTF-8'), bytes(), expires=0)
    response.set_cookie("account".encode('UTF-8'), bytes(), expires=0)
    clear_session()
    return response

def permission_error():
    return render_template('403.html')

def logged_in():
    if not 'logged_in' in g:
        g.logged_in = check_session()
    return g.logged_in

def is_admin():
    if not 'is_admin' in g:
        role, cookies = get_current_user_role()
        g.is_admin = role == 'admin'
    return g.is_admin

def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            role, cookies = get_current_user_role()
            if role not in roles:
                if role == 'anonymous':
                    g.logged_in = False
                    return login()
                g.logged_in = False
                return permission_error()
            g.logged_in = True
            if role == 'anonymous':
                g.logged_in = False
            response = make_response(f(*args, **kwargs))
            for cookie in cookies:
                response.set_cookie(*cookie)
            return response
        return wrapped
    return wrapper