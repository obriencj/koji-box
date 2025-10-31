# Koji-Adjutant Integration Guide for Koji-Boxed

**Branch**: adjutant
**Date**: 2025-10-31
**Purpose**: Integration testing of koji-adjutant SRPM adapters

---

## Overview

This branch integrates koji-adjutant (podman-based build worker) into koji-boxed for integration testing. The worker now uses containerized builds instead of mock chroots while remaining fully compatible with the koji hub.

**What Changed**:
- koji-worker now includes koji-adjutant modules
- Podman socket mounted from host (like orch service)
- kojid uses koji-adjutant's modified version
- Container-based task execution for: buildArch, createrepo, rebuildSRPM, buildSRPMFromSCM

---

## Changes Made

### 1. docker-compose.yml

**Modified**: `koji-worker` service

**Changes**:
```yaml
additional_context:
  koji-adjutant: ../koji-adjutant  # Mount adjutant source

volumes:
  - ${PODMAN_SOCKET:-/var/run/podman.sock}:/var/run/podman.sock  # Podman access
```

**Rationale**: Worker needs podman socket to spawn build containers

---

### 2. services/koji-worker/Dockerfile

**Changes**:
```dockerfile
# Added podman package
RUN dnf install -qy podman ...

# Added podman-py for Python bindings
RUN python3 -m pip install --no-cache-dir podman

# Install koji-adjutant
COPY koji-adjutant/ /mnt/koji-adjutant/
RUN python3 -m pip install --no-cache-dir -e /mnt/koji-adjutant/

# Use kojid from koji-adjutant (not koji-src)
RUN cp /mnt/koji-adjutant/koji_adjutant/kojid.py /app/kojid
```

**Rationale**:
- Podman needed to interact with containers
- koji-adjutant provides adapted kojid with container support
- Editable install allows live updates

---

### 3. services/koji-worker/kojid.conf.template

**Added**: `[adjutant]` section at end

```ini
[adjutant]
task_image_default = docker.io/almalinux/almalinux:9-minimal
image_pull_policy = if-not-present
network_enabled = true
policy_enabled = true
policy_cache_ttl = 300
buildroot_enabled = true
monitoring_enabled = true
monitoring_bind = 0.0.0.0:8080
container_mounts = /mnt/koji:/mnt/koji:rw:z
container_timeouts = pull=300,start=60,stop_grace=20
```

**Rationale**: Configure koji-adjutant behavior per ADR 0003

---

## Prerequisites

### Host Requirements

**Podman Socket**:
```bash
# Ensure podman socket is running (rootless or rootful)
systemctl --user status podman.socket
# or
sudo systemctl status podman.socket

# If not running:
systemctl --user enable --now podman.socket
# or
sudo systemctl enable --now podman.socket
```

**Environment Variable**:
```bash
# For rootless podman (recommended):
export PODMAN_SOCKET=/run/user/$(id -u)/podman/podman.sock

# For rootful podman:
export PODMAN_SOCKET=/var/run/podman.sock

# Add to .env or env.default
echo "PODMAN_SOCKET=/run/user/$(id -u)/podman/podman.sock" >> env.default
```

### Container Image

**Pre-pull build image** (optional but recommended):
```bash
podman pull docker.io/almalinux/almalinux:9-minimal
```

---

## Building and Starting

### Build Services

```bash
cd /home/siege/koji-boxed

# Rebuild koji-worker with adjutant
docker compose build koji-worker

# Or rebuild all services
docker compose build
```

### Start Environment

```bash
# Start core services
docker compose up -d postgres kdc orch-service koji-hub

# Start worker with adjutant
docker compose up -d koji-worker --scale koji-worker=1

# Check status
docker compose ps
```

### Verify Worker Started

```bash
# Check worker logs
docker compose logs koji-worker -f

# Should see:
# - kojid starting
# - koji-adjutant modules imported
# - "Using container-based execution" messages

# Check monitoring API (if enabled)
curl http://localhost:8080/api/v1/status
# Should return: {"status": "ok", ...}
```

---

## Testing Workflows

### Test 1: RebuildSRPM Task

**Scenario**: Rebuild an existing SRPM

**Prerequisites**:
- Existing SRPM file in koji storage
- Build tag configured

**Test Command**:
```bash
# Enter koji-client container
docker compose exec koji-client bash

# Submit rebuild task
koji call rebuildSRPM work/<old_task_id>/package.src.rpm f39-build '{"repo_id": 1}'

# Monitor task
koji watch-task <task_id>

# Expected: Task completes successfully, new SRPM with correct dist tag created
```

**Validation**:
```bash
# Check logs for container execution
docker compose logs koji-worker | grep "Using container-based SRPM rebuild"

# Check monitoring API
curl http://localhost:8080/api/v1/tasks/<task_id>

# Verify SRPM created
ls -lh /mnt/koji/work/<task_id>/result/*.src.rpm
```

---

### Test 2: BuildSRPMFromSCM Task (CRITICAL)

**Scenario**: Build SRPM from git repository

**Prerequisites**:
- Build tag configured
- Network access from worker container
- Git repository accessible

**Test Command**:
```bash
# Enter koji-client container
docker compose exec koji-client bash

# Submit SCM build task
koji call buildSRPMFromSCM 'git://example.com/test-package.git' f39-build '{"repo_id": 1}'

# Or use a real test repo:
koji call buildSRPMFromSCM 'https://github.com/<user>/<simple-test-package>.git' f39-build '{"repo_id": 1}'

# Monitor task
koji watch-task <task_id>

# Expected:
# - Git checkout successful
# - SRPM built from source
# - Task completes successfully
```

**Validation**:
```bash
# Check logs for SCM checkout
docker compose logs koji-worker | grep -i "git clone"

# Check logs for container execution
docker compose logs koji-worker | grep "Using container-based"

# Verify SRPM created
ls -lh /mnt/koji/work/<task_id>/result/*.src.rpm

# Check monitoring API
curl http://localhost:8080/api/v1/tasks/<task_id>
```

---

### Test 3: Complete RPM Build (END-TO-END)

**Scenario**: Full workflow: git → SRPM → RPMs

**Test Command**:
```bash
# Enter koji-client container
docker compose exec koji-client bash

# Submit complete build
koji build f39-candidate 'git://example.com/test-package.git'

# Or with real package
koji build f39-candidate 'https://github.com/<user>/<test-package>.git'

# Monitor build
koji watch-logs <build_id>

# Expected workflow:
# 1. BuildSRPMFromSCM subtask spawns (uses BuildSRPMFromSCMAdapter)
# 2. Git checkout → SRPM built
# 3. BuildArch subtasks spawn (use BuildArchAdapter)
# 4. RPMs built for each arch
# 5. Build completes successfully
```

**Validation**:
```bash
# Check task tree
koji taskinfo <build_task_id> --verbose

# Verify SRPM created
ls -lh /mnt/koji/work/<srpm_task_id>/result/*.src.rpm

# Verify RPMs created
ls -lh /mnt/koji/work/<buildarch_task_id>/result/*.rpm

# Check all containers cleaned up
podman ps -a --filter label=io.koji.adjutant.task_id
# Should be empty (all cleaned up)

# Check monitoring
curl http://localhost:8080/api/v1/status
```

---

### Test 4: Createrepo Task

**Scenario**: Verify createrepo still works

**Test Command**:
```bash
docker compose exec koji-client bash

# Submit createrepo task
koji regen-repo f39-build

# Monitor
koji watch-task <task_id>
```

**Validation**:
```bash
# Check repodata created
ls -lh /mnt/koji/repos/f39-build/latest/x86_64/repodata/

# Verify used container
docker compose logs koji-worker | grep createrepo
```

---

## Monitoring and Debugging

### Monitoring API

**Available at**: `http://localhost:8080/api/v1/`

**Endpoints**:
```bash
# Worker status
curl http://localhost:8080/api/v1/status

# Active containers
curl http://localhost:8080/api/v1/containers

# Task details
curl http://localhost:8080/api/v1/tasks/<task_id>

# Active tasks
curl http://localhost:8080/api/v1/tasks
```

### Logs

**Worker logs**:
```bash
# Follow worker logs
docker compose logs worker -f

# Grep for adapter activity
docker compose logs worker | grep "container-based"

# Grep for errors
docker compose logs worker | grep -i error
```

**Task logs**:
```bash
# Container logs (persisted)
cat /mnt/koji/logs/<task_id>/container.log

# Buildroot initialization logs
cat /mnt/koji/work/<task_id>/buildroot.log
```

**Podman logs**:
```bash
# Inside worker container
docker compose exec koji-worker bash

# List containers (including exited)
podman ps -a --filter label=io.koji.adjutant.task_id

# View container logs
podman logs <container_id>
```

### Debug Mode

**Enable verbose logging**:
```bash
# In docker-compose.yml or via environment
BUILDER_ARGS="--force-lock --verbose --debug"

# Restart worker
docker compose restart koji-worker
```

**Check buildroot initialization**:
```bash
# View generated files
cat /mnt/koji/work/<task_id>/koji.repo
cat /mnt/koji/work/<task_id>/macros.koji
```

---

## Troubleshooting

### Issue 1: Podman socket not accessible

**Symptom**: Worker logs show "Failed to connect to podman"

**Solution**:
```bash
# Check socket exists on host
ls -l $PODMAN_SOCKET

# Verify socket is running
systemctl --user status podman.socket

# Check socket permissions
# Worker runs as koji (uid 1000), should have access

# Inside worker container:
docker compose exec koji-worker ls -l /var/run/podman.sock
```

### Issue 2: Image pull fails

**Symptom**: "Failed to pull image docker.io/almalinux/almalinux:9-minimal"

**Solution**:
```bash
# Pull image on host first
podman pull docker.io/almalinux/almalinux:9-minimal

# Or inside worker:
docker compose exec koji-worker podman pull docker.io/almalinux/almalinux:9-minimal
```

### Issue 3: Network not available for SCM checkout

**Symptom**: "git clone failed: Could not resolve host"

**Solution**:
```bash
# Check network_enabled in kojid.conf
docker compose exec koji-worker cat /etc/kojid/kojid.conf | grep network_enabled
# Should be: network_enabled = true

# Test DNS inside build container manually
docker compose exec koji-worker podman run --rm docker.io/almalinux/almalinux:9-minimal ping -c 1 github.com
```

### Issue 4: Container cleanup not working

**Symptom**: Orphaned containers accumulating

**Solution**:
```bash
# List all koji-adjutant containers
podman ps -a --filter label=io.koji.adjutant.task_id

# Manual cleanup
podman rm -f $(podman ps -aq --filter label=io.koji.adjutant.task_id)

# Check worker logs for cleanup errors
docker compose logs koji-worker | grep -i cleanup
```

### Issue 5: Permission denied in buildroot

**Symptom**: "Permission denied" during SRPM build

**Solution**:
```bash
# Check SELinux labels on mounts
docker compose exec koji-worker ls -lZ /mnt/koji

# Should show proper context (svirt_sandbox_file_t or similar)

# If issues, try :z or :Z label
# Already configured in kojid.conf.template: container_mounts = /mnt/koji:/mnt/koji:rw:z
```

---

## Performance Monitoring

### Measure Build Times

```bash
# Start build and time it
time koji build f39-candidate git://example.com/package.git

# Compare to mock-based worker (if available)
```

### Container Metrics

```bash
# Inside worker
docker compose exec koji-worker bash

# Monitor containers during build
watch -n 1 'podman ps --filter label=io.koji.adjutant.task_id'

# Check resource usage
podman stats <container_id>
```

---

## Expected Behavior

### Adapter Detection

**Worker logs should show**:
```
Using container-based SRPM rebuild execution
Using container-based buildArch execution
Using container-based createrepo execution
```

**If adapters not available (fallback)**:
```
Adapter not available, using mock-based buildroot
```

### Task Execution Flow

**For `koji build f39 git://...`**:

1. **BuildSRPMFromSCMTask spawns**
   - Logs: "Using container-based execution"
   - Container created with network enabled
   - Git clone executes
   - SRPM built from source
   - Container cleaned up

2. **BuildArch subtasks spawn** (parallel)
   - Logs: "Using container-based buildArch execution"
   - Containers created per architecture
   - RPMs built
   - Containers cleaned up

3. **Build completes**
   - All artifacts uploaded
   - Task tree shows success
   - No orphaned containers

---

## Validation Checklist

### Pre-flight Checks
- [ ] Podman socket accessible from host
- [ ] koji-adjutant source at `/home/siege/koji-adjutant`
- [ ] koji-boxed on "adjutant" branch
- [ ] Base image pulled: `docker.io/almalinux/almalinux:9-minimal`

### Build Checks
- [ ] Worker builds successfully
- [ ] No build errors in Dockerfile
- [ ] koji-adjutant installed in worker
- [ ] kojid is from koji-adjutant

### Runtime Checks
- [ ] Worker starts and stays healthy
- [ ] kojid process running
- [ ] Monitoring API responds (port 8080)
- [ ] Worker registered with hub

### Functional Checks
- [ ] Can rebuild SRPM (rebuildSRPM task)
- [ ] Can build SRPM from git (buildSRPMFromSCM task)
- [ ] Can build RPMs from SRPM (buildArch task)
- [ ] Complete build workflow succeeds (git → SRPM → RPM)
- [ ] Createrepo task works
- [ ] Containers cleaned up after tasks

### Performance Checks
- [ ] Build time acceptable (< 10% overhead)
- [ ] No memory leaks
- [ ] No container accumulation

---

## Quick Start Commands

### 1. Build and Start
```bash
cd /home/siege/koji-boxed

# Set podman socket
export PODMAN_SOCKET=/run/user/$(id -u)/podman/podman.sock  # or /var/run/podman.sock

# Build worker
docker compose build koji-worker

# Start environment
docker compose up -d

# Scale worker
docker compose up -d --scale koji-worker=1

# Check health
docker compose ps
```

### 2. Submit Test Build
```bash
# Enter client
docker compose exec koji-client bash

# Simple test (if you have a test SRPM)
koji call rebuildSRPM work/test/package.src.rpm f39-build '{"repo_id": 1}'

# Full workflow test (if you have a git repo)
koji build f39-candidate git://your-test-repo.git

# Watch progress
koji watch-logs <build_id>
```

### 3. Monitor
```bash
# Worker logs
docker compose logs koji-worker -f

# Monitoring API
curl http://localhost:8080/api/v1/status

# Active containers
curl http://localhost:8080/api/v1/containers
```

### 4. Cleanup
```bash
# Stop worker
docker compose stop koji-worker

# Remove orphaned containers (if any)
podman rm -f $(podman ps -aq --filter label=io.koji.adjutant.task_id) 2>/dev/null || true

# Restart worker
docker compose up -d koji-worker
```

---

## Test Packages

### Create Simple Test Package

**Minimal spec for testing**:
```bash
# Create test git repo with simple spec
mkdir test-package
cd test-package

cat > test-package.spec << 'SPEC'
Name:           test-package
Version:        1.0
Release:        1%{?dist}
Summary:        Simple test package for koji-adjutant

License:        MIT
URL:            https://example.com

%description
Simple test package for validating koji-adjutant SRPM adapters.

%prep
# No sources needed

%build
# Nothing to build

%install
mkdir -p %{buildroot}/usr/share/doc/%{name}
echo "Test package" > %{buildroot}/usr/share/doc/%{name}/README

%files
/usr/share/doc/%{name}/README

%changelog
* Thu Oct 31 2025 Test User <test@example.com> - 1.0-1
- Initial test package
SPEC

# Init git repo
git init
git add test-package.spec
git commit -m "Initial commit"

# Push to accessible git server or use local path
```

### Using Local Git Repo

```bash
# Make test repo available to worker
docker compose cp test-package koji-worker:/tmp/test-package

# Inside worker
docker compose exec koji-worker bash
cd /tmp/test-package
git daemon --base-path=/tmp --export-all --reuseaddr &

# Use URL: git://koji-worker.koji.box/test-package
```

---

## Success Criteria

Integration testing is successful when:

✅ **RebuildSRPM works**
- Task completes successfully
- SRPM rebuilt with correct dist tags
- Container created and cleaned up
- Logs show container execution

✅ **BuildSRPMFromSCM works**
- Git checkout successful
- SRPM built from checked-out source
- Container created and cleaned up
- SCM metadata in result

✅ **Complete workflow works**
- `koji build f39 git://...` succeeds
- BuildSRPMFromSCM → BuildArch chain works
- All containers cleaned up
- Build artifacts uploaded

✅ **No regressions**
- BuildArch still works
- Createrepo still works
- Hub compatibility maintained

✅ **Performance acceptable**
- Build time < 10% slower than mock-based
- No resource leaks
- Monitoring responsive

---

## Rollback Plan

**If integration issues**:

```bash
# Stop worker
docker compose stop koji-worker

# Switch to original koji-worker (mock-based)
git checkout main

# Rebuild and restart
docker compose build koji-worker
docker compose up -d koji-worker
```

**Or revert specific changes**:
- Comment out podman socket mount
- Use original kojid from koji-src
- Disable `[adjutant]` section

---

## Known Limitations

### Current Scope
- Git support only (no SVN/CVS yet)
- Public repos only (no private repo auth yet)
- AlmaLinux 9 minimal images (configurable)
- Network always enabled (no per-tag policies yet)

### Future Enhancements (Phase 3)
- SVN/CVS support
- Private repository authentication
- Per-tag network policies
- Container image caching
- Advanced monitoring dashboards

---

## Support

**Issues with koji-adjutant**:
- Check: `/home/siege/koji-adjutant/docs/`
- ADRs: `/home/siege/koji-adjutant/docs/architecture/decisions/`
- WORKFLOW: `/home/siege/koji-adjutant/docs/WORKFLOW.md`

**Issues with koji-boxed**:
- Check: `/home/siege/koji-boxed/README.md`
- SOCKET_README: `/home/siege/koji-boxed/SOCKET_README.md`

**Debugging**:
- Worker logs: `docker compose logs koji-worker`
- Task logs: `/mnt/koji/logs/<task_id>/`
- Monitoring: `http://localhost:8080/api/v1/`

---

## Next Steps After Validation

**When integration tests pass**:

1. **Document Results**
   - Update koji-adjutant PROJECT_STATUS.md
   - Create integration test report
   - Document any issues found

2. **Prepare for Staging**
   - Build production container images
   - Configure hub policies
   - Create operator documentation

3. **Production Pilot**
   - Low-risk builds first
   - Monitor performance
   - Gather operator feedback

---

**Integration Guide Status**: ✅ READY

**Start testing with**: `docker compose up -d && docker compose logs koji-worker -f`

**Questions?** Check troubleshooting section or review koji-adjutant docs!

---
