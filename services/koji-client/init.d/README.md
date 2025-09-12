# Koji Client Init Scripts

This directory contains initialization scripts for the Koji client container. These scripts are executed in alphabetical order when the container starts.

## Status: ✅ Fully Functional

The Koji Client service is currently working and provides:
- Koji CLI command execution
- Kerberos authentication integration
- Automated testing capabilities
- Integration with the keytab service

## Scripts

### 01-kinit.sh
Fetches the client principal from the keytab service and performs Kerberos authentication using `kinit`.

**Environment Variables:**
- `CLIENT_PRINCIPAL`: The principal name to authenticate as (default: friend@KOJI.BOX)
- `KEYTAB_SERVICE_HOST`: Hostname of the keytab service (default: keytab-service.koji.box)
- `KEYTAB_SERVICE_PORT`: Port of the keytab service (default: 5000)

### 02-test-koji.sh
Tests the Koji client functionality after authentication.

## Service Access

- **Container Access**: `make shell-hub` or `podman exec -it koji-boxed-koji-client-1 /bin/bash`
- **Profile**: Available via `shell` profile in docker-compose
- **Dependencies**: Requires keytab-service and koji-hub to be running

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
