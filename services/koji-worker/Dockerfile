FROM koji-boxed-common

# Install worker-specific dependencies
RUN dnf install -qy \
    createrepo_c \
    mock \
    podman \
    python3-cheetah \
    python3-librepo \
    python3-multilib \
    python3-pycdio \
    pykickstart \
    yum-utils \
    zstd && \
    dnf clean all

# Install koji-adjutant dependencies
RUN python3 -m pip install --no-cache-dir podman

# Create worker-specific directories
RUN mkdir -p \
    /var/tmp/koji \
    /var/log/koji-worker \
    /var/lib/koji-worker \
    /var/lib/mock \
    /var/cache/mock \
    /etc/mock/koji

RUN chown -R koji:mock \
    /var/tmp/koji \
    /var/log/koji-worker \
    /var/lib/koji-worker \
    /var/lib/mock \
    /var/cache/mock \
    /etc/mock/koji

RUN usermod koji -aG mock

# Install koji-adjutant
COPY adjutant/ /mnt/koji-adjutant/
RUN python3 -m pip install --no-cache-dir -e /mnt/koji-adjutant/

# kojid is now available as console script entry point from koji-adjutant
# No need to copy - it's installed in PATH as 'kojid' command

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
