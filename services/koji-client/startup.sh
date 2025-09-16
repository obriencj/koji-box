
# --- Config (override with env) ---
INIT_DIR="${INIT_DIR:-/var/lib/koji-client/client-init.d}"   # place your init scripts here

# --- Run init scripts exactly once ---
run_init_scripts() {
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
    else
        echo "[entrypoint] No init directory found at $INIT_DIR"
    fi
}

run_init_scripts


# The end.
