# koji-habitude tools

FROM koji-boxed-common

COPY koji-habitude/ /mnt/koji-habitude/

RUN dnf install -qy \
    python3-click \
    python3-PyYAML

RUN python3 -m pip install --no-cache-dir /mnt/koji-habitude/

# The end.
