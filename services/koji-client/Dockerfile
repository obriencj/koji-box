FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    curl \
    jq \
    bash \
    shadow \
    util-linux \
    git \
    make \
    gcc \
    g++ \
    python3-dev \
    krb5-dev \
    krb5 \
    envsubst

# Install Python packages
RUN pip install --no-cache-dir \
    requests-gssapi

# Create koji user and group
RUN addgroup -g 1000 friend && \
    adduser -D -u 1000 -G friend friend

# Create directories
RUN mkdir -p /etc/koji \
    /var/log/koji-client \
    /var/lib/koji-client \
    /mnt/koji


COPY koji-src/ /mnt/koji-src/
RUN pip install /mnt/koji-src/ && \
    rm -rf /mnt/koji-src/

COPY services/common/krb5.conf.template /etc/krb5.conf.template
COPY services/common/koji.conf.template /etc/koji.conf.template

COPY services/common/orch.sh /app/orch.sh
COPY services/koji-client/entrypoint.sh /app/entrypoint.sh
COPY services/koji-client/startup.sh /app/startup.sh
RUN chmod +x /app/*.sh

# Set ownership
RUN chown -R friend:friend /etc/koji \
    /var/log/koji-client \
    /var/lib/koji-client

# Start client service (interactive shell)
CMD ["/app/entrypoint.sh"]

# The end.
