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
- Keytab Service (for authentication)
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
- `KEYTAB_SERVICE_URL`: Keytab service URL

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
