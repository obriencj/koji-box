FROM koji-boxed-common

# Set up working directory
WORKDIR /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY ansible.sh /app/ansible.sh
RUN chmod +x /app/ansible.sh

# Copy ansible infrastructure (baked in)
COPY ansible/ /app/ansible/
COPY validation/ /app/ansible/validation/

# Install ansible collections as koji user
RUN su koji -c "ansible-galaxy collection install -r requirements.yml"

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["ansible-playbook", "site.yml"]

# The end.
