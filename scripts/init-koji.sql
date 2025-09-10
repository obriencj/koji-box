-- Koji Database Initialization Script
-- This script creates the basic Koji database schema

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,
    usertype INTEGER NOT NULL DEFAULT 0,
    krb_principal VARCHAR(128),
    krb_principal_created TIMESTAMP,
    krb_principal_updated TIMESTAMP,
    password VARCHAR(128),
    status_change_time TIMESTAMP,
    status_change_message TEXT,
    status_change_user_id INTEGER,
    status_change_comment TEXT,
    krb_principal_expires TIMESTAMP
);

-- Create permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id)
);

-- Create user_perms table
CREATE TABLE IF NOT EXISTS user_perms (
    user_id INTEGER NOT NULL REFERENCES users(id),
    perm_id INTEGER NOT NULL REFERENCES permissions(id),
    creator_id INTEGER NOT NULL REFERENCES users(id),
    create_event INTEGER NOT NULL REFERENCES events(id),
    revoke_event INTEGER REFERENCES events(id),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (user_id, perm_id, create_event)
);

-- Create tags table
CREATE TABLE IF NOT EXISTS tag (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES tag(id),
    arches VARCHAR(128),
    locked BOOLEAN NOT NULL DEFAULT FALSE,
    maven_support BOOLEAN NOT NULL DEFAULT FALSE,
    maven_include_all BOOLEAN NOT NULL DEFAULT FALSE,
    extra TEXT
);

-- Create tag_inheritance table
CREATE TABLE IF NOT EXISTS tag_inheritance (
    tag_id INTEGER NOT NULL REFERENCES tag(id),
    parent_id INTEGER NOT NULL REFERENCES tag(id),
    priority INTEGER NOT NULL DEFAULT 0,
    noconfig BOOLEAN NOT NULL DEFAULT FALSE,
    maxdepth INTEGER,
    pkg_filter TEXT,
    intransitive BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (tag_id, parent_id, priority)
);

-- Create build table
CREATE TABLE IF NOT EXISTS build (
    id SERIAL PRIMARY KEY,
    pkg_id INTEGER NOT NULL,
    version VARCHAR(128) NOT NULL,
    release VARCHAR(128) NOT NULL,
    epoch INTEGER,
    state INTEGER NOT NULL,
    task_id INTEGER,
    owner INTEGER NOT NULL REFERENCES users(id),
    volume_id INTEGER,
    creation_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creation_event_id INTEGER NOT NULL REFERENCES events(id),
    start_time TIMESTAMP,
    completion_time TIMESTAMP,
    source TEXT,
    extra TEXT
);

-- Create package table
CREATE TABLE IF NOT EXISTS package (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    extra TEXT
);

-- Insert default permissions
INSERT INTO permissions (name) VALUES
    ('admin'),
    ('build'),
    ('repo'),
    ('sign'),
    ('cancel')
ON CONFLICT (name) DO NOTHING;

-- Insert default admin user
INSERT INTO users (name, status, usertype) VALUES
    ('admin', 0, 0)
ON CONFLICT (name) DO NOTHING;

-- Create initial event
INSERT INTO events (time, user_id) VALUES
    (CURRENT_TIMESTAMP, (SELECT id FROM users WHERE name = 'admin'));

-- Grant admin permission to admin user
INSERT INTO user_perms (user_id, perm_id, creator_id, create_event)
SELECT u.id, p.id, u.id, 1
FROM users u, permissions p
WHERE u.name = 'admin' AND p.name = 'admin'
ON CONFLICT DO NOTHING;

-- Create default tags
INSERT INTO tag (name, arches) VALUES
    ('dist-foo', 'x86_64'),
    ('dist-foo-build', 'x86_64')
ON CONFLICT (name) DO NOTHING;

-- Set up tag inheritance
INSERT INTO tag_inheritance (tag_id, parent_id, priority)
SELECT child.id, parent.id, 0
FROM tag child, tag parent
WHERE child.name = 'dist-foo-build' AND parent.name = 'dist-foo'
ON CONFLICT DO NOTHING;

COMMIT;
