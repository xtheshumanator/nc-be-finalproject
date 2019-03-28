api_info = {
    "Login: /api/login": {
        "POST": "Logs the user in if the username and password match"
    },
    "Users: /api/users": {
        "GET": "Returns all users in the system",
        "POST": "Creates a new user into the system"
    },
    "User workspaces: /api/users/<username>": {
        "GET": "Returns all workspaces user belongs to including flag to indicate workspace user is admin of"
    },
    "Delete user from workspace: /api/deleteUser": {
        "DELETE": "Given a user, admin_user and workspace, deletes the user from workspace"
    },
    "Invites: /api/invites": {
        "POST": "Given a user, admin and workspace, invites the user to workspace"
    },
    "Invites for user: /api/invites/<username>": {
        "GET": "Returns all pending invites for user",
        "POST": "Takes accept true/false and adds user to workspace accordingly"
    },
    "Workspaces: /api/workspaces": {
        "POST": "Creates a new workspace, adds creator as admin and creates bucket in S3",
        "DELETE": "Deletes the workspace from the system and S3"
    },
    "Workspaces: /api/workspaces/<workspace_name>": {
        "PUT": "Given a user, an admin and a make_admin flag, it makes the user an admin or removes from admin",
    },
    "Workspace files: /api/workspaces/<workspace_name>/files": {
        "GET": "Returns files in a workspace"
    },
    "Workspace users: /api/workspaces/<workspace_name>/users": {
        "GET": "Returns users in a workspace"
    },
    "Generate encryption key: /api/audiokey": {
        "POST": "Given an audio file/recording and session id,  it generates an encryption key based on audio"
    },
    "Encrypt File: /api/encryptFile": {
        "POST": "Given a file to encrypt, workspace/bucket and session id, it encrypts a file using a previously generated audio via /api/audiokey and saves it on S3"
    },
    "Decrypt File: /api/decryptFile/<workspace_name>/<file>": {
        "POST": "Given an audio file/recording, file to decrypt and workspace, it uses the audio to generate the decryption key then downloads the encrypted file from S3, decrypts it and sends it back to front end to download"
    }
}
