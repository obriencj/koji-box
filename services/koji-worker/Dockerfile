FROM build_image

# Install worker-specific dependencies
RUN dnf install -qy \
    createrepo_c \
    mock \
    yum-utils && \
    dnf clean all

# Create worker-specific directories
RUN mkdir -p /var/log/koji-worker \
    /var/lib/koji-worker \
    /var/lib/mock \
    /var/cache/mock

# Copy worker service script
COPY services/koji-worker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy health check script
COPY services/koji-worker/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Switch to koji user
# USER koji

# Start worker service
CMD ["/usr/local/bin/entrypoint.sh"]

# The end.
