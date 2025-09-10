#!/bin/bash
# Database initialization script for Koji

set -e

echo "Initializing Koji database..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h postgres -p 5432 -U koji; do
    echo "PostgreSQL not ready, waiting..."
    sleep 2
done

echo "PostgreSQL is ready"

# Create database schema
echo "Creating database schema..."

# Connect to PostgreSQL and create the schema
psql -h postgres -U koji -d koji << 'EOF'
-- Create Koji database schema
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
    krb_principal_expires TIMESTAMP,
    krb_principal_updated TIMESTAMP,
    krb_principal_created TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_perms (
    user_id INTEGER NOT NULL REFERENCES users(id),
    perm_id INTEGER NOT NULL,
    creator_id INTEGER NOT NULL REFERENCES users(id),
    create_event INTEGER NOT NULL,
    revoke_event INTEGER,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (perm_id) REFERENCES permissions(id),
    FOREIGN KEY (creator_id) REFERENCES users(id),
    FOREIGN KEY (create_event) REFERENCES events(id),
    FOREIGN KEY (revoke_event) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    time TIMESTAMP NOT NULL,
    user_id INTEGER REFERENCES users(id)
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

-- Grant admin permission to admin user
INSERT INTO user_perms (user_id, perm_id, creator_id, create_event)
SELECT u.id, p.id, u.id, 1
FROM users u, permissions p
WHERE u.name = 'admin' AND p.name = 'admin'
ON CONFLICT DO NOTHING;

COMMIT;
EOF

echo "Database schema created successfully"
