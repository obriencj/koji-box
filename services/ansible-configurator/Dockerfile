FROM registry.fedoraproject.org/fedora:39

# Install Ansible and dependencies
RUN dnf install -y \
    ansible \
    python3-psycopg2 \
    python3-requests \
    koji \
    krb5-workstation \
    && dnf clean all

# Create koji user (matching the koji-hub setup)
RUN groupadd -g 1000 koji && \
    useradd -u 1000 -g koji -m -s /bin/bash koji

# Set up working directory
WORKDIR /ansible

# Copy entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy ansible task modules
COPY tasks/ /ansible/tasks/

# Switch to koji user
USER koji

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["ansible-playbook", "site.yml"]
