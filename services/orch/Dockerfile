FROM koji-boxed-common


RUN dnf install -y \
    python3-flask \
    python3-gunicorn \
    python3-podman \
    python3-pyyaml

# Install Python dependencies
COPY services/orch/requirements.txt /app/

# Copy application code
COPY services/orch/app/ /app/app/

COPY services/orch/entrypoint.sh /app/
COPY services/orch/health-check.sh /app/
COPY services/orch/manage-koji-host.sh /app/

# Make scripts executable
RUN chmod +x /app/*.sh

# Create necessary directories
RUN mkdir -p /mnt/data/keytabs /mnt/data/certs /mnt/data/logs

# Set working directory
WORKDIR /app

# Expose port
EXPOSE 5000

# Start the application
ENTRYPOINT ["/usr/bin/tini", "-g", "/app/entrypoint.sh"]

# The end.
