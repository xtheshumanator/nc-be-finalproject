import psycopg2
from ssc.dbconfig import user, password

connection = psycopg2.connect(
            user = user,
            password = password,
            database = "ssc")
        cursor = connection.cursor()