import os

from flask import Flask, jsonify, request, abort

from ssc.Invites.invites import fetch_user_invites, process_invite, insert_user_invite

from ssc.Workspaces.workspaces import delete_workspace, update_admin, \
    create_workspace_with_users, create_workspace_only, fetch_workspace_files, \
    delete_user_from_workspace

from ssc.Users.users import fetch_users, add_user, fetch_user_workspaces

from ssc.login.get_logged_in import fetch_user_details

from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='testflask/templates')

@app.route("/")
def homeDummy():
    return 'Hello'


@app.route("/api/audio", methods=['POST'])
def handle_audio():
    # target = os.path.join(UPLOAD_FOLDER, 'test_docs')
    # if not os.path.isdir(target):
    #     os.mkdir(target)
    print('In handle audio')
    file = request.files['file']
    print(file)
    # print(open(file, 'rb'))
    print(file.filename)
    filename = secure_filename(file.filename)

    # destination = "/".join([target, filename])
    # file.save(destination)
    # session['uploadFilePath'] = destination
    response = "Whatever you wish too return"
    return jsonify(response)


@app.route('/api/login', methods=['GET'])
def login():
    username = request.json['username']
    password = request.json['password']
    res = fetch_user_details(username, password)
    res_json = jsonify(res)

    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200


@app.route("/api/users")
def get_users():
    res = fetch_users()
    res_json = jsonify(res)

    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200


@app.route("/api/users", methods=['POST'])
def post_user():
    username = request.json['username']
    password = request.json['password']
    res = add_user(username, password)
    res_json = jsonify(res)
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 201


@app.route('/api/users/<username>', methods=["GET"])
def get_user_workspaces(username):
    res = fetch_user_workspaces(username)
    res_json = jsonify(res)

    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200


@app.route("/api/deleteUser", methods=['DELETE'])
def delete_user():
    if (not request.json) | ('username' not in request.json) | ('admin_username' not in request.json) | (
            'workspace_name' not in request.json):
        abort(400)

    res = delete_user_from_workspace(request.json)
    res_json = jsonify(res)
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200



@app.route("/api/invites", methods=["POST"])
def invite_user():
    if (not request.json) | ('username' not in request.json) \
            | ('workspace' not in request.json) | ('invitedBy' not in request.json):
        abort(400)

    res = insert_user_invite(request.json)
    res_json = jsonify(res)
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200


@app.route("/api/invites/<username>", methods=["GET"])
def get_user_invites(username):
    res = fetch_user_invites(username)
    res_json = jsonify(res)
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200

@app.route("/api/invites/<username>", methods=["POST"])
def update_invite(username):
    if (not request.json) | ('accept' not in request.json) | ('workspace' not in request.json):
        abort(400)

    res = process_invite(username, request.json)
    res_json = jsonify(res);
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200


# TODO

@app.route('/api/workspaces', methods=['POST'])
def handle_create_workspace():
    if (not request.json) | ('name' not in request.json) | ('admin' not in request.json):
        abort(400)
    else:
        if ('users' in request.json):
            res = create_workspace_with_users(request.json)
            if (res == len(request.json['users'])):
                res_json = {'workspace_added': True}
            elif (res != 0):
                res_json = {'workspace_added': False,
                            'error': 'Workspace added but not all users added.'}
            else:
                res_json = {'workspace_added': False,
                            'error': 'Workspace could not be added.'}
        else:
            res = create_workspace_only(request.json)
            if (res):
                res_json = {'workspace_added': True}
            else:
                res_json = {'workspace_added': False,
                            'error': 'Could not add workspace or set admin.'}

        return jsonify(res_json);


@app.route("/api/workspaces", methods=["DELETE"])
def handle_delete_workspace():
    if (not request.json) | ('workspace' not in request.json) | ('deleted_by' not in request.json):
        abort(400)

    res = delete_workspace(request.json)
    res_json = {'workspace_deleted': res}
    if (res == False): res_json['error'] = 'Could not delete workspace. ' \
                                           'Check user is admin or workspace still exists'
    return jsonify(res_json);


@app.route("/api/workspaces/<name>", methods=["GET"])
def get_workspace_file(name):
    list_of_files = fetch_workspace_files(name)
    res = {'files': list_of_files}
    return jsonify(res);


@app.route("/api/workspaces/<workspace_name>", methods=["PUT"])
def handle_update_workspace(workspace_name):
    if (not request.json) | ('username' not in request.json) \
            | ('admin_username' not in request.json) | ('make_admin' not in request.json):
        abort(400)

    res = update_admin(workspace_name, request.json)
    print(res)
    res_json = {'workspace_admin_updated': res}
    if (res == False): res_json['error'] = 'Could not update workspace. ' \
                                           'Check admin user is an admin'

    return jsonify(res_json);


if __name__ == "__main__":
    # app.run(debug=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
