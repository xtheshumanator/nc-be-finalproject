import asyncio

import psycopg2

from ssc.Utils.db_ops import get_workspace_id, get_user_id


# TODO test
def fetch_user_invites(username):
    try:
        connection = psycopg2.connect(
            database="ssc")
        cursor = connection.cursor()

        loop = asyncio.new_event_loop()
        user_id = loop.run_until_complete(get_user_id(username))

        if (user_id == -1):
            return []

        get_invites_sql = """select w.name, u.username from invites i 
                            inner join workspaces w on i.workspace_id=w.workspace_id 
                            inner join users u on i.invited_by_id = u.user_id 
                            where i.user_id=%s"""
        cursor.execute(get_invites_sql, (user_id,))
        user_invites = cursor.fetchall()

        list_of_invites = []
        for row in user_invites:
            list_of_invites.append({'workspace': row[0], 'invited_by': row[1]})

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

    return list_of_invites;


def process_invite(username, invite_response):
    decision = invite_response['accept']
    workspace = invite_response['workspace']

    try:
        connection = psycopg2.connect(
            database="ssc")
        cursor = connection.cursor()

        get_invite_id_sql = """select i.invite_id, i.user_id,  i.workspace_id
                                    from invites i, users u, workspaces w 
                                    where u.username=%s and w.name=%s
                                    and u.user_id=i.user_id and w.workspace_id=i.workspace_id"""

        cursor.execute(get_invite_id_sql, (username, workspace))
        invites = cursor.fetchone()
        if (invites is None):
            return 0

        invite_id = invites[0]
        user_id = invites[1]
        workspace_id = invites[2]

        if (decision == 'True'):
            insert_user_to_workspace_sql = """insert into workspace_users (user_id, workspace_id, is_admin)
                                        values(%s, %s, false)"""
            cursor.execute(insert_user_to_workspace_sql, (user_id, workspace_id))
            connection.commit()
            count = cursor.rowcount

            if (count == 0):
                return 0;

            delete_invite_sql = "delete from invites where invite_id=%s"
            cursor.execute(delete_invite_sql, (invite_id,))
            connection.commit()
            count = cursor.rowcount

        else:
            delete_invite_sql = "delete from invites where invite_id=%s"
            cursor.execute(delete_invite_sql, (invite_id,))
            connection.commit()
            count = cursor.rowcount


    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

    return count


def insert_user_invite(invite_json):
    username = invite_json['username']
    workspace = invite_json['workspace']
    invited_by = invite_json['invitedBy']

    loop = asyncio.new_event_loop()
    user_id = loop.run_until_complete(get_user_id(username))

    loop = asyncio.new_event_loop()
    invited_by_id = loop.run_until_complete(get_user_id(invited_by))

    loop = asyncio.new_event_loop()
    workspace_id = loop.run_until_complete(get_workspace_id(workspace))

    try:
        connection = psycopg2.connect(
            database="ssc")
        cursor = connection.cursor()

        is_inviter_admin_sql = """select * from workspace_users where user_id=%s and 
                                workspace_id=%s and is_admin=True"""

        cursor.execute(is_inviter_admin_sql, (invited_by_id, workspace_id))
        row = cursor.fetchone()

        if (row is None):
            return False

        insert_to_invites_sql = """insert into invites (user_id, workspace_id, invited_by_id)
                                                values(%s, %s, %s)"""
        cursor.execute(insert_to_invites_sql, (user_id, workspace_id, invited_by_id))
        connection.commit()
        count = cursor.rowcount

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        count = 0
    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
            if (count == 0): return False
            return True
        else:

            return False

