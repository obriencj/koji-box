FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    curl \
    bash \
    shadow \
    util-linux \
    git \
    make \
    gcc \
    g++ \
    python3-dev \
    krb5-dev \
    gettext

# Install Python packages
RUN pip install --no-cache-dir \
    psycopg2-binary \
    sqlalchemy \
    flask \
    gunicorn \
    requests \
    cryptography \
    pyopenssl \
    jinja2

# Create koji user and group
RUN addgroup -g 1000 koji && \
    adduser -D -u 1000 -G koji koji

# Create directories
RUN mkdir -p /etc/koji-web \
    /var/log/koji-web \
    /var/lib/koji-web \
    /usr/share/koji-web

# Copy shared configuration templates
COPY configs/shared/krb5.conf.template /app/krb5.conf.template

# Copy Koji source (will be mounted from host)
# The actual Koji installation will be done in the entrypoint script

# Copy entrypoint script
COPY containers/koji-web/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy health check script
COPY containers/koji-web/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Set ownership
RUN chown -R koji:koji /etc/koji-web \
    /var/log/koji-web \
    /var/lib/koji-web \
    /usr/share/koji-web

# Switch to koji user
USER koji

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=15s --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Start web service
CMD ["/usr/local/bin/entrypoint.sh"]
