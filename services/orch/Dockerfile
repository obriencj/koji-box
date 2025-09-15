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

RUN pip install --no-cache-dir gssapi requests-gssapi gunicorn

COPY koji-src/ /tmp/koji-src/
RUN pip install /tmp/koji-src && rm -rf /tmp/koji-src

# Install Python dependencies
COPY services/orch/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY services/orch/app/ /app/app/
COPY services/orch/templates/ /app/templates/

COPY services/orch/entrypoint.sh /app/
COPY services/orch/health-check.sh /app/
COPY services/orch/manage-koji-host.sh /app/
COPY services/common/orch.sh /app/

COPY services/common/koji.conf.template /app/koji.conf.template
COPY services/common/krb5.conf.template /app/krb5.conf.template

# Make scripts executable
RUN chmod +x /app/*.sh

# Create necessary directories
RUN mkdir -p /mnt/data/keytabs /mnt/data/certs /mnt/data/logs

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 5000

# Start the application
CMD ["/app/entrypoint.sh"]

# The end.
