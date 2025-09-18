# Koji Data Configuration

This directory contains YAML data files for configuring your Koji instance. All infrastructure and orchestration logic is built into the `ansible-configurator` service - you only need to define your Koji data here.

## Overview

The `ansible-configurator` service runs as a separate container that configures your Koji instance after it starts up. This approach allows you to:

- **Declaratively define** your Koji data in simple YAML files
- **Version control** your Koji setup alongside your code
- **Reset state** easily by rerunning the configuration
- **Focus on data** without worrying about infrastructure complexity

## Quick Start

1. **Edit the data files** in this directory to match your needs
2. **Validate your configuration**: `make validate-ansible`
3. **Start your Koji environment**: `make up`
4. **Run the Ansible configuration**: `make configure`

## Data Files

This directory contains **only data files** - all Ansible infrastructure is built into the container:

- **`users.yml`** - Define Koji users and their permissions
- **`hosts.yml`** - Define build hosts and their capabilities
- **`tags.yml`** - Define package tags and inheritance
- **`targets.yml`** - Define build targets

## Usage Commands

### Basic Operations

```bash
# Validate configuration files (recommended first step)
make validate-ansible

# Run Ansible configuration (first time or after changes)
make configure

# Check what would change without applying (dry-run)
make configure-check

# Force reconfiguration (removes and recreates container)
make reconfigure

# View Ansible logs
make logs-ansible

# Get interactive shell for debugging
make ansible-shell
```

### Integration with Koji Boxed

```bash
# Start everything and configure
make up
make configure

# Quick restart with reconfiguration
make restart
make reconfigure
```

## Configuration Examples

### Adding Users

Edit `users.yml`:

```yaml
- name: "myuser"
  principal: "myuser@KOJI.BOX"
  permissions:
    - "tag"
    - "target"
  state: "present"
```

### Adding Build Hosts

Edit `hosts.yml`:

```yaml
- name: "builder03.koji.box"
  arches:
    - "x86_64"
    - "aarch64"
    - "noarch"
  capacity: 8.0
  enabled: true
  state: "present"
```

### Adding Tags

Edit `tags.yml`:

```yaml
- name: "my-project"
  parent: null
  locked: false
  maven_support: false
  state: "present"

- name: "my-project-build"
  parent: "my-project"
  locked: false
  maven_support: false
  state: "present"
```

### Adding Build Targets

Edit `targets.yml`:

```yaml
- name: "my-project"
  build_tag: "my-project-build"
  dest_tag: "my-project"
  state: "present"
```

## Available Permissions

When defining users, you can grant these permissions:

- **`admin`** - Full administrative access
- **`tag`** - Create and manage tags
- **`target`** - Create and manage build targets
- **`host`** - Manage build hosts
- **`dist-repo`** - Manage distribution repositories
- **`maven-import`** - Import Maven artifacts

## Architecture Notes

### How It Works

1. All Ansible infrastructure (playbooks, roles, collection) is **built into the container**
2. The `ansible-configurator` service waits for `koji-hub` to be healthy
3. It validates your data files using built-in schema validation
4. It authenticates using the admin keytab from the orchestration service
5. It applies your configuration using the `ktdreyer.koji_ansible` collection
6. The container exits after successful configuration

### Clean Separation

- **Infrastructure**: Hidden inside the container (playbooks, roles, collection, validation)
- **Data**: User-configurable YAML files in this directory
- **You can't break** the service interconnectivity - only configure Koji data

### Service Profile

The service uses the `ansible` profile, meaning:
- It doesn't start with `make up` by default
- You must explicitly run `make configure` to execute it
- This prevents unnecessary runs on every startup

### Authentication

The service authenticates using:
- **Kerberos keytab**: Mounted from the orchestration service
- **Admin principal**: Defined in `KOJI_ADMIN_PRINC` environment variable
- **Local connection**: Runs directly against the koji-hub container

## Troubleshooting

### Common Issues

**Configuration not applied:**
```bash
# Check if service ran successfully
make logs-ansible

# Force reconfiguration
make reconfigure
```

**YAML syntax errors:**
```bash
# Validate before running
make validate-ansible
```

**Authentication failures:**
```bash
# Check if keytab is available
make ansible-shell
ls -la /etc/koji-hub/admin.keytab
```

**Service won't start:**
```bash
# Check dependencies
podman-compose -p koji-boxed ps
```

### Debug Mode

For detailed debugging:

```bash
# Get interactive shell
make ansible-shell

# Run playbook manually with verbose output
cd /ansible-configs
ansible-playbook -i inventory.yml site.yml -vvv
```

## Extending the Configuration

### Adding Custom Tasks

1. Create new task files in `services/ansible-configurator/tasks/`
2. Add corresponding YAML configuration files
3. Update `site.yml` to include your new tasks

### Custom Ansible Modules

The `services/ansible-configurator/tasks/` directory contains custom Ansible modules:

- **`koji_user.py`** - Manages Koji users and permissions
- **`koji_host.py`** - Manages build hosts

You can add more custom modules following the same pattern.

### Environment Variables

Override defaults using environment variables:

```bash
# Custom Koji URLs
export KOJI_HUB_URL="https://my-koji-hub.example.com/kojihub"

# Custom admin principal
export KOJI_ADMIN_PRINC="my-admin@MY.REALM"

# Run configuration
make configure
```

## Best Practices

1. **Version Control**: Keep all configuration files in git
2. **Validation**: Always run `make validate-ansible` before applying
3. **Incremental Changes**: Make small changes and test frequently
4. **Backup**: Use `make backup` before major configuration changes
5. **Documentation**: Comment your YAML files to explain complex setups

## Security Considerations

- Configuration files are mounted read-only
- Admin keytab access is required but limited to the container
- No sensitive data should be stored in plain text YAML files
- Use environment variables for sensitive configuration

## Limitations

- Currently supports basic user/host/tag/target management
- More complex Koji features may require manual configuration
- Large-scale changes should be tested in development first
- Some operations may not be idempotent (running multiple times safely)

## Future Enhancements

Planned improvements:

- Support for package lists and build groups
- External group management integration
- Configuration drift detection
- Rollback capabilities
- Integration with CI/CD pipelines
