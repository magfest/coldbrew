from contextlib import contextmanager
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="coldbrew",
    passwd="coldbrew",
    database="coldbrew",
    autocommit=True
)

cursor = db.cursor(buffered=True, dictionary=True)

cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, url VARCHAR(64), badge INT(16) UNSIGNED, name VARCHAR(255), email VARCHAR(255), payment_type VARCHAR(16), stripe_id VARCHAR(255), password VARCHAR(255))")
cursor.execute("CREATE TABLE IF NOT EXISTS transactions (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, account INT(6) UNSIGNED, amount INT(6), note VARCHAR(255), timestamp TIMESTAMP)")

cursor.close()
db.commit()
db.close()

@contextmanager
def Cursor():
    db = mysql.connector.connect(
            host="localhost",
            user="coldbrew",
            passwd="coldbrew",
            database="coldbrew"
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