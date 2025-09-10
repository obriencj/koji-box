FROM postgres:15-alpine

# Install additional packages
RUN apk add --no-cache \
    curl \
    bash \
    postgresql-contrib

# Set environment variables
ENV POSTGRES_INITDB_ARGS="--encoding=UTF8 --locale=C"

# Create directories
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy initialization script
# COPY init-koji.sql /docker-entrypoint-initdb.d/

# Set proper permissions
# RUN chmod 644 /docker-entrypoint-initdb.d/init-koji.sql

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB

# Expose port
EXPOSE 5432

# Use default postgres entrypoint
CMD ["postgres"]
