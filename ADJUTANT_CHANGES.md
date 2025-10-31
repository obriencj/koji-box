# Koji-Adjutant Integration Changes Summary

**Branch**: adjutant
**Date**: 2025-10-31
**Purpose**: Enable koji-adjutant testing in koji-boxed

---

## Files Modified

### 1. docker-compose.yml

**Lines**: ~252-269

**Changes**:
```yaml
koji-worker:
  build:
    additional_context:
      koji-adjutant: ../koji-adjutant  # NEW: Mount adjutant source for build
  volumes:
    - ${PODMAN_SOCKET:-/var/run/podman.sock}:/var/run/podman.sock  # NEW: Podman access
```

**Rationale**:
- Worker needs access to koji-adjutant source code
- Worker needs podman socket to spawn build containers (same pattern as orch service)

---

### 2. services/koji-worker/Dockerfile

**Lines**: 4-18, 39-44

**Changes**:
```dockerfile
# Added to package list
RUN dnf install -qy \
    podman \          # NEW: Podman for container execution
    ...

# NEW: Install podman Python bindings
RUN python3 -m pip install --no-cache-dir podman

# NEW: Install koji-adjutant
COPY koji-adjutant/ /mnt/koji-adjutant/
RUN python3 -m pip install --no-cache-dir -e /mnt/koji-adjutant/

# CHANGED: Use kojid from koji-adjutant instead of koji-src
RUN cp /mnt/koji-adjutant/koji_adjutant/kojid.py /app/kojid && chmod +x /app/kojid
```

**Rationale**:
- Podman package: Container runtime
- podman-py: Python library for podman API
- koji-adjutant: Our adapted build worker
- Modified kojid: Includes SRPM adapter integration

---

### 3. services/koji-worker/kojid.conf.template

**Lines**: 175-204 (end of file)

**Changes**:
```ini
# NEW SECTION: Koji-Adjutant Configuration

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

**Rationale**: Configure koji-adjutant behavior per Phase 2 ADRs

---

## Files Created

### 1. ADJUTANT_INTEGRATION.md

**Purpose**: Integration testing guide
**Size**: ~450 lines
**Contents**:
- Overview of changes
- Prerequisites and setup
- Testing workflows (4 test scenarios)
- Monitoring and debugging
- Troubleshooting guide
- Validation checklist

### 2. ADJUTANT_CHANGES.md

**Purpose**: This file - change summary
**Size**: ~200 lines

---

## Architecture

### Container Execution Flow

**Before (mock-based)**:
```
kojid → BuildRoot (mock chroot) → rpmbuild in chroot
```

**After (container-based)**:
```
kojid → Adapter → PodmanManager → Podman socket → Build container → rpmbuild in container
```

### Network Architecture

```
Host:
  ├─ Podman socket (/run/user/UID/podman/podman.sock)
  │
  └─ Docker Compose Network (koji-network)
      │
      ├─ koji-worker container (privileged)
      │   ├─ Mounts: /var/run/podman.sock
      │   ├─ Has: podman CLI + podman-py
      │   └─ Runs: kojid (from koji-adjutant)
      │       │
      │       └─ Spawns via podman socket:
      │           ├─ Build container 1 (SRPM build)
      │           ├─ Build container 2 (RPM build x86_64)
      │           └─ Build container 3 (RPM build aarch64)
      │
      └─ Other services (hub, orch, postgres, etc.)
```

---

## Integration Points

### 1. Podman Socket

**Source**: Host podman socket (rootless or rootful)
**Mounted at**: `/var/run/podman.sock` (in worker container)
**Pattern**: Same as orch-service (line 184 in docker-compose.yml)
**Requirement**: Socket must be running on host

### 2. Koji Storage

**Shared Volume**: `koji_storage` → `/mnt/koji`
**Used by**: Hub, worker, build containers
**Purpose**: Artifacts, logs, work directories
**SELinux**: Labeled with `:z` for sharing

### 3. Container Images

**Default**: `docker.io/almalinux/almalinux:9-minimal`
**Configurable**: Via `[adjutant]` section in kojid.conf
**Policy-driven**: Hub can override via build tag policies
**Pulled by**: Worker's podman (via socket)

### 4. Network Access

**Worker**: Has full network (internet access)
**Build containers**: Network enabled (for git clone)
**SCM checkout**: Can access public git repositories
**Isolation**: Each container has own network namespace

---

## Configuration Reference

### Required Environment Variables

```bash
# Podman socket location
PODMAN_SOCKET=/run/user/$(id -u)/podman/podman.sock  # rootless
# or
PODMAN_SOCKET=/var/run/podman.sock  # rootful

# Standard koji-boxed variables (unchanged)
KOJI_TOP_DIR=/mnt/koji
BUILDER_MAX_JOBS=10
BUILDER_ARGS=--force-lock --verbose
```

### adjutant Section Explained

```ini
[adjutant]
# Which container image to use for builds
task_image_default = docker.io/almalinux/almalinux:9-minimal

# When to pull images: always, if-not-present, never
image_pull_policy = if-not-present

# Enable network in build containers (required for git clone)
network_enabled = true

# Use hub policies for image selection (ADR 0003)
policy_enabled = true
policy_cache_ttl = 300

# Enable buildroot initialization (deps, repos, macros)
buildroot_enabled = true

# Enable monitoring HTTP API on port 8080
monitoring_enabled = true
monitoring_bind = 0.0.0.0:8080

# Volume mounts for build containers
container_mounts = /mnt/koji:/mnt/koji:rw:z

# Timeouts for container operations
container_timeouts = pull=300,start=60,stop_grace=20
```

---

## Compatibility

### Backward Compatibility

**Graceful Fallback**: If koji-adjutant not available, kojid uses original mock-based execution

**Mechanism**:
```python
# In kojid.py
try:
    from koji_adjutant.task_adapters.rebuild_srpm import RebuildSRPMAdapter
    # Use adapter
except ImportError:
    # Use original BuildRoot (mock)
```

**Benefit**: Can run with or without koji-adjutant

### Forward Compatibility

**Additional task types**: Adapters for maven, image builds can be added in Phase 3

**SCM types**: SVN/CVS handlers can be added without changing architecture

**Hub policies**: Can configure per-tag image selection without code changes

---

## Security Considerations

### Podman Socket Access

**Risk**: Worker has access to host podman socket (can create containers on host)
**Mitigation**:
- Worker runs as koji user (uid 1000)
- Podman socket permissions restrict access
- Containers isolated with SELinux labels
- No privileged containers spawned by adjutant

### Build Container Isolation

**Network**: Containers have network access (required for git clone)
**Filesystem**: Only /mnt/koji and /work/<task_id> mounted
**User**: Containers run as koji user (uid 1000)
**SELinux**: All mounts labeled (Z or z)

### Container Images

**Trust**: Using official AlmaLinux images from docker.io
**Validation**: Images pulled from registry
**Future**: Use internal registry or pre-built images (ADR 0004)

---

## Differences from Mock-based Worker

| Aspect | Mock-based | Adjutant (Container-based) |
|--------|------------|----------------------------|
| **Isolation** | Chroot | Container (stronger) |
| **Cleanup** | Manual | Automatic (guaranteed) |
| **Image** | Mock config | Container image (policy-driven) |
| **Network** | Mock settings | Container network |
| **Startup** | Mock init (~30s) | Container start (~2s) |
| **Monitoring** | Limited | HTTP API available |
| **Debugging** | Mock logs | Container logs + exec access |

---

## Testing Matrix

| Task Type | Mock-based | Adjutant | Status |
|-----------|------------|----------|--------|
| **buildArch** | Yes | Yes | ✅ Validated |
| **createrepo** | Yes | Yes | ✅ Validated |
| **rebuildSRPM** | Yes | Yes | ✅ NEW - Phase 2.5 Week 1 |
| **buildSRPMFromSCM** | Yes | Yes | ✅ NEW - Phase 2.5 Week 2 |
| **maven** | Yes | No | Phase 3 |
| **image** | Yes | No | Phase 3 |
| **Other tasks** | Yes | Fallback | Uses mock |

---

## Performance Expectations

Based on Phase 2 measurements:

| Metric | Mock-based | Adjutant | Overhead |
|--------|------------|----------|----------|
| **Container startup** | ~30s (mock init) | ~2s | -93% (faster!) |
| **Build execution** | Baseline | +2-5% | < 5% |
| **Cleanup** | ~10s | ~1s | -90% (faster!) |
| **Total overhead** | - | - | < 5% overall |

**Expected for SRPM tasks**:
- RebuildSRPM: < 3% overhead (simpler than buildArch)
- BuildSRPMFromSCM: < 8% overhead (git clone adds time)

---

## Next Steps

### Immediate Testing (Today)
1. Build worker: `docker compose build koji-worker`
2. Start environment: `docker compose up -d`
3. Check worker health: `docker compose ps koji-worker`
4. Test RebuildSRPM: Submit rebuild task
5. Test BuildSRPMFromSCM: Submit git build
6. Validate complete workflow: `koji build f39 git://...`

### Integration Validation (This Week)
1. Run all test scenarios from ADJUTANT_INTEGRATION.md
2. Monitor performance and resource usage
3. Document any issues or unexpected behavior
4. Collect metrics for Phase 2.5 completion report

### After Successful Testing
1. Update koji-adjutant PROJECT_STATUS.md
2. Create koji-boxed integration report
3. Plan production deployment
4. Consider merging "adjutant" branch

---

## Change Summary

**Files Modified**: 3
- docker-compose.yml
- services/koji-worker/Dockerfile
- services/koji-worker/kojid.conf.template

**Files Created**: 2
- ADJUTANT_INTEGRATION.md (testing guide)
- ADJUTANT_CHANGES.md (this file)

**Lines Changed**: ~50 lines modified, ~450 lines documentation

**Impact**: Enables complete container-based build workflow in koji-boxed

---

**Status**: ✅ READY FOR TESTING

**Command to start**:
```bash
export PODMAN_SOCKET=/run/user/$(id -u)/podman/podman.sock
cd /home/siege/koji-boxed
docker compose build koji-worker
docker compose up -d
```

---
