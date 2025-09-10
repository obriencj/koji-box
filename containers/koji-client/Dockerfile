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
    requests \
    cryptography \
    pyopenssl \
    click

# Create koji user and group
RUN addgroup -g 1000 koji && \
    adduser -D -u 1000 -G koji koji

# Create directories
RUN mkdir -p /etc/koji \
    /var/log/koji-client \
    /var/lib/koji-client \
    /mnt/koji

# Copy Koji source (will be mounted from host)
# The actual Koji installation will be done in the entrypoint script

# Copy configuration files
# COPY koji.conf /etc/koji/koji.conf

# Copy client service script
COPY client-service.py /usr/local/bin/client-service.py
RUN chmod +x /usr/local/bin/client-service.py

# Copy health check script
COPY health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Set ownership
RUN chown -R koji:koji /etc/koji \
    /var/log/koji-client \
    /var/lib/koji-client

# Switch to koji user
USER koji

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Start client service (interactive shell)
CMD ["/usr/local/bin/client-service.py"]
