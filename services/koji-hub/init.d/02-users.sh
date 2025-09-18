#! /bin/bash

function ensure_user_principal() {
    local principal=${1}
    local username=${principal%%@*}
    shift

    if [[ -z "${username}" ]] ; then
        echo "ERROR: Invalid principal ${principal}"
        return 1
    else
        if [[ -z "$@" ]]; then
            echo "Ensuring user ${username} with principal ${principal}"
        else
            echo "Ensuring user ${username} with principal ${principal} and permissions: ${@}"
        fi
    fi

    local userinfo=$(koji --noauth call --json-output getUser "${principal}")
    if [ "$userinfo" == "null" ] ; then
        echo "User ${principal} not found, checking for user ${username}"
        userinfo=$(koji --noauth call --json-output getUser "${username}")
        if [ "$userinfo" == "null" ] ; then
            echo "Creating user ${username} with principal ${principal}"
            koji add-user ${username} --principal ${principal}
        else
            echo "Editing user ${username} to add principal ${principal}"
            koji edit-user ${username} --add-principal ${principal}
        fi
    fi

    userinfo=$(koji --noauth call --json-output getUser "${principal}")
    if [ "$userinfo" == "null" ] ; then
        echo "Failed to ensure user ${principal}"
        return 1
    fi

    for perm in "$@" ; do
        koji grant-permission ${perm} ${principal} >/dev/null 2>&1
    done

    koji userinfo ${principal}
}

ensure_user_principal "${KOJI_CLIENT_PRINC}" tag target dist-repo maven-import
ensure_user_principal "${KOJI_CLIENT_ADMIN_PRINC}" admin
ensure_user_principal "${ORCH_PRINC}" admin host
ensure_user_principal "${ANSIBLE_PRINC}" admin


# The end.
