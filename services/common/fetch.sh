#!/bin/bash
# Simple Keytab Service Client
# Lightweight script for use within containers

set -e

# Default configuration
KEYTAB_SERVICE_URL="${KEYTAB_SERVICE_URL:-http://keytabs.koji.box:5000}"
KRB5_REALM="${KRB5_REALM:-KOJI.BOX}"

# Function to show usage
usage() {
    echo "Usage: $0 <command> <argument> <output_file>"
    echo ""
    echo "Commands:"
    echo "  principal <name> <file>   Fetch keytab for principal"
    echo "  worker <name> <file>      Fetch keytab and register worker"
    echo "  cert <cn> <file>          Fetch SSL certificate"
    echo "  key <cn> <file>           Fetch SSL private key"
    echo "  health                    Check service health"
    echo ""
    echo "Examples:"
    echo "  $0 principal myuser@${KRB5_REALM} /tmp/myuser.keytab"
    echo "  $0 worker worker1 /tmp/worker1.keytab"
    echo "  $0 cert my-service.koji.box /tmp/my-service.crt"
    echo "  $0 key my-service.koji.box /tmp/my-service.key"
    exit 1
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
fi

command="$1"
arg="$2"
output_file="$3"

# Normalize principal name
normalize_principal() {
    local principal="$1"
    if [[ ! "$principal" == *"@$KRB5_REALM" ]]; then
        principal="${principal}@${KRB5_REALM}"
    fi
    echo "$principal"
}

# Make HTTP request
fetch_file() {
    local url="$1"
    local output="$2"

    # Create output directory if needed
    mkdir -p "$(dirname "$output")"

    if curl -L -s -o "$output" "$url"; then
        echo "✓ Saved to $output"
    else
        echo "✗ Failed to fetch from $url"
        rm -f "$output"
        exit 1
    fi
}

# Handle commands
case "$command" in
    principal)
        if [ -z "$arg" ] || [ -z "$output_file" ]; then
            echo "Error: principal command requires <name> and <output_file>"
            usage
        fi
        normalized_principal=$(normalize_principal "$arg")
        fetch_file "${KEYTAB_SERVICE_URL}/api/v1/principal/${normalized_principal}" "$output_file"
        ;;
    worker)
        if [ -z "$arg" ] || [ -z "$output_file" ]; then
            echo "Error: worker command requires <name> and <output_file>"
            usage
        fi
        fetch_file "${KEYTAB_SERVICE_URL}/api/v1/worker/${arg}" "$output_file"
        ;;
    cert)
        if [ -z "$arg" ] || [ -z "$output_file" ]; then
            echo "Error: cert command requires <cn> and <output_file>"
            usage
        fi
        fetch_file "${KEYTAB_SERVICE_URL}/api/v1/cert/${arg}" "$output_file"
        ;;
    key)
        if [ -z "$arg" ] || [ -z "$output_file" ]; then
            echo "Error: key command requires <cn> and <output_file>"
            usage
        fi
        fetch_file "${KEYTAB_SERVICE_URL}/api/v1/key/${arg}" "$output_file"
        ;;
    health)
        if curl -s "${KEYTAB_SERVICE_URL}/health" | grep -q "healthy"; then
            echo "✓ Keytab service is healthy"
        else
            echo "✗ Keytab service is not healthy"
            exit 1
        fi
        ;;
    *)
        echo "Error: Unknown command '$command'"
        usage
        ;;
esac

# The end.
