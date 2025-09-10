FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    nfs-utils \
    curl \
    bash \
    shadow \
    util-linux

# Install Python packages
RUN pip install --no-cache-dir \
    flask \
    gunicorn \
    requests

# Create koji user and group
RUN addgroup -g 1000 koji && \
    adduser -D -u 1000 -G koji koji

# Create storage directories
RUN mkdir -p /mnt/koji/{packages,repos,work,scratch} && \
    chown -R koji:koji /mnt/koji

# Create storage service script
COPY storage-service.py /usr/local/bin/storage-service.py
RUN chmod +x /usr/local/bin/storage-service.py

# Create health check script
COPY health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Switch to koji user
USER koji

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Start storage service
CMD ["/usr/local/bin/storage-service.py"]
