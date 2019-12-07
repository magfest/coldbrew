from contextlib import contextmanager
import mysql.connector
import secrets

db = mysql.connector.connect(
    host=secrets.DB_HOST,
    user=secrets.DB_USER,
    passwd=secrets.DB_PASS,
    database=secrets.DB_BASE,
    autocommit=True
)

cursor = db.cursor(buffered=True, dictionary=True)

cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, url VARCHAR(64), badge INT(16) UNSIGNED, name VARCHAR(255), email VARCHAR(255), payment_type VARCHAR(16), stripe_id VARCHAR(255), password VARCHAR(255), volunteer_barcode VARCHAR(255))")
cursor.execute("CREATE TABLE IF NOT EXISTS transactions (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, account INT(6) UNSIGNED, amount INT(6), note VARCHAR(255), timestamp TIMESTAMP)")
cursor.execute("CREATE TABLE IF NOT EXISTS sessions (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, account INT(6) UNSIGNED, sessionkey VARCHAR(64), expiration TIMESTAMP)")
cursor.execute("CREATE TABLE IF NOT EXISTS tapstate (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, tap int(6) UNSIGNED, state BOOLEAN, timestamp TIMESTAMP)")
cursor.execute("SELECT * FROM accounts WHERE name = 'bitbyt3r'")
accounts = cursor.fetchall()
if not accounts:
    cursor.execute("INSERT INTO accounts (url, badge, name, email, password) VALUES (%s, %s, %s, %s, %s)", (*secrets.DEFAULT_ADMIN,))

cursor.close()
db.commit()
db.close()

@contextmanager
def Cursor():
    db = mysql.connector.connect(
            host=secrets.DB_HOST,
            user=secrets.DB_USER,
            passwd=secrets.DB_PASS,
            database=secrets.DB_BASE,
        )
    cursor = db.cursor(buffered=True, dictionary=True)
    try:
        yield cursor
    except:
        raise
    else:
        db.commit()
    finally:
        cursor.close()
        db.close()