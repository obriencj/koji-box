FROM python:3.11-alpine

# Install system dependencies
RUN apt-get update && apt-get install -y \
    krb5-dev \
    krb5 \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir gssapi requests-gssapi gunicorn

COPY koji-src/ /tmp/koji-src/
RUN pip install /tmp/koji-src && rm -rf /tmp/koji-src

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY app/ /app/app/
COPY templates/ /app/templates/

COPY entrypoint.sh /app/
COPY health-check.sh /app/
COPY manage-koji-host.sh /app/

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
