# Test Runner Init Scripts

This directory contains initialization scripts for the Test Runner container. These scripts are executed in alphabetical order when the container starts.

## Status: 🚧 In Progress

The Test Runner service is currently being developed and will provide:
- Automated integration testing
- Test result reporting
- Continuous testing capabilities
- Integration with the Koji environment

## Scripts

### 01-kinit.sh
Fetches the test user principal from the keytab service and performs Kerberos authentication using `kinit`.

**Environment Variables:**
- `CLIENT_PRINCIPAL`: The principal name for test user (default: test-user@KOJI.BOX)
- `KEYTAB_SERVICE_HOST`: Hostname of the keytab service (default: keytab-service.koji.box)
- `KEYTAB_SERVICE_PORT`: Port of the keytab service (default: 5000)

### 02-test-koji.sh
Executes basic Koji functionality tests after authentication.

## Service Access

- **Container Access**: `make shell-hub` (extends koji-client)
- **Profile**: Available via `test` profile in docker-compose
- **Dependencies**: Requires all core services to be running

## Adding New Test Scripts

To add new test scripts:

1. Create a new shell script with a numeric prefix (e.g., `03-my-test.sh`)
2. Make it executable: `chmod +x 03-my-test.sh`
3. The script will be automatically executed in alphabetical order

## Script Requirements

- Scripts must be executable
- Scripts should handle errors gracefully
- Scripts can exit with non-zero status without stopping the container
- Scripts have access to all environment variables set in docker-compose.yml
- Test scripts should output results in a consistent format

## Example Test Script

```bash
#!/bin/bash
echo "Running my custom test..."
# Your test logic here
if [ $? -eq 0 ]; then
    echo "✅ Test passed"
else
    echo "❌ Test failed"
    exit 1
fi
echo "Test completed"
```
