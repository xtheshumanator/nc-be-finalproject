import psycopg2

from ssc.dbconnection import getDBConnection


def add_audio_key(audio_key, session_id):
    connection = None
    try:
        connection = getDBConnection()
        cursor = connection.cursor()

        add_audio_key_sql = "INSERT INTO audio_keys (audio_key, session_id)" \
                            "VALUES (%s, %s)"

        cursor.execute(add_audio_key_sql, (audio_key, session_id))
        connection.commit()

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return False

    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

    return 'Key Added Successfully'


def get_audio_key(session_id):
    connection = None
    try:
        connection = getDBConnection()
        cursor = connection.cursor()

        get_audio_key_sql = "SELECT audio_key FROM audio_keys " \
                            "WHERE session_id = %s "
        cursor.execute(get_audio_key_sql, [session_id])

        key = cursor.fetchone()
        # if (cursor.rowcount != 0):
        #     user_added = True
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return False
    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

        if key == None:
            return {"error": "There has been error, your session may have expired, please try again"}

        res = key[0]
        return res
