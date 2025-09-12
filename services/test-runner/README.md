# Test Runner Service

This directory contains the automated testing framework for the Koji Boxed environment.

## Status: 🚧 In Progress

The Test Runner service is currently being developed and will provide:
- Automated integration testing
- Test result reporting
- Continuous testing capabilities
- Integration with the Koji environment

## Planned Features

### Test Execution
- Automated test script execution
- Test result collection and reporting
- Integration with CI/CD pipelines
- Parallel test execution

### Test Coverage
- Basic Koji functionality tests
- Authentication and authorization tests
- Build process tests
- API endpoint tests
- Service integration tests

## Service Structure

### init.d/
Directory containing test initialization scripts that run when the container starts.

## Service Access

- **Container Access**: `make shell-hub` (extends koji-client)
- **Profile**: Available via `test` profile in docker-compose
- **Dependencies**: Requires all core services to be running

## Environment Variables

- `CLIENT_PRINCIPAL`: Test user principal (default: test-user@KOJI.BOX)
- `KOJI_HUB_URL`: Koji Hub URL for testing
- `KEYTAB_SERVICE_URL`: Keytab service URL
- `KRB5_REALM`: Kerberos realm

## Development Status

- Test framework is being developed
- Integration with Koji services is being tested
- Test scripts are being written
- Reporting mechanisms are being implemented

## Test Categories

### Unit Tests
- Individual service functionality
- Configuration validation
- Authentication mechanisms

### Integration Tests
- Service-to-service communication
- End-to-end workflows
- Error handling and recovery

### Performance Tests
- Load testing
- Resource usage monitoring
- Response time validation

## Usage

### Running Tests
```bash
# Start test environment
make up

# Run specific test profile
podman-compose --profile test up -d test-runner

# Execute tests
make test
```

### Test Development
1. Add test scripts to `init.d/` directory
2. Make scripts executable
3. Test scripts will run automatically on container start
4. Check logs for test results

## Troubleshooting

If you encounter issues with the Test Runner:

1. Check service logs: `make logs` (test-runner extends koji-client)
2. Verify all dependencies are running
3. Test authentication: `make test-kerberos`
4. Check test script permissions

## Future Enhancements

- Test result dashboard
- Automated test scheduling
- Performance benchmarking
- Test coverage reporting
- Integration with external testing tools
