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
    krb5-dev

# Install Python packages
RUN pip install --no-cache-dir \
    psycopg2-binary \
    sqlalchemy \
    flask \
    gunicorn \
    requests \
    cryptography \
    pyopenssl

# Create koji user and group
RUN addgroup -g 1000 koji && \
    adduser -D -u 1000 -G koji koji

# Create directories
RUN mkdir -p /etc/koji-hub \
    /var/log/koji-hub \
    /var/lib/koji-hub \
    /mnt/koji

# Copy Koji source (will be mounted from host)
# The actual Koji installation will be done in the entrypoint script

# Copy configuration files
# COPY hub.conf /etc/koji-hub/hub.conf
# COPY koji-ca-crt.crt /etc/koji-hub/koji-ca-crt.crt

# Copy setup script
COPY setup-koji-hub.sh /usr/local/bin/setup-koji-hub.sh
RUN chmod +x /usr/local/bin/setup-koji-hub.sh

# Copy hub service script
COPY hub-service.py /usr/local/bin/hub-service.py
RUN chmod +x /usr/local/bin/hub-service.py

# Copy health check script
COPY health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Set ownership
RUN chown -R koji:koji /etc/koji-hub \
    /var/log/koji-hub \
    /var/lib/koji-hub

# Switch to koji user
USER koji

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=15s --timeout=10s --start-period=30s --retries=5 \
    CMD /usr/local/bin/health-check.sh

# Start hub service
CMD ["/usr/local/bin/hub-service.py"]
