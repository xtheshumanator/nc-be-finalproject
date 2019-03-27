from io import BytesIO

from flask import Flask, jsonify, request, abort
from flask_cors import CORS

from ssc.Invites.invites import fetch_user_invites, process_invite, insert_user_invite
from ssc.Users.users import fetch_users, add_user, fetch_user_workspaces
from ssc.Workspaces.workspaces import *
from ssc.audio_analysis.acr_api_requests import identify_audio, upload_audio
from ssc.audiokey_api.audiokey import add_audio_key
from ssc.audiokey_api.audiokey import get_audio_key
from ssc.login.get_logged_in import fetch_user_details
from ssc.Utils.info import api_info


app = Flask(__name__)
CORS(app)


@app.route("/")
def homeDummy():
    return 'Hello'

@app.route("/api")
def getApiInfo():
    return jsonify(api_info)


@app.route("/api/encryptFile", methods = ['POST'])
def post_encrypted_file():
    key = get_audio_key(request.form["session_id"])
    if ("error" in key):
        return jsonify(key), 404
    return encrypt_file(request.files['file'], request.form['bucket_name'], key)


@app.route("/api/decryptFile/<workspace_name>/<file>", methods = ['GET', 'POST'])
def download_decrypted_file(workspace_name, file):
    if (not request.files):
        abort(400)

    audio_file = request.files["file"].read()
    audio_file_bytes = BytesIO(audio_file)
    sample_bytes = len(file)
    acr_response = identify_audio(audio_file_bytes, sample_bytes)

    if acr_response["status"]["msg"] == 'No result':
        abort(404)
    else:
        audio_key = acr_response["metadata"]["music"][0]["acrid"]
        return decrypt_file(workspace_name, file, audio_key)


@app.route('/api/login', methods = ['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    res = fetch_user_details(username, password)
    res_json = jsonify(res)

    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200


@app.route("/api/users", methods = ['GET'])
def get_users():
    res = fetch_users()
    res_json = jsonify(res)

    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200


@app.route("/api/users", methods = ['POST'])
def post_user():
    username = request.json['username']
    password = request.json['password']
    res = add_user(username, password)
    res_json = jsonify(res)
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 201


@app.route('/api/users/<username>', methods = ["GET"])
def get_user_workspaces(username):
    res = fetch_user_workspaces(username)
    res_json = jsonify(res)
    return res_json, 200


@app.route("/api/deleteUser", methods = ['DELETE'])
def delete_user():
    if (not request.json) | ('username' not in request.json) | ('admin_username' not in request.json) | (
            'workspace_name' not in request.json):
        abort(400)

    res = delete_user_from_workspace(request.json)
    res_json = jsonify(res)
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 204


@app.route("/api/invites", methods = ["POST"])
def invite_user():
    if (not request.json) | ('username' not in request.json) \
            | ('workspace' not in request.json) | ('invitedBy' not in request.json):
        abort(400)

    res = insert_user_invite(request.json)
    res_json = jsonify(res)
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 201


@app.route("/api/invites/<username>", methods = ["GET"])
def get_user_invites(username):
    res = fetch_user_invites(username)
    res_json = jsonify(res)
    return res_json, 200


@app.route("/api/invites/<username>", methods = ["POST"])
def update_invite(username):
    if (not request.json) | ('accept' not in request.json) | ('workspace' not in request.json):
        abort(400)

    res = process_invite(username, request.json)
    res_json = jsonify(res);
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 201


@app.route('/api/workspaces', methods = ['POST'])
def handle_create_workspace():
    if (not request.json) | ('name' not in request.json) | ('admin' not in request.json):
        abort(400)
    else:
        if ('users' in request.json):
            res = create_workspace_with_users(request.json)
        else:
            res = create_workspace_only(request.json)
        print(res)
        res_json = jsonify(res);
        if ("error" in res):
            return res_json, 404
        else:
            return res_json, 201
        return jsonify(res_json);


@app.route("/api/workspaces", methods = ["DELETE"])
def handle_delete_workspace():
    if (not request.json) | ('workspace' not in request.json) | ('deleted_by' not in request.json):
        abort(400)

    res = delete_workspace(request.json)
    res_json = jsonify(res)
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 204


@app.route("/api/workspaces/<name>/files", methods = ["GET"])
def get_workspace_file(name):
    res = fetch_workspace_files(name)
    res_json = jsonify(res)
    return res_json, 200


@app.route("/api/workspaces/<name>/users", methods = ["GET"])
def get_workspace_users(name):
    res = fetch_workspace_users(name)
    res_json = jsonify(res);
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 200


@app.route("/api/workspaces/<workspace_name>", methods = ["PUT"])
def handle_update_workspace(workspace_name):
    if (not request.json) | ('username' not in request.json) \
            | ('admin_username' not in request.json) | ('make_admin' not in request.json):
        abort(400)

    res = update_admin(workspace_name, request.json)
    res_json = jsonify(res);
    if ("error" in res):
        return res_json, 404
    else:
        return res_json, 201
    print(res)
    res_json = {'workspace_admin_updated': res}
    if (res == False): res_json['error'] = 'Could not update workspace. ' \
                                           'Check admin user is an admin'

    return jsonify(res_json);


@app.route("/api/audiokey", methods = ["POST"])
def post_audio_key():
    if (not request.files) | ("session_id" not in request.values) | ("filename" not in request.values):
        abort(400)

    file = request.files["file"].read()
    audio_file_copy1 = BytesIO(file)
    audio_file_copy2 = BytesIO(file)
    sample_bytes = len(file)
    session_id = request.values.get("session_id")
    file_name = request.values.get("filename")
    acr_response = identify_audio(audio_file_copy1, sample_bytes)
    if acr_response["status"]["msg"] == 'No result' and ("isRecorded" in request.values):
        return jsonify({"recordedNotRecognised": True})
    if acr_response["status"]["msg"] == 'No result':
        acr_upload_response = upload_audio(audio_file_copy2, file_name, session_id)
        add_audio_key(acr_upload_response["acr_id"], session_id)
        return jsonify({"notRecognised": True})
    if 'custom_files' in acr_response["metadata"].keys():
        return jsonify({"fileError": True})
    if acr_response["status"]["msg"] == 'Success':
        add_audio_key(acr_response["metadata"]["music"][0]["acrid"], session_id)
        return jsonify({"title": acr_response["metadata"]["music"][0]["title"],
                        "artist": acr_response["metadata"]["music"][0]["artists"][0]["name"]})

    return jsonify('Error check')


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 9090))
    app.run(host = '0.0.0.0', port = port)
