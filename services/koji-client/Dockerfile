FROM koji-boxed-common


COPY services/koji-client/entrypoint.sh /app/entrypoint.sh
COPY services/koji-client/startup.sh /app/startup.sh
RUN chmod +x /app/*.sh

CMD ["/app/entrypoint.sh"]

# The end.
