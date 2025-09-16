# Koji Web Service

This directory contains the Koji Web interface configuration and setup.

## Status: 🚧 In Progress

The Koji Web service is currently being configured and tested. It will provide:
- Web-based interface for Koji management
- User-friendly build monitoring
- Package browsing and search
- Integration with Koji Hub backend

## Planned Features

### Web Interface
- Build queue monitoring
- Package search and browsing
- User management interface
- Build history and logs
- Tag and target management

### Integration
- Koji Hub API integration
- Kerberos authentication
- Static file serving
- Real-time updates

## Configuration Files

### koji_web.conf
Koji Web configuration file with backend settings and authentication.

### entrypoint.sh
Container startup script for service initialization.

### health-check.sh
Health check script for service monitoring.

## Service Access

- **Planned Direct Access**: `http://koji-web.koji.box:8080`
- **Planned via Nginx**: `http://localhost:8080/` (when nginx is ready)
- **Container Access**: `make shell-web`
- **Health Check**: `curl http://koji-web.koji.box:8080/`

## Dependencies

- Koji Hub service (for API access)
- Orch Service (for authentication and resource management)
- Nginx service (for unified access)

## Development Status

- Web interface configuration is being developed
- Backend integration is being tested
- Authentication setup is in progress
- Health checks are being implemented

## Environment Variables

- `KOJI_HUB_URL`: Backend Koji Hub URL
- `KOJI_WEB_URL`: Web interface URL
- `KRB5_REALM`: Kerberos realm
- `ORCH_SERVICE_URL`: Orch service URL for resource management

## Troubleshooting

If you encounter issues with the Koji Web service:

1. Check service logs: `make logs-web`
2. Verify Koji Hub connectivity
3. Test authentication: `make test-kerberos`
4. Check configuration: `make shell-web`

## Future Enhancements

- Modern web UI framework integration
- Real-time build monitoring
- Advanced search capabilities
- Mobile-responsive design
- User preference management
- Integration with orch service for enhanced security
- SSL/TLS support via orch service CA certificates

## Integration with Orch Service

The koji-web service integrates with the orch service for:

- **Authentication**: Enhanced authentication via orch service resource management
- **Security**: Improved security through orch service resource checkout system
- **Resource Management**: Coordinated resource management with other services
- **SSL/TLS**: Certificate management via orch service CA

### Resource Management

```bash
# Get web service keytab from orch service
./services/common/orch.sh checkout <web-keytab-uuid> /etc/koji-web/web.keytab

# Get SSL certificate for web service
./services/common/orch.sh checkout <web-cert-uuid> /etc/koji-web/ssl/web.crt
```

## Related Documentation

- [Main Project README](../../README.md)
- [Orch Service README](../orch/README.md)
- [Koji Hub Service README](../koji-hub/README.md)
- [Nginx Service README](../nginx/README.md)
