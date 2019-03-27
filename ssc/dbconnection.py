import os
import urllib.parse as urlparse

import psycopg2

ON_HEROKU = 'ON_HEROKU' in os.environ

def getDBConnection():
    try:
        if (ON_HEROKU):
            url = urlparse.urlparse(os.environ['DATABASE_URL'])
            dbname = url.path[1:]
            user = url.username
            password = url.password
            host = url.hostname
            port = url.port
            connection = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
        else:
            connection = psycopg2.connect(
                database="ssc")
    except:
        connection=None
    finally:
        return connection



def getAsyncConn():
    if (ON_HEROKU):
        url = urlparse.urlparse(os.environ['DATABASE_URL'])
        dbname = url.path[1:]
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port

        dsn = "dbname="+dbname+" user="+user+" password="+password+" host="+host+" port="+str(port)
        return dsn
    else:
        return 'dbname=ssc'
