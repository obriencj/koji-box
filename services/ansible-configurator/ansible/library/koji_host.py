#!/usr/bin/env python3

"""
Ansible module for managing Koji hosts
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


def get_host_info(hostname):
    """Get host information from koji"""
    stdout, stderr = run_koji_command(f"koji --noauth call --json-output getHost '{hostname}'")
    if stderr:
        return None, stderr

    if stdout == "null":
        return None, None

    try:
        return json.loads(stdout), None
    except json.JSONDecodeError as e:
        return None, f"Failed to parse host info: {e}"


def add_host(hostname, arches, capacity=1.0):
    """Add a new koji host"""
    arch_str = " ".join(arches)
    stdout, stderr = run_koji_command(f"koji add-host '{hostname}' '{arch_str}' --capacity={capacity}")
    return stderr is None, stderr


def edit_host(hostname, arches=None, capacity=None, enabled=None):
    """Edit an existing koji host"""
    commands = []

    if arches:
        arch_str = " ".join(arches)
        commands.append(f"koji edit-host '{hostname}' --arches='{arch_str}'")

    if capacity is not None:
        commands.append(f"koji edit-host '{hostname}' --capacity={capacity}")

    if enabled is not None:
        action = "enable-host" if enabled else "disable-host"
        commands.append(f"koji {action} '{hostname}'")

    for command in commands:
        stdout, stderr = run_koji_command(command)
        if stderr:
            return False, stderr

    return True, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            arches=dict(type='list', elements='str', default=['x86_64', 'noarch']),
            capacity=dict(type='float', default=1.0),
            enabled=dict(type='bool', default=True),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    arches = module.params['arches']
    capacity = module.params['capacity']
    enabled = module.params['enabled']
    state = module.params['state']

    if module.check_mode:
        module.exit_json(changed=False, msg="Check mode - no changes made")

    changed = False
    messages = []

    if state == 'present':
        # Check if host exists
        host_info, error = get_host_info(name)
        if error:
            module.fail_json(msg=f"Failed to check host: {error}")

        if not host_info:
            # Host doesn't exist, create it
            success, error = add_host(name, arches, capacity)
            if not success:
                module.fail_json(msg=f"Failed to add host: {error}")
            changed = True
            messages.append(f"Added host {name}")

            # Enable/disable as needed
            if not enabled:
                success, error = edit_host(name, enabled=enabled)
                if not success:
                    module.fail_json(msg=f"Failed to disable host: {error}")
                messages.append(f"Disabled host {name}")
        else:
            # Host exists, check if we need to update it
            current_arches = set(host_info.get('arches', '').split())
            desired_arches = set(arches)
            current_capacity = float(host_info.get('capacity', 1.0))
            current_enabled = bool(host_info.get('enabled', True))

            needs_update = False
            update_arches = None
            update_capacity = None
            update_enabled = None

            if current_arches != desired_arches:
                needs_update = True
                update_arches = arches
                messages.append(f"Updated arches for {name}: {' '.join(arches)}")

            if abs(current_capacity - capacity) > 0.01:  # Float comparison
                needs_update = True
                update_capacity = capacity
                messages.append(f"Updated capacity for {name}: {capacity}")

            if current_enabled != enabled:
                needs_update = True
                update_enabled = enabled
                status = "enabled" if enabled else "disabled"
                messages.append(f"Host {name} {status}")

            if needs_update:
                success, error = edit_host(name, update_arches, update_capacity, update_enabled)
                if not success:
                    module.fail_json(msg=f"Failed to update host: {error}")
                changed = True

    result = {
        'changed': changed,
        'msg': '; '.join(messages) if messages else 'Host is up to date'
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
