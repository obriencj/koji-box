# Install system dependencies - consolidated from koji-hub and koji-worker


# We need to be running on almalinux:10 in order to have a version of
# createrepo_c that is compatible with modern fedora repositories. But
# unfortunately, almalinux:10 EPEL doesn't include tini, which we need for hub
# and worker and web. So we'll fetch the tini srpm from almalinux:9 and rebuild
# it on almalinux:10 and then install that in our base image.


FROM almalinux:9 as tini-srpm

RUN dnf install -qy dnf-plugins-core epel-release && \
    dnf config-manager --set-enabled crb

RUN dnf install -qy yum-utils
RUN yumdownloader --source tini


FROM almalinux:10 as build-tini

RUN dnf install -qy dnf-plugins-core epel-release && \
    dnf config-manager --set-enabled crb

WORKDIR /build-tini
RUN mkdir -p /build-tini/SRPMS /build-tini/RPMS

COPY --from=tini-srpm /tini-*.src.rpm /build-tini/SRPMS/tini-*.src.rpm

RUN dnf install -qy rpm-build && \
    dnf builddep -qy /build-tini/SRPMS/tini-*.src.rpm && \
    rpmbuild -rb /build-tini/SRPMS/tini-*.src.rpm  && \
    mv /root/rpmbuild/RPMS/*/*.rpm /build-tini/RPMS/

RUN ls /build-tini/RPMS/


FROM almalinux:10

RUN dnf install -qy dnf-plugins-core epel-release && \
    dnf config-manager --set-enabled crb

RUN dnf install -qy \
    bash \
    diffutils \
    gettext \
    git \
    jq \
    krb5-workstation \
    make \
    openssl \
    procps-ng \
    python3 \
    python3-dateutil \
    python3-defusedxml \
    python3-devel \
    python3-gssapi \
    python3-jinja2 \
    python3-pyOpenSSL \
    python3-pip \
    python3-psycopg2 \
    python3-requests \
    python3-requests-gssapi \
    python3-setuptools \
    python3-six \
    python3-wheel \
    shadow-utils \
    util-linux \
    which && \
    dnf clean all

COPY --from=build-tini /build-tini/RPMS/ /tmp/tini/
RUN dnf install -qy $(ls -d /tmp/tini/*.rpm | grep 'tini-[0-9].*rpm$') && \
    rm -rf /tmp/tini/

# Create koji user and group with consistent IDs
RUN groupadd -g 1000 koji && \
    useradd -u 1000 -g koji -m -s /bin/bash koji

# Copy and install Koji source
ENV PIP_ROOT_USER_ACTION=ignore
COPY koji-src/ /mnt/koji-src/
RUN python3 -m pip install --no-cache-dir /mnt/koji-src/

# Copy common configuration templates
COPY services/common/krb5.conf.template /app/krb5.conf.template
COPY services/common/koji.conf.template /app/koji.conf.template
COPY services/common/configure.sh /app/configure.sh
COPY services/common/orch.sh /app/orch.sh
RUN chmod +x /app/configure.sh /app/orch.sh

# Set up common ownership
RUN mkdir -p /mnt/koji /etc/koji-common && \
    chown -R koji:koji /mnt/koji /etc/koji-common

# The end.
