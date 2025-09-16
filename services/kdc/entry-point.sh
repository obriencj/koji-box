#!/usr/bin/env bash
set -Eeuo pipefail

# --- Config (override with env) ---
KRB5_REALM="${KRB5_REALM:-KOJI.BOX}"

# Ensure KRB5_REALM is set for template expansion
KDC_OPTS=${KDC_OPTS:-"-n"}            # krb5kdc in foreground
KADMIN_OPTS=${KADMIN_OPTS:-"-nofork"} # kadmind in foreground
INIT_DIR="${INIT_DIR:-/var/lib/krb5kdc/kdc-init.d}"   # place your init scripts here
KADMIN_PRINC="${KADMIN_PRINC:-admin/admin}"
KADMIN_PASS="${KADMIN_PASS:-admin_password}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-30}"     # seconds to wait for kadmind RPC readiness

# expand configuration templates
echo "[entrypoint] Expanding kdc.conf template..."
envsubst < /etc/krb5kdc/kdc.conf.template > /etc/krb5kdc/kdc.conf

echo "[entrypoint] Expanding kadm5.acl template..."
envsubst < /etc/krb5kdc/kadm5.acl.template > /etc/krb5kdc/kadm5.acl

echo "[entrypoint] Expanding krb5.conf template..."
envsubst < /etc/krb5kdc/krb5.conf.template > /etc/krb5kdc/krb5.conf

# copy configuration files
echo "[entrypoint] Copying configuration files..."
cp /etc/krb5kdc/krb5.conf /etc/krb5.conf
cp /etc/krb5kdc/kdc.conf /var/lib/krb5kdc/kdc.conf
cp /etc/krb5kdc/kadm5.acl /var/lib/krb5kdc/kadm5.acl

# ensure initial database is created
if [ ! -f /var/lib/krb5kdc/principal ]; then
  echo "Initial database not found, creating..."
  kdb5_util create -r $KRB5_REALM -s -P ${KRB5_MASTER_PASSWORD:-master_password}
fi


# --- Start both services (non-daemonized) ---
krb5kdc $KDC_OPTS &
PID_KDC=$!

kadmind $KADMIN_OPTS &
PID_KADMIN=$!

# --- Signal fan-out ---
term() { kill -TERM "$PID_KDC" "$PID_KADMIN" 2>/dev/null || true; }
quit() { kill -QUIT "$PID_KDC" "$PID_KADMIN" 2>/dev/null || true; }
hup()  { kill -HUP  "$PID_KDC" "$PID_KADMIN" 2>/dev/null || true; }
trap term TERM INT
trap quit QUIT
trap hup HUP

# --- Optional: wait for kadmind to be ready (RPC on 749) ---
wait_kadmind() {
  local end=$((SECONDS + WAIT_TIMEOUT))
  while (( SECONDS < end )); do
    if kadmin -p "$KADMIN_PRINC" -w "$KADMIN_PASS" -q "getprinc $KADMIN_PRINC" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "[entrypoint] WARNING: kadmind not confirmed ready after ${WAIT_TIMEOUT}s; continuing anyway." >&2
  return 1
}
wait_kadmind || true
touch /var/lib/krb5kdc/kadmind-ready

# --- Run init scripts exactly once (they may exit; we ignore their exit codes) ---
if [[ -d "$INIT_DIR" ]]; then
  echo "[entrypoint] Running init scripts in $INIT_DIR ..."
  # Sort to get a stable order (e.g., 00-foo.sh, 10-bar.sh)
  while IFS= read -r -d '' f; do
    if [[ -x "$f" ]]; then
      echo "[entrypoint] -> $f"
      # Let scripts exit with non-zero without killing the container:
      set +e
      "$f"
      rc=$?
      set -e
      echo "[entrypoint] <- $f (exit $rc)"
    else
      echo "[entrypoint] WARNING: $f is not executable"
    fi
  done < <(find "$INIT_DIR" -maxdepth 1 -type f -iname "*.sh" -print0 | sort -z)

  echo "[entrypoint] Init complete."
fi
touch /var/lib/krb5kdc/kdc-init-complete

# --- If either daemon exits, shut down the other and exit with its status ---
wait -n "$PID_KDC" "$PID_KADMIN"
STATUS=$?

kill -TERM "$PID_KDC" "$PID_KADMIN" 2>/dev/null || true
for i in {1..15}; do
  kill -0 "$PID_KDC" 2>/dev/null || unset PID_KDC
  kill -0 "$PID_KADMIN" 2>/dev/null || unset PID_KADMIN
  [[ -z "${PID_KDC:-}" && -z "${PID_KADMIN:-}" ]] && break
  sleep 1
done
kill -KILL ${PID_KDC:-} ${PID_KADMIN:-} 2>/dev/null || true

exit "$STATUS"

# The end.
