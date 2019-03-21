import psycopg2
from ssc.dbconfig import user, password, database

connection = psycopg2.connect(
    user=user,
    password=password,
    database=database)

cursor = connection.cursor()
