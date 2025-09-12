# Nginx Service

This directory contains the Nginx reverse proxy configuration for the Koji Boxed environment.

## Status: 🚧 In Progress

The Nginx service is currently being configured and tested. It will provide:
- Unified entry point for all Koji services
- Reverse proxy routing to backend services
- Static file serving for downloads
- Health check endpoints

## Planned Features

### Routing Configuration
- **`/`** - Routes to Koji Web interface (default)
- **`/kojihub/`** - Routes to Koji Hub API
- **`/downloads/`** - Serves static content from `/mnt/koji` with directory indexing
- **`/health`** - Nginx health check endpoint

### Service Integration
- Koji Web backend integration
- Koji Hub API proxy
- Static file serving with directory indexing
- SSL/TLS termination (planned)

## Configuration Files

### nginx.conf
Main Nginx configuration file with global settings and includes.

### default.conf
Default server configuration with routing rules and upstream definitions.

## Service Access

- **Planned Main Entry**: `http://localhost:8080`
- **Container Access**: `make shell-nginx`
- **Health Check**: `http://localhost:8080/health`

## Dependencies

- Koji Hub service (for API routing)
- Koji Web service (for web interface routing)
- Shared storage volume (for static file serving)

## Development Status

- Configuration files are being developed
- Routing rules are being tested
- Integration with backend services is in progress
- Health checks are being implemented

## Troubleshooting

If you encounter issues with the Nginx service:

1. Check service logs: `make logs-nginx`
2. Verify configuration: `make shell-nginx` then `nginx -t`
3. Test routing: `curl http://localhost:8080/health`
4. Check backend service connectivity

## Future Enhancements

- SSL/TLS certificate management
- Load balancing for multiple workers
- Caching configuration
- Security headers
- Rate limiting
