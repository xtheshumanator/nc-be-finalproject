import asyncio
import base64
import os
import time

import boto3
import psycopg2
from cryptography.fernet import Fernet
from flask import send_file
from werkzeug import secure_filename

from flask import jsonify

from ssc.Utils.db_ops import get_workspace_id, get_user_id, is_user_admin
from ssc.dbconnection import getDBConnection


def delete_workspace(delete_request):
    workspace_deleted = False
    res = {}

    deleted_by = delete_request['deleted_by']
    workspace = delete_request['workspace']
    loop = asyncio.new_event_loop()
    workspace_id = loop.run_until_complete(get_workspace_id(workspace))

    loop = asyncio.new_event_loop()
    deleted_by_id = loop.run_until_complete(get_user_id(deleted_by))

    try:
        if (workspace_id == -1 | deleted_by_id == -1):
            res['error'] = 'Could not locate workspace or user deleting the workspace'
        else:
            connection = getDBConnection()
            cursor = connection.cursor()

            loop = asyncio.new_event_loop()
            admin_status = loop.run_until_complete(is_user_admin(deleted_by_id, workspace_id))

            if (admin_status == 0):
                res['error'] = 'User is not an admin of the workspace'
            else:
                delete_workspace_sql = "delete from workspaces where workspace_id=%s"
                cursor.execute(delete_workspace_sql, (workspace_id,))
                connection.commit()
                count = cursor.rowcount

                if (count != 0):
                    workspace_deleted = True

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        res['error'] = str(error)

    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

        res['workspace_deleted'] = workspace_deleted
        return res


def update_admin(workspace, admin_request):
    workspace_admin_updated = False
    res = {}

    username = admin_request['username']
    admin_username = admin_request['admin_username']
    make_admin = admin_request['make_admin']

    loop = asyncio.new_event_loop()
    workspace_id = loop.run_until_complete(get_workspace_id(workspace))

    loop = asyncio.new_event_loop()
    user_id = loop.run_until_complete(get_user_id(username))

    loop = asyncio.new_event_loop()
    admin_id = loop.run_until_complete(get_user_id(admin_username))

    try:

        if (workspace_id == -1 | admin_id == -1 | user_id == -1):
            res['error'] = 'Invalid input. Check username, admin and workspace are correct'
        else:
            connection = getDBConnection()
            cursor = connection.cursor()

            loop = asyncio.new_event_loop()
            admin_status = loop.run_until_complete(is_user_admin(admin_id, workspace_id))

            if (admin_status == 0):
                res['error'] = 'Admin is not actual admin of workspace'
            else:
                if (make_admin == 'True'):
                    make_admin_bool = True;
                else:
                    make_admin_bool = False;

                update_admin_sql = "update workspace_users set is_admin=%s where workspace_id=%s" \
                                   "and user_id=%s"
                cursor.execute(update_admin_sql, (make_admin_bool, workspace_id, user_id))
                connection.commit()
                count = cursor.rowcount
                if (count == 0):
                    res['error'] = 'Could not make user as admin'
                else:
                    workspace_admin_updated = True

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        res['error'] = str(error)

    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

        res['workspace_admin_updated'] = workspace_admin_updated
        return res


def create_workspace_only(data):
    res = {}
    workspace_added = False

    workspace_name = data['name']

    s3 = boto3.client('s3')
    s3.create_bucket(Bucket = '%s' % workspace_name)
    response = s3.list_buckets()
    buckets = [bucket['Name'] for bucket in response['Buckets']]


    try:
        admin = data['admin'];
        loop = asyncio.new_event_loop()
        admin_id = loop.run_until_complete(get_user_id(admin))

        if (admin_id == -1):

            res['error'] = 'Could not find user in the system so cannot add workspace for user'
        else:
            connection = getDBConnection()

            insert_workspace_name = "insert into workspaces (name) values (%s) returning workspace_id"

            cursor = connection.cursor()
            cursor.execute(insert_workspace_name, (workspace_name,))

            connection.commit()
            count = cursor.rowcount
            if (count == 0):
                res['error'] = 'Could not add workspace into the system'
            else:
                new_workspace_id = cursor.fetchone()[0]
                admin_added = add_user_to_workspace([admin_id], new_workspace_id, True)

                if (admin_added != 0):
                    workspace_added = True

                else:
                    res['error'] = 'Workspace created but could not set admin. Contact support'

    except (Exception, psycopg2.Error) as error:
        print('Error while conecting to PostgresQL', error)
        res['error'] = str(error)
    finally:

        if (connection):
            # close the connection and the cursor
            cursor.close()
            connection.close()
            print("PostgresSQL connection is closed")

        res['workspace_added'] = workspace_added

        return res


def create_workspace_with_users(data):
    users = data['users'];
    admin = data['admin'];
    workspace = data['name'];

    res = {}
    users_added = False

    try:
        connection = getDBConnection()

        cursor = connection.cursor()

        insert_workspace_sql = "insert into workspaces (name) values (%s) " \
                               "returning workspace_id"
        cursor.execute(insert_workspace_sql, (workspace,))

        connection.commit()

        count = cursor.rowcount
        if (count == 0):
            res['error'] = 'Could not create the workspace'
        else:
            new_workspace_id = cursor.fetchone()[0]
            loop = asyncio.new_event_loop()
            admin_id = loop.run_until_complete(get_user_id(admin))
            admin_added = add_user_to_workspace([admin_id], new_workspace_id, True);
            if (admin_added == 0):
                res['error'] = 'Workspace added but could not set admin to workspace.'
            else:
                user_id_list = []
                for user in users:
                    loop = asyncio.new_event_loop()
                    single_user_id = loop.run_until_complete(get_user_id(user['username']))
                    user_id_list.append(single_user_id)
                users_added = add_user_to_workspace(user_id_list, new_workspace_id);

                if (users_added != len(users)):
                    res['error'] = 'Some users could not be added to workspace. Try again'
                else:
                    users_added = True

    except (Exception, psycopg2.Error) as error:
        print('Error while conecting to PostgresQL', error)
        res['error'] = str(error)
    finally:
        if (connection):
            # close the connection and the cursor
            cursor.close()
            connection.close()
            print("PostgresSQL connection is closed")

        res['users_added'] = users_added
        return res


def add_user_to_workspace(list_of_ids, workspace_id, is_admin = False):
    try:
        connection = getDBConnection()

        cursor = connection.cursor()
        insert_user_to_workspace_sql = "insert into workspace_users (user_id, workspace_id, is_admin) " \
                                       "values (%s,%s,%s) returning user_id"

        count = 0
        for user_id in list_of_ids:
            if (user_id != -1):
                cursor.execute(insert_user_to_workspace_sql, (user_id, workspace_id, is_admin))
                connection.commit()
                count += cursor.rowcount

    except (Exception, psycopg2.Error) as error:
        print('Error while connecting to PostgresQL', error)
        return 0
    finally:
        if (connection):
            # close the connection and the cursor
            cursor.close()
            connection.close()
            print("PostgresSQL connection is closed")

    return 'workspace added'

    return count


def delete_user_from_workspace(data):
    res = {}
    user_deleted = False

    try:
        # check if admin_username is the same as the workspace_admins
        username = data['username']
        admin_username = data['admin_username']
        workspace_name = data['workspace_name']

        connection = getDBConnection()

        cursor = connection.cursor()
        select_user = "select user_id from users where username = (%s)"
        cursor.execute(select_user, [username])
        user_id = cursor.fetchone()
        count = cursor.rowcount
        if (count == 0):
            res["error"] = "User does not exist in the system"
        else:
            cursor.execute(select_user, [admin_username])
            admin_id = cursor.fetchone()
            count = cursor.rowcount
            if (count == 0):
                res["error"] = "Admin does not exist in the system"
            else:
                select_workspace_id = "select workspace_id from workspaces where name = (%s)"
                cursor.execute(select_workspace_id, [workspace_name])
                workspace_id = cursor.fetchone()
                count = cursor.rowcount
                if (count == 0):
                    res["error"] = "Workspace does not exist in the system"

                else:
                    select_admin_boolean = "select is_admin from workspace_users where user_id = (%s) and workspace_id = (%s)"
                    cursor.execute(select_admin_boolean, (admin_id, workspace_id))
                    admin_boolean = cursor.fetchone()
                    count = cursor.rowcount
                    if (count == 0) | (not admin_boolean):
                        res["error"] = "Given admin is not actual admin of workspace"
                    else:
                        delete_user = "delete from workspace_users where user_id =(%s) and workspace_id = (%s)"
                        cursor.execute(delete_user, (user_id, workspace_id))
                        connection.commit()
                        count = cursor.rowcount
                        if (count != 0):
                            user_deleted = True
                        else:
                            res["error"] = "Could not remove user from workspace"


    except (Exception, psycopg2.Error) as error:
        print('Error while conecting to PostgresQL', error)

        res['error'] = str(error)

    finally:

        if (connection):
            # close the connection and the cursor
            cursor.close()
            connection.close()
            print("PostgresSQL connection is closed")
        res["user_deleted_from_workspace"] = user_deleted
        return res


def encrypt_file(f, bucket_name, audio_key):

    f.save(secure_filename(f.filename))
    s3 = boto3.client('s3')
    key_string = bytes(audio_key, 'utf-8')
    encoded_key = base64.b64encode(key_string)
    res = {}

    try:
        # convert key from 56 into 64

        key = encoded_key

        connection = getDBConnection()
        cursor = connection.cursor()
        actualFile = secure_filename(f.filename)
        time_stamp = str(time.time())
        file_start = str(secure_filename(f.filename))[0:-4]
        file_end = str(secure_filename(f.filename))[-4:]

        filename = (file_start + '-' + time_stamp + '-' + file_end)


        with open(actualFile, 'rb') as f:
            file = f.read()

            fernet = Fernet(key)
            encrypted = fernet.encrypt(file)

        with open(filename, 'wb') as f:
            f.write(encrypted)

        s3.upload_file(filename, bucket_name, filename)

        loop = asyncio.new_event_loop()
        workspace_id = loop.run_until_complete(get_workspace_id(bucket_name))
        if (workspace_id == -1):
            res["error"] = "Workspace name is invalid"

        else:
            add_file_to_workspace = "INSERT INTO workspace_files (workspace_id, file_name) " \
                                    "VALUES (%s, %s) RETURNING *; "

            cursor.execute(add_file_to_workspace, (workspace_id, filename))
            connection.commit()
            # if cursor.rowcount == 0:
            #     res["error"] = ""

    except (Exception, psycopg2.Error) as error:
        print('Error while connecting to PostgresQL', error)

    finally:
        os.remove(filename)
        os.remove(actualFile)

        if (connection):
            # close the connection and the cursor
            cursor.close()
            connection.close()
            print("PostgresSQL connection is closed")

        return 'encrypted'


def decrypt_file(workspace_name, filename, audio_key):
    s3 = boto3.resource('s3')
    time_stamp = str(time.time())
    split = filename.split('-')
    altered_filename = split[0] + time_stamp + split[2]
    altered = str(split[0] + time_stamp + 'decrypted' + split[2])
    key_string = bytes(audio_key, 'utf-8')
    encoded_key = base64.b64encode(key_string)

    try:

        s3.Bucket(workspace_name).download_file(filename, altered_filename)

        connection = getDBConnection()

        key = encoded_key
        cursor = connection.cursor()

        with open(altered_filename, 'rb') as f:
            file = f.read()
            fernet = Fernet(key)
            decrypted = fernet.decrypt(file)

        with open(altered, 'wb') as f:
            print(f.write(decrypted))

        if os.path.exists(altered_filename):
            os.remove(altered_filename)
    except (Exception, psycopg2.Error) as error:
        print('Error while connecting to PostgresQL', error)
    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgresSQL connection is closed")
        if(altered == None):
            return jsonify({"incorrect_key": True})
        else:
            to_send = send_file(altered)
            os.remove(altered)
            return to_send


def fetch_workspace_users(name):
    list_of_users = []
    res = {}

    try:
        connection = getDBConnection()

        cursor = connection.cursor()
        if (name == None):
            res["error"] = "Workspace name is invalid"
        else:
            loop = asyncio.new_event_loop()
            workspace_id = loop.run_until_complete(get_workspace_id(name))
            if (workspace_id == -1):
                res["error"] = "Workspace name is invalid"
            else:
                cursor.execute("""SELECT u.username, wu.is_admin FROM workspace_users wu 
                       INNER JOIN workspaces w ON w.workspace_id = wu.workspace_id
                       INNER JOIN users u ON wu.user_id=u.user_id
                       WHERE w.workspace_id = %s
                       """, (workspace_id,))

                workspace_users = cursor.fetchall()
                for row in workspace_users:
                    list_of_users.append(
                        {'username': row[0], 'is_admin': str(row[1])})

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        res["error"] = str(error)
    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        if ((len(list_of_users) == 0) & ("error" not in res)):
            res["error"] = "There are no users in this workspace"
        res["users"] = list_of_users
        return res


def fetch_workspace_files(name):
    list_of_files = []
    res = {}

    try:
        connection = getDBConnection()

        cursor = connection.cursor()
        if (name == None):
            res["error"] = "Workspace name is invalid"
        else:
            loop = asyncio.new_event_loop()
            workspace_id = loop.run_until_complete(get_workspace_id(name))
            if (workspace_id == -1):
                res["error"] = "Workspace name is invalid"
            else:
                cursor.execute("""SELECT file_name FROM workspace_files
                       INNER JOIN workspaces ON workspaces.workspace_id = workspace_files.workspace_id
                       WHERE workspaces.workspace_id = %s
                       """, (workspace_id,))

                workspace_files = cursor.fetchall()

                for row in workspace_files:
                    list_of_files.append(
                        {'file_name': row[0]})

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        res["error"] = str(error)
    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
        if ((len(list_of_files) == 0) & ("error" not in res)):
            res["error"] = "There are no files in this workspace"
        res["files"] = list_of_files
        return res
