FROM registry.fedoraproject.org/fedora:39

# Install Ansible and dependencies
RUN dnf install -y \
    ansible \
    python3-psycopg2 \
    python3-requests \
    koji \
    krb5-workstation \
    python3-pyyaml \
    && dnf clean all

# Create koji user (matching the koji-hub setup)
RUN groupadd -g 1000 koji && \
    useradd -u 1000 -g koji -m -s /bin/bash koji

# Set up working directory
WORKDIR /ansible

# Copy ansible infrastructure (baked in)
COPY ansible/ /ansible/
COPY validation/ /ansible/validation/

# Install ansible collections as koji user
USER koji
RUN ansible-galaxy collection install -r requirements.yml

# Copy entrypoint script
USER root
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Switch back to koji user for runtime
USER koji

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["ansible-playbook", "site.yml"]
