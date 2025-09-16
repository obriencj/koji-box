FROM koji-boxed-common


COPY services/koji-client/entrypoint.sh /app/entrypoint.sh
COPY services/koji-client/startup.sh /app/startup.sh
RUN chmod +x /app/*.sh

# Start client service (interactive shell)
CMD ["/app/entrypoint.sh"]

# The end.
