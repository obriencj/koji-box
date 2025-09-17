FROM almalinux:9

# Install system dependencies - consolidated from koji-hub and koji-worker
RUN dnf install -qy dnf-plugins-core epel-release && \
    dnf config-manager --set-enabled crb && \
    dnf install -qy \
    bash \
    diffutils \
    gettext \
    git \
    jq \
    krb5-workstation \
    make \
    openssl \
    python3 \
    python3-dateutil \
    python3-defusedxml \
    python3-devel \
    python3-gssapi \
    python3-jinja2 \
    python3-pyOpenSSL \
    python3-pip \
    python3-psycopg2 \
    python3-requests \
    python3-requests-gssapi \
    python3-setuptools \
    python3-six \
    python3-wheel \
    shadow-utils \
    tini \
    util-linux \
    which && \
    dnf clean all

# Create koji user and group with consistent IDs
RUN groupadd -g 1000 koji && \
    useradd -u 1000 -g koji -m -s /bin/bash koji

# Copy and install Koji source
ENV PIP_ROOT_USER_ACTION=ignore
COPY koji-src/ /mnt/koji-src/
RUN python3 -m pip install --no-cache-dir /mnt/koji-src/

# Copy common configuration templates
COPY services/common/krb5.conf.template /app/krb5.conf.template
COPY services/common/koji.conf.template /app/koji.conf.template
COPY services/common/configure.sh /app/configure.sh
COPY services/common/orch.sh /app/orch.sh
RUN chmod +x /app/configure.sh /app/orch.sh

# Set up common ownership
RUN mkdir -p /mnt/koji /etc/koji-common && \
    chown -R koji:koji /mnt/koji /etc/koji-common

# The end.
