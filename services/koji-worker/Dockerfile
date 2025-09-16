FROM almalinux:9

# Install system dependencies
RUN dnf install -qy dnf-plugins-core epel-release && \
    dnf config-manager --set-enabled crb && \
    dnf install -qy \
    postgresql-devel \
    gcc \
    libffi-devel \
    openssl-devel \
    bash \
    shadow \
    util-linux \
    git \
    make \
    python3-devel \
    python3-gssapi \
    python3-dateutil \
    python3-requests-gssapi \
    rpm \
    createrepo_c \
    mock \
    yum-utils

# Install Python packages
RUN pip install --no-cache-dir \
    psycopg2-binary \
    sqlalchemy \
    requests \
    cryptography \
    pyopenssl \
    docker

# Create koji user and group
RUN useradd -m -U -s /bin/bash koji

# Create directories
RUN mkdir -p /var/log/koji-worker \
    /var/lib/koji-worker \
    /mnt/koji \
    /var/lib/mock \
    /var/cache/mock

# Copy Koji source (will be mounted from host)
COPY koji-src/ /mnt/koji-src/
RUN pip install --no-cache-dir /mnt/koji-src/


# Copy worker service script
COPY services/koji-worker/worker-service.py /usr/local/bin/worker-service.py
RUN chmod +x /usr/local/bin/worker-service.py

# Copy health check script
COPY services/koji-worker/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Set ownership
RUN chown -R koji:koji /var/log/koji-worker \
    /var/lib/koji-worker \
    /var/lib/mock \
    /var/cache/mock

# Switch to koji user
# USER koji

# Start worker service
CMD ["/usr/local/bin/worker-service.py"]

# The end.
