FROM koji-boxed-common

# Install hub-specific dependencies
RUN dnf install -y \
    httpd \
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
COPY services/koji-hub/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy startup script
COPY services/koji-hub/startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# Copy health check script
COPY services/koji-hub/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Copy hub-specific configuration templates
COPY services/koji-hub/hub.conf.template /app/hub.conf.template
COPY services/koji-hub/httpd.conf.template /app/httpd.conf.template

# Expose port
EXPOSE 80 443

# Start hub service
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# The end.
