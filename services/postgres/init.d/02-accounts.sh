#! /bin/bash

KRB5_REALM=${KRB5_REALM:-KOJI.BOX}
KOJI_ADMIN_NAME=${KOJI_ADMIN_NAME:-hub-admin}
KOJI_ADMIN_PRINC=${KOJI_ADMIN_PRINC:-${KOJI_ADMIN_NAME}@${KRB5_REALM}}

echo "Creating user ${KOJI_ADMIN_NAME} (${KOJI_ADMIN_PRINC}) and granting admin permissions"
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} << EOF
insert into users (name, usertype, status) values ('${KOJI_ADMIN_NAME}', 0, 0);
insert into user_krb_principals (user_id, krb_principal)
      select users.id, '${KOJI_ADMIN_PRINC}' from users
      where users.name = '${KOJI_ADMIN_NAME}';
insert into user_perms (user_id, perm_id, creator_id)
      select users.id, permissions.id, users.id from users, permissions
      where users.name = '${KOJI_ADMIN_NAME}'
            and permissions.name = 'admin';
EOF

# The end.
