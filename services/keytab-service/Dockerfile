FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    krb5-dev \
    krb5 \
    curl \
    bash \
    gcc \
    musl-dev \
    libffi-dev \
    envsubst \
    openssl

# Install Python packages
RUN pip install --no-cache-dir \
    flask gunicorn \
    requests-gssapi

COPY koji-src/ /mnt/koji-src/
RUN pip install /mnt/koji-src/ && \
    rm -rf /mnt/koji-src/

# Create principal-service user
RUN addgroup -g 1001 principal-service && \
    adduser -D -u 1001 -G principal-service principal-service

# Create directories
RUN mkdir -p /app \
    /var/log/principal-service

WORKDIR /app

# Copy shared configuration templates
COPY services/common/koji.conf.template /app/koji.conf.template
COPY services/common/krb5.conf.template /app/krb5.conf.template

# Copy application files
COPY services/keytab-service/app.py /app/app.py
COPY services/keytab-service/health-check.sh /app/health-check.sh
COPY services/keytab-service/manage-koji-host.sh /app/manage-koji-host.sh
COPY services/keytab-service/entrypoint.sh /app/entrypoint.sh

# Set permissions
RUN chmod +x /app/app.py \
    /app/health-check.sh \
    /app/manage-koji-host.sh \
    /app/entrypoint.sh

# Set ownership
RUN chown -R principal-service:principal-service /app \
    /var/log/principal-service && \
    mkdir -p /mnt/data/keytabs /mnt/data/certs && \
    chown -R principal-service:principal-service /mnt/data

# Switch to principal-service user
USER principal-service

# Expose port
EXPOSE 5000

# Start the service
CMD ["/app/entrypoint.sh"]

# The end.
