# Container Socket Configuration Guide

This guide explains how to find and configure the correct socket path for different container runtimes used with the Koji Boxed system.

## Overview

The Orch service requires access to the container runtime socket to inspect containers when they request resources. The socket path varies depending on your container runtime and configuration.

## Supported Container Runtimes

### 1. Docker

Docker typically uses the standard Docker socket location:

```bash
# Standard Docker socket
PODMAN_SOCKET=/var/run/docker.sock
```

**Verification:**
```bash
# Check if Docker socket exists
ls -la /var/run/docker.sock

# Test Docker access
docker ps
```

### 2. Podman (Root Mode)

When running Podman as root, it uses the standard socket location:

```bash
# Root Podman socket
PODMAN_SOCKET=/var/run/podman.sock
```

**Verification:**
```bash
# Check if Podman socket exists
ls -la /var/run/podman.sock

# Test Podman access
sudo podman ps
```

### 3. Rootless Podman

Rootless Podman uses a user-specific socket location. The path varies by user ID and system configuration.

#### Finding Your Rootless Podman Socket

**Method 1: Check systemd user service**
```bash
# Check if podman.socket is running
systemctl --user status podman.socket

# Get the socket path from systemd
systemctl --user show podman.socket --property=ListenStream
```

**Method 2: Check common locations**
```bash
# Check user-specific socket locations
ls -la /run/user/$UID/podman/podman.sock
ls -la ~/.local/share/containers/podman/machine/podman-machine-default/podman.sock
ls -la /run/user/$UID/podman/podman.sock
```

**Method 3: Use podman info command**
```bash
# Get socket information from podman
podman info --format '{{.Host.RemoteSocket.Path}}'
```

**Method 4: Check environment variables**
```bash
# Check if DOCKER_HOST is set
echo $DOCKER_HOST

# Check if CONTAINER_HOST is set
echo $CONTAINER_HOST
```

#### Common Rootless Podman Socket Paths

```bash
# Most common rootless locations
PODMAN_SOCKET=/run/user/1000/podman/podman.sock
PODMAN_SOCKET=/run/user/$UID/podman/podman.sock
PODMAN_SOCKET=~/.local/share/containers/podman/machine/podman-machine-default/podman.sock
```

### 4. Podman with Docker Compatibility

If you're using Podman with Docker compatibility (podman-docker package), it may create a Docker-compatible socket:

```bash
# Docker-compatible socket
PODMAN_SOCKET=/var/run/docker.sock
```

## Configuration Steps

### Step 1: Identify Your Container Runtime

```bash
# Check what's available
which docker podman

# Check if services are running
systemctl status docker
systemctl --user status podman.socket
```

### Step 2: Find the Correct Socket Path

Use the verification methods above to find your socket path.

### Step 3: Update Environment Configuration

Edit your `.env` file (copied from `env.default`):

```bash
# Copy the default configuration
cp env.default .env

# Edit the configuration
nano .env
```

Update the `PODMAN_SOCKET` variable:

```bash
# Example for rootless podman
PODMAN_SOCKET=/run/user/1000/podman/podman.sock

# Example for root podman
PODMAN_SOCKET=/var/run/podman.sock

# Example for docker
PODMAN_SOCKET=/var/run/docker.sock
```

### Step 4: Test the Configuration

```bash
# Test with docker-compose
docker-compose config

# Check if the orch service can access the socket
docker-compose up orch-service
```

## Troubleshooting

### Common Issues

**1. Permission Denied**
```bash
# Check socket permissions
ls -la /var/run/docker.sock
ls -la /run/user/$UID/podman/podman.sock

# Add user to docker group (for Docker)
sudo usermod -aG docker $USER
```

**2. Socket Not Found**
```bash
# Start the podman socket service (for rootless podman)
systemctl --user start podman.socket

# Enable automatic startup
systemctl --user enable podman.socket
```

**3. Wrong Socket Path**
```bash
# Use podman info to find the correct path
podman info --format '{{.Host.RemoteSocket.Path}}'

# Check all available sockets
find /run -name "*podman*" -o -name "*docker*" 2>/dev/null
```

### Verification Commands

```bash
# Test socket access
curl --unix-socket /var/run/docker.sock http://localhost/version
curl --unix-socket /run/user/$UID/podman/podman.sock http://localhost/version

# Test with podman/docker commands
docker ps
podman ps
```

## Security Considerations

### Rootless Podman (Recommended)

Rootless Podman is more secure as it doesn't require root privileges:

```bash
# Enable rootless podman
echo 'kernel.unprivileged_userns_clone=1' | sudo tee /etc/sysctl.d/99-rootless-podman.conf
sudo sysctl --system

# Start rootless podman service
systemctl --user start podman.socket
systemctl --user enable podman.socket
```

### Docker Socket Security

The Docker socket provides full access to the Docker daemon. Use with caution:

```bash
# Only add trusted users to docker group
sudo usermod -aG docker $USER

# Consider using Docker rootless mode
dockerd-rootless-setuptool.sh install
```

## Examples by Distribution

### Ubuntu/Debian

```bash
# Install podman
sudo apt install podman

# Enable rootless podman
echo 'kernel.unprivileged_userns_clone=1' | sudo tee /etc/sysctl.d/99-rootless-podman.conf
sudo sysctl --system

# Start podman socket
systemctl --user start podman.socket
systemctl --user enable podman.socket

# Find socket path
systemctl --user show podman.socket --property=ListenStream
```

### Fedora/RHEL/CentOS

```bash
# Install podman
sudo dnf install podman

# Enable rootless podman (usually enabled by default)
systemctl --user start podman.socket
systemctl --user enable podman.socket

# Find socket path
podman info --format '{{.Host.RemoteSocket.Path}}'
```

### Arch Linux

```bash
# Install podman
sudo pacman -S podman

# Enable rootless podman
systemctl --user start podman.socket
systemctl --user enable podman.socket

# Find socket path
ls -la /run/user/$UID/podman/podman.sock
```

## Additional Resources

- [Podman Rootless Documentation](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md)
- [Docker Rootless Mode](https://docs.docker.com/engine/security/rootless/)
- [Podman Socket Configuration](https://github.com/containers/podman/blob/main/docs/source/markdown/podman-system-service.1.md)

## Need Help?

If you're still having trouble finding the correct socket path:

1. Check the logs: `docker-compose logs orch-service`
2. Verify your container runtime: `which docker podman`
3. Test socket access manually
4. Check systemd services: `systemctl --user status podman.socket`

The Orch service will log helpful error messages if it can't access the container socket.
