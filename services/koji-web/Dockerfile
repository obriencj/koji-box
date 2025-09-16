FROM build_image

RUN dnf install -qy \
    httpd \
    mod_ssl \
    mod_wsgi \
    mod_auth_gssapi && \
    dnf clean all

# Copy entrypoint script
COPY services/koji-web/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy health check script
COPY services/koji-web/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/health-check.sh

# Set ownership
RUN chown -R koji:koji /etc/koji-web \
    /var/log/koji-web \
    /var/lib/koji-web \
    /usr/share/koji-web

# Switch to koji user
# USER koji

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=15s --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Start web service
CMD ["/usr/local/bin/entrypoint.sh"]
