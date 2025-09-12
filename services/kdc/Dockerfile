FROM alpine

# Set environment variables
ENV KRB5_REALM=${KRB5_REALM:-KOJI.BOX}
ENV KRB5_KDC=${KRB5_KDC:-localhost}
ENV KRB5_ADMIN_SERVER=${KRB5_ADMIN_SERVER:-localhost}

RUN apk add --update krb5 krb5-server tini bash gettext envsubst

# # Install Kerberos and dependencies
# RUN apt-get update && apt-get install -y \
#     krb5-kdc \
#     krb5-admin-server \
#     krb5-user \
#     krb5-config \
#     bash \
#     tini && \
#     rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /var/lib/krb5kdc \
    /etc/krb5kdc \
    /var/log/krb5kdc

# Copy entry point script
COPY services/kdc/entry-point.sh /bin/entry-point.sh
RUN chmod +x /bin/entry-point.sh

# Copy health check script
COPY services/kdc/health-check.sh /bin/health-check.sh
RUN chmod +x /bin/health-check.sh

# Copy configuration templates
COPY services/kdc/kdc.conf.template /etc/krb5kdc/
COPY services/kdc/kadm5.acl.template /etc/krb5kdc/
COPY services/common/krb5.conf.template /etc/krb5kdc/

# RUN addgroup -g 1000 krb5 && \
#     adduser -D -u 1000 -G krb5 krb5

# Expose ports
EXPOSE 88 749 464

# Start KDC service
ENTRYPOINT ["/sbin/tini", "-g", "--", "/bin/entry-point.sh"]

# The end.
