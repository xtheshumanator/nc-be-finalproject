create table users (
	user_id SERIAL PRIMARY KEY,
	username VARCHAR UNIQUE,
	password VARCHAR );

create table workspaces (
	workspace_id SERIAL PRIMARY KEY,
	name VARCHAR UNIQUE);

create table workspace_users (
	user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
	workspace_id INT REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
	is_admin BOOLEAN);

create table workspace_files (
	workspace_id INT REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
	file_name VARCHAR,
	audio_key VARCHAR);

create table invites (
	invite_id SERIAL PRIMARY KEY,
	user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
	workspace_id INT REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
	invited_by_id INT REFERENCES users(user_id) ON DELETE CASCADE);

create table audio_keys (
    audio_key VARCHAR NOT NULL,
    session_id VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW());
