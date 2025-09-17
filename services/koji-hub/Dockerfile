FROM koji-boxed-common

# Install hub-specific dependencies
RUN dnf install -y \
    httpd \
    python3-psycopg2 \
    python3-sqlalchemy \
    mod_ssl \
    mod_wsgi \
    mod_auth_gssapi && \
    dnf clean all

# Create hub-specific directories
RUN mkdir -p /etc/koji-hub \
    /var/log/koji-hub \
    /var/lib/koji-hub && \
    chown -R koji:koji /etc/koji-hub /var/log/koji-hub /var/lib/koji-hub

# Install koji-hub components
RUN chmod +x /mnt/koji-src/devtools/*.py && \
    cd /mnt/koji-src/kojihub && \
    PYTHON=python3 DESTDIR=/ make install

# Copy entrypoint script
COPY services/koji-hub/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy startup script
COPY services/koji-hub/startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Copy health check script
COPY services/koji-hub/health-check.sh /app/health-check.sh
RUN chmod +x /app/health-check.sh

# Copy hub-specific configuration templates
COPY services/koji-hub/hub.conf.template /app/hub.conf.template
COPY services/koji-hub/httpd.conf.template /app/httpd.conf.template

# Expose port
EXPOSE 80 443

# Start hub service
ENTRYPOINT ["/usr/bin/tini", "-g", "/app/entrypoint.sh"]

# The end.
