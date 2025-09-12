# Koji Hub Init Scripts

This directory contains initialization scripts for the Koji Hub container. These scripts are executed in alphabetical order when the container starts.

## Status: ✅ Fully Functional

The Koji Hub service is currently working and provides:
- Central coordination for the Koji build system
- User and permission management
- Build task coordination
- REST API endpoints
- Kerberos authentication integration

## Scripts

### 01-kinit.sh
Fetches the hub principal from the keytab service and performs Kerberos authentication using `kinit`.

**Environment Variables:**
- `KOJI_HUB_PRINC`: The principal name for the hub service (default: HTTP/koji-hub.koji.box@KOJI.BOX)
- `KEYTAB_SERVICE_HOST`: Hostname of the keytab service (default: keytab-service.koji.box)
- `KEYTAB_SERVICE_PORT`: Port of the keytab service (default: 5000)

### 02-setup-koji-hub.sh
Configures the Koji Hub service after authentication.

## Service Access

- **Direct Access**: `http://koji-hub.koji.box:80`
- **API Endpoint**: `http://koji-hub.koji.box:80/kojihub`
- **Health Check**: `koji version` command

## Adding New Scripts

To add new initialization scripts:

1. Create a new shell script with a numeric prefix (e.g., `03-my-script.sh`)
2. Make it executable: `chmod +x 03-my-script.sh`
3. The script will be automatically executed in alphabetical order

## Script Requirements

- Scripts must be executable
- Scripts should handle errors gracefully
- Scripts can exit with non-zero status without stopping the container
- Scripts have access to all environment variables set in docker-compose.yml

## Example Script

```bash
#!/bin/bash
echo "My custom initialization script"
# Your initialization logic here
echo "Script completed"
```
