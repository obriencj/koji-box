FROM koji-boxed-common

# Install worker-specific dependencies
RUN dnf install -qy \
    createrepo_c \
    mock \
    pykickstart \
    python3-cheetah \
    python3-librepo \
    python3-multilib \
    python3-pycdio \
    yum-utils && \
    dnf clean all

# Create worker-specific directories
RUN mkdir -p /var/log/koji-worker \
    /var/lib/koji-worker \
    /var/lib/mock \
    /var/cache/mock


RUN cp /mnt/koji-src/builder/kojid /app/kojid && \
    sed -i 's,/usr/bin/python2,/usr/bin/python3,g' /app/kojid && \
    chmod +x /app/kojid


# Copy kojid.conf template
COPY services/koji-worker/kojid.conf.template /app/kojid.conf.template

# Copy kojid.conf template
COPY services/koji-worker/kojid.conf.template /app/kojid.conf.template

# Copy entrypoint.sh
COPY services/koji-worker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy health-check.sh
COPY services/koji-worker/health-check.sh /app/health-check.sh
RUN chmod +x /app/health-check.sh

# Start worker service
CMD ["/app/entrypoint.sh"]

# The end.
