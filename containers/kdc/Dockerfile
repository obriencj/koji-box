FROM ubuntu:22.04

# Install Kerberos and dependencies
RUN apt-get update && apt-get install -y \
    krb5-kdc \
    krb5-admin-server \
    krb5-user \
    krb5-config \
    libkrb5-dev \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV KRB5_REALM=KOJI.BOX
ENV KRB5_KDC=localhost
ENV KRB5_ADMIN_SERVER=localhost

# Create directories
RUN mkdir -p /var/lib/krb5kdc \
    /etc/krb5kdc \
    /var/log/krb5kdc

# Copy configuration files
# COPY krb5.conf /etc/krb5.conf
# COPY kdc.conf /etc/krb5kdc/kdc.conf
# COPY kadm5.acl /etc/krb5kdc/kadm5.acl

# Copy setup script
COPY setup-kdc.sh /usr/local/bin/setup-kdc.sh
RUN chmod +x /usr/local/bin/setup-kdc.sh

# Copy service script
COPY kdc-service.sh /usr/local/bin/kdc-service.sh
RUN chmod +x /usr/local/bin/kdc-service.sh

# Copy health check script
COPY health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Expose ports
EXPOSE 88 749 464

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Start KDC service
CMD ["/usr/local/bin/kdc-service.sh"]
