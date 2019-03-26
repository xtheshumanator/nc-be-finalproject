import psycopg2
from passlib.hash import pbkdf2_sha256

from ssc.dbconnection import getDBConnection


def fetch_user_details(username, password):
    res = {}
    password_ok = False
    try:
        connection = getDBConnection()
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        encrypted_pw = cursor.fetchone()[0]
        print(encrypted_pw)
        count = cursor.rowcount
        print(count)

        if (count == 1):
            password_ok = pbkdf2_sha256.verify(password, encrypted_pw)
        else:
            res["error"] = "Invalid username and/or password"
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        res["error"] = str(error)
    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        res["user_exists"] = password_ok
        return res
