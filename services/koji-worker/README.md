# Koji Worker Service

This directory contains the Koji worker configuration and setup for build execution.

## Status: 🚧 In Progress

The Koji Worker service is currently in development and available via the `workers` profile. It provides:
- Build execution capabilities
- Integration with Koji Hub
- Resource management via orch service
- Container-based build environment

## Current Status

### ✅ Working Features
- Basic worker container setup
- Integration with orch service for resource management
- Health check functionality
- Container orchestration support

### 🚧 In Progress
- Build execution reliability
- Integration with Koji Hub
- Resource management optimization
- Error handling and recovery

## Configuration Files

### Dockerfile
Container image definition with Koji worker installation and configuration.

### worker-service.py
Python service script for worker management and build execution.

### health-check.sh
Health check script for service monitoring and container orchestration.

## Service Access

- **Profile-based Access**: `make up --profile workers`
- **Container Access**: `make shell-worker`
- **Health Check**: Automatic health monitoring via container orchestration

## Dependencies

- Koji Hub service (for build coordination)
- Orch Service (for resource management)
- KDC service (for Kerberos authentication)
- Shared storage volume (for build artifacts)

## Environment Variables

- `KOJI_HUB_URL`: Backend Koji Hub URL
- `ORCH_SERVICE_URL`: Orch service URL for resource management
- `KRB5_REALM`: Kerberos realm
- `KOJI_TOP_DIR`: Shared storage directory for build artifacts

## Usage Examples

### Starting Workers
```bash
# Start the worker service
make up --profile workers

# Check worker status
make status

# View worker logs
make logs-worker
```

### Accessing Worker Container
```bash
# Open shell in worker container
make shell-worker

# Inside the container, check worker status
ps aux | grep koji-worker
```

## Service Profile

The worker service uses Docker Compose profiles for optional deployment:

```yaml
profiles:
  - "workers"
```

This allows workers to be started only when needed:
```bash
# Start only workers
make up --profile workers

# Start all services including workers
make up --profile workers
```

## Troubleshooting

If you encounter issues with the Koji Worker service:

1. **Check service logs**: `make logs-worker`
2. **Verify Koji Hub connectivity**: Test from within the container
3. **Check orch service**: Verify resource management is working
4. **Test worker registration**: Verify worker is registered with hub
5. **Access container shell**: `make shell-worker` for debugging

### Common Issues

1. **Worker registration failures**: Check Koji Hub connectivity and authentication
2. **Resource management errors**: Verify orch service status and configuration
3. **Build execution issues**: Check worker configuration and dependencies
4. **Health check failures**: Verify worker process is running correctly

## Development Status

- **Current Focus**: Build execution reliability and hub integration
- **Resource Management**: Working on optimal integration with orch service
- **Error Handling**: Adding better error handling and recovery mechanisms
- **Monitoring**: Improving health checks and status reporting

## Future Enhancements

- Enhanced build execution capabilities
- Better integration with orch service V2 API
- Improved error handling and recovery
- Advanced monitoring and logging
- Support for multiple worker instances
- Build artifact management improvements

## Architecture Integration

The worker service integrates with the overall Koji Boxed architecture:

```
koji-hub ←─── koji-worker
    ↓              ↓
orch-service ←─────┘
    ↓
   kdc
```

- **Koji Hub**: Receives build requests and coordinates with workers
- **Orch Service**: Manages worker resources and authentication
- **KDC**: Provides Kerberos authentication for worker operations
- **Shared Storage**: Stores build artifacts and packages

## Related Documentation

- [Main Project README](../../README.md)
- [Orch Service README](../orch/README.md)
- [Koji Hub Service README](../koji-hub/README.md)
- [KDC Service README](../kdc/README.md)
