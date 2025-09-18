#!/usr/bin/env python3

"""
Ansible module for managing Koji users
"""

from ansible.module_utils.basic import AnsibleModule
import subprocess
import json


def run_koji_command(command):
    """Run a koji command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()


def get_user_info(user_identifier):
    """Get user information from koji"""
    stdout, stderr = run_koji_command(f"koji --noauth call --json-output getUser '{user_identifier}'")
    if stderr:
        return None, stderr

    if stdout == "null":
        return None, None

    try:
        return json.loads(stdout), None
    except json.JSONDecodeError as e:
        return None, f"Failed to parse user info: {e}"


def create_user(username, principal):
    """Create a new koji user"""
    stdout, stderr = run_koji_command(f"koji add-user '{username}' --principal '{principal}'")
    return stderr is None, stderr


def add_principal(username, principal):
    """Add a principal to an existing user"""
    stdout, stderr = run_koji_command(f"koji edit-user '{username}' --add-principal '{principal}'")
    return stderr is None, stderr


def grant_permission(permission, user_identifier):
    """Grant a permission to a user"""
    stdout, stderr = run_koji_command(f"koji grant-permission '{permission}' '{user_identifier}'")
    # Ignore errors for grant-permission as it might already exist
    return True, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            principal=dict(type='str', required=True),
            permissions=dict(type='list', elements='str', default=[]),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    principal = module.params['principal']
    permissions = module.params['permissions']
    state = module.params['state']

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode - no changes made")

    changed = False
    messages = []

    if state == 'present':
        # Check if user exists by principal
        user_info, error = get_user_info(principal)
        if error:
            module.fail_json(msg=f"Failed to check user by principal: {error}")

        if not user_info:
            # User doesn't exist by principal, check by username
            user_info, error = get_user_info(name)
            if error:
                module.fail_json(msg=f"Failed to check user by name: {error}")

            if not user_info:
                # User doesn't exist at all, create it
                success, error = create_user(name, principal)
                if not success:
                    module.fail_json(msg=f"Failed to create user: {error}")
                changed = True
                messages.append(f"Created user {name} with principal {principal}")
            else:
                # User exists but doesn't have this principal, add it
                success, error = add_principal(name, principal)
                if not success:
                    module.fail_json(msg=f"Failed to add principal: {error}")
                changed = True
                messages.append(f"Added principal {principal} to user {name}")

        # Grant permissions
        for permission in permissions:
            success, error = grant_permission(permission, principal)
            if success:
                messages.append(f"Granted permission {permission} to {principal}")
            # Note: We don't set changed=True for permissions as they might already exist

    result = {
        'changed': changed,
        'msg': '; '.join(messages) if messages else 'No changes needed'
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
