FROM almalinux:9

# Install system dependencies
RUN dnf install -y epel-release && \
    dnf config-manager --set-enabled crb

RUN dnf install -y \
    gcc \
    glibc-devel \
    libffi-devel \
    openssl-devel \
    bash \
    shadow-utils \
    util-linux \
    git \
    make \
    gcc-c++ \
    krb5-devel \
    krb5-workstation \
    python3 \
    python3-devel \
    python3-pip \
    python3-six \
    python3-defusedxml \
    python3-setuptools \
    python3-gssapi \
    python3-wheel \
    python3-dateutil \
    python3-psycopg2 \
    python3-jinja2 \
    python3-requests \
    python3-requests-gssapi \
    gettext \
    httpd \
    mod_ssl \
    mod_wsgi \
    mod_auth_gssapi \
    openssl && \
    dnf clean all

# Create koji user and group
RUN groupadd -g 1000 koji && \
    useradd -u 1000 -g koji -m -s /bin/bash koji

# Create directories
RUN mkdir -p /etc/koji-hub \
    /var/log/koji-hub \
    /var/lib/koji-hub \
    /mnt/koji && \
    touch /etc/koji.conf /etc/krb5.conf && \
    chown -R koji:koji /etc/koji-hub /mnt/koji /var/log/koji-hub /var/lib/koji-hub && \
    chown koji:koji /etc/koji.conf /etc/krb5.conf

# Copy Koji source (will be mounted from host)
# The actual Koji installation will be done in the entrypoint script
COPY koji-src/ /mnt/koji-src/
RUN python3 -m pip install --prefix /usr /mnt/koji-src/
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

# Copy configuration templates
COPY services/koji-hub/hub.conf.template /app/hub.conf.template
COPY services/koji-hub/httpd.conf.template /app/httpd.conf.template
COPY services/common/krb5.conf.template /app/krb5.conf.template
COPY services/common/koji.conf.template /app/koji.conf.template

COPY services/common/orch.sh /app/orch.sh
RUN chmod +x /app/orch.sh

# Expose port
EXPOSE 8080


# Start hub service
CMD ["/usr/local/bin/entrypoint.sh"]
