# KDC Configuration Templates

This directory contains configuration templates for the KDC (Key Distribution Center) service.

## Status: ✅ Fully Functional

The KDC service is currently working and provides:
- Kerberos authentication for all Koji services
- Service principal management
- Admin user creation and management
- Realm: KOJI.BOX

## Files

### kdc.conf.template
Template for the KDC configuration file. Environment variables are expanded at runtime to create the final `kdc.conf` file.

### kadm5.acl.template
Template for the KDC admin access control list. Environment variables are expanded at runtime to create the final `kadm5.acl` file.

**Environment Variables:**
- `KRB5_REALM`: Kerberos realm name (default: KOJI.BOX)

**Hard-coded Configuration:**
- KDC ports: 88 (UDP and TCP)
- Maximum ticket lifetime: 12h 0m 0s
- Maximum renewable ticket lifetime: 7d 0h 0m 0s
- Master key type: aes256-cts
- Supported encryption types: aes256-cts:normal aes128-cts:normal des3-hmac-sha1:normal arcfour-hmac:normal des-hmac-sha1:normal des-cbc-md5:normal des-cbc-crc:normal
- Default principal flags: +preauth
- Log files: /var/log/krb5libs.log, /var/log/krb5kdc.log, /var/log/kadmind.log

## Service Access

- **KDC Port**: `kdc.koji.box:88`
- **Admin Access**: `kdc.koji.box:749`
- **Password Change**: `kdc.koji.box:464`
- **Container Access**: `make shell-kdc`

## How It Works

1. The template files are copied into the container during build
2. At runtime, the entrypoint script uses `envsubst` to expand environment variables in both templates
3. The expanded configurations are written to `/etc/krb5kdc/kdc.conf` and `/etc/krb5kdc/kadm5.acl`
4. The KDC services start using the generated configurations

## Customization

To customize the KDC configuration:

1. Set the `KRB5_REALM` environment variable in `docker-compose.yml` or `.env` file
2. Rebuild the container: `podman-compose build kdc`
3. Restart the service: `podman-compose up -d kdc`

For other configuration changes (ports, encryption types, etc.), modify the template file directly and rebuild.

## Example

```bash
# Set custom realm
export KRB5_REALM=MYCOMPANY.COM

# Rebuild and restart
podman-compose build kdc
podman-compose up -d kdc
```
