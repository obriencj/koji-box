# Koji Client Service

This directory contains the Koji CLI client configuration and setup.

## Status: 🚧 In Progress

The Koji Client service is currently working but undergoing reliability improvements. It provides:
- CLI interface for Koji administration and testing
- Kerberos authentication integration
- Resource management via orch service

## Current Status

### ✅ Working Features
- Basic Koji CLI functionality
- Kerberos authentication
- Integration with orch service for resource management
- Container-based execution environment

### 🚧 In Progress
- Reliability improvements for consistent operation
- Enhanced error handling and recovery
- Better integration with the new orch service
- Improved authentication flow

## Configuration Files

### Dockerfile
Container image definition with Koji client installation and configuration.

### entrypoint.sh
Container startup script for service initialization and authentication setup.

### startup.sh
Main startup script that handles authentication and Koji client initialization.

### init.d/
Initialization scripts for:
- Koji client configuration
- Kerberos setup
- Resource management integration

## Service Access

- **Container Access**: `make shell-client`
- **Direct Commands**: Execute via `podman-compose exec koji-client <command>`
- **Health Check**: Service runs on-demand for CLI operations

## Dependencies

- Koji Hub service (for API access)
- Orch Service (for resource management)
- KDC service (for Kerberos authentication)

## Environment Variables

- `KOJI_HUB_URL`: Backend Koji Hub URL
- `KOJI_WEB_URL`: Web interface URL
- `KRB5_REALM`: Kerberos realm
- `ORCH_SERVICE_URL`: Orch service URL for resource management

## Usage Examples

### Basic Koji Commands
```bash
# Access the client container
make shell-client

# Inside the container, run Koji commands
koji list-users
koji list-tags
koji list-targets
```

### Resource Management
```bash
# The client automatically integrates with orch service
# for resource management and authentication
```

## Troubleshooting

If you encounter issues with the Koji Client service:

1. **Check service logs**: `make logs-client` (if available)
2. **Verify Koji Hub connectivity**: Test from within the container
3. **Test authentication**: `make test-kerberos`
4. **Check orch service**: Verify resource management is working
5. **Access container shell**: `make shell-client` for debugging

### Common Issues

1. **Authentication failures**: Check KDC service and principal configuration
2. **Connection issues**: Verify Koji Hub is running and accessible
3. **Resource management errors**: Check orch service status and configuration
4. **Reliability issues**: These are being actively addressed in current development

## Development Status

- **Current Focus**: Reliability improvements and enhanced error handling
- **Integration**: Working on better integration with the new orch service
- **Authentication**: Improving Kerberos authentication flow
- **Error Recovery**: Adding better error handling and recovery mechanisms

## Future Enhancements

- Enhanced error handling and recovery
- Better integration with orch service V2 API
- Improved authentication flow
- More robust connection management
- Enhanced logging and debugging capabilities

## Related Documentation

- [Main Project README](../../README.md)
- [Orch Service README](../orch/README.md)
- [KDC Service README](../kdc/README.md)
- [Koji Hub Service README](../koji-hub/README.md)
