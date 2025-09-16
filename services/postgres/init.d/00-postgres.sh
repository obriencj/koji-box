#! /bin/bash

psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} << EOF

CREATE ROLE healthcheck WITH LOGIN;
GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO healthcheck;

ALTER SYSTEM SET max_connections TO ${DB_MAX_CONNECTIONS:-200};
ALTER SYSTEM SET idle_in_transaction_session_timeout TO '${DB_IDLE_IN_TRANSACTION_SESSION_TIMEOUT:-10min}';
ALTER SYSTEM SET idle_session_timeout TO '${DB_IDLE_SESSION_TIMEOUT:-0}';
SELECT pg_reload_conf();

EOF

# The end.
