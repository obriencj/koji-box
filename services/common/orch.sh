#!/bin/bash
# Orch Service V2 API Client
# Simple client for the orch service v2 APIs using curl -sS

set -euo pipefail

# Default configuration
ORCH_SERVICE_URL="${ORCH_SERVICE_URL:-http://orch.koji.box:5000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show usage
usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  checkout <uuid> [file]     Checkout a resource by UUID"
    echo "  release <uuid>             Release a resource by UUID"
    echo "  status <uuid>              Get resource status"
    echo "  validate <uuid>            Validate resource access"
    echo "  health                     Check service health"
    echo "  mappings                   List all resource mappings"
    echo "  docs                       Show API documentation"
    echo "  ca-cert [file]             Get CA certificate (public key only)"
    echo "  ca-info                    Get CA certificate information"
    echo "  ca-status                  Get CA status"
    echo "  ca-install                 Install CA certificate to system trust store"
    echo ""
    echo "Environment Variables:"
    echo "  ORCH_SERVICE_URL           Orch service URL (default: http://orch.koji.box:5000)"
    echo ""
    echo "Examples:"
    echo "  $0 checkout a1b2c3d4-e5f6-7890-abcd-ef1234567890 /tmp/keytab"
    echo "  $0 status a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    echo "  $0 release a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    echo "  $0 health"
    echo "  $0 mappings"
    echo "  $0 ca-cert /tmp/ca.crt"
    echo "  $0 ca-info"
    echo "  $0 ca-status"
    echo "  $0 ca-install"
    exit 1
}

# Function to make HTTP requests
make_request() {
    local method="$1"
    local url="$2"
    local output_file="$3"
    local show_headers="${4:-false}"

    local curl_opts=(-sS -X "$method")

    if [ "$show_headers" = "true" ]; then
        curl_opts+=(-i)
    fi

    if [ -n "$output_file" ]; then
        # Create output directory if needed
        mkdir -p "$(dirname "$output_file")"
        curl_opts+=(-o "$output_file")
    fi

    if curl "${curl_opts[@]}" "$url"; then
        if [ -n "$output_file" ]; then
            echo -e "${GREEN}✓${NC} Resource saved to $output_file"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} Request failed: $method $url"
        return 1
    fi
}

# Function to validate UUID format
validate_uuid() {
    local uuid="$1"
    if [[ ! "$uuid" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
        echo -e "${RED}Error:${NC} Invalid UUID format: $uuid"
        echo "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        exit 1
    fi
}

# Function to detect CA anchors directory and update command
detect_ca_system() {
    local anchors_dir=""
    local update_cmd=""

    # Check for different CA trust store systems
    if [ -d "/usr/local/share/ca-certificates" ]; then
        # Debian/Ubuntu system
        anchors_dir="/usr/local/share/ca-certificates"
        update_cmd="update-ca-certificates"
        echo "Detected Debian/Ubuntu CA system"
    elif [ -d "/etc/pki/ca-trust/source/anchors" ]; then
        # RHEL/CentOS/Fedora system
        anchors_dir="/etc/pki/ca-trust/source/anchors"
        update_cmd="update-ca-trust extract"
        echo "Detected RHEL/CentOS/Fedora CA system"
    elif [ -d "/usr/share/pki/trust/anchors" ]; then
        # OpenSUSE system
        anchors_dir="/usr/share/pki/trust/anchors"
        update_cmd="update-ca-trust extract"
        echo "Detected OpenSUSE CA system"
    elif [ -d "/etc/ssl/certs" ] && command -v update-ca-certificates >/dev/null 2>&1; then
        # Alternative Debian/Ubuntu system
        anchors_dir="/usr/local/share/ca-certificates"
        update_cmd="update-ca-certificates"
        echo "Detected Debian/Ubuntu CA system (alternative)"
    else
        echo -e "${RED}Error:${NC} Could not detect CA trust store system"
        echo "Supported systems:"
        echo "  - Debian/Ubuntu: /usr/local/share/ca-certificates"
        echo "  - RHEL/CentOS/Fedora: /etc/pki/ca-trust/source/anchors"
        echo "  - OpenSUSE: /usr/share/pki/trust/anchors"
        return 1
    fi

    echo "Anchors directory: $anchors_dir"
    echo "Update command: $update_cmd"

    # Export variables for use by caller
    export CA_ANCHORS_DIR="$anchors_dir"
    export CA_UPDATE_CMD="$update_cmd"
    return 0
}

function cmd_ca_install() {
    # Detect CA system
    if ! detect_ca_system; then
        exit 1
    fi

    # Check if we have the necessary permissions
    if [ ! -w "$CA_ANCHORS_DIR" ]; then
        echo -e "${RED}Error:${NC} No write permission to $CA_ANCHORS_DIR"
        echo "This command requires root privileges. Please run with sudo:"
        echo "  sudo $0 ca-install"
        exit 1
    fi

    # Create temporary file for CA certificate
    local temp_ca_file=$(mktemp)
    local ca_file="$CA_ANCHORS_DIR/orch-ca.crt"

    if [ -f "$ca_file" ]; then
        echo -e "${BLUE}CA certificate already exists in $ca_file${NC}"
        return 0
    fi

    echo -e "${BLUE}Retrieving CA certificate...${NC}"

    # Get CA certificate
    if ! make_request "GET" "${ORCH_SERVICE_URL}/api/v2/ca/certificate" "$temp_ca_file"; then
        echo -e "${RED}✗${NC} Failed to retrieve CA certificate"
        rm -f "$temp_ca_file"
        exit 1
    fi

    # Verify the certificate file is valid
    if [ ! -s "$temp_ca_file" ]; then
        echo -e "${RED}✗${NC} Retrieved CA certificate is empty"
        rm -f "$temp_ca_file"
        exit 1
    fi

    # Check if it's a valid certificate
    if ! openssl x509 -in "$temp_ca_file" -text -noout >/dev/null 2>&1; then
        echo -e "${RED}✗${NC} Retrieved file is not a valid certificate"
        rm -f "$temp_ca_file"
        exit 1
    fi

    # Copy certificate to anchors directory
    echo -e "${BLUE}Installing CA certificate to $ca_file...${NC}"
    if cp "$temp_ca_file" "$ca_file"; then
        echo -e "${GREEN}✓${NC} CA certificate installed to $ca_file"
    else
        echo -e "${RED}✗${NC} Failed to install CA certificate"
        rm -f "$temp_ca_file"
        exit 1
    fi

    # Set appropriate permissions
    chmod 644 "$ca_file"

    # Update CA trust store
    echo -e "${BLUE}Updating CA trust store...${NC}"
    if $CA_UPDATE_CMD; then
        echo -e "${GREEN}✓${NC} CA trust store updated successfully"
    else
        echo -e "${YELLOW}⚠${NC} CA certificate installed but trust store update failed"
        echo "You may need to run: $CA_UPDATE_CMD"
    fi

    # Clean up temporary file
    rm -f "$temp_ca_file"

    echo -e "${GREEN}✓${NC} CA certificate installation completed"
    echo "The orch CA certificate is now trusted by the system"
}


function main() {
    # Check arguments
    if [ $# -lt 1 ]; then
        usage
    fi

    command="$1"
    uuid="${2:-}"
    output_file="${3:-}"

    # Handle commands
    case "$command" in
        checkout)
            if [ -z "$uuid" ]; then
                echo -e "${RED}Error:${NC} checkout command requires <uuid>"
                usage
            fi
            validate_uuid "$uuid"
            echo -e "${BLUE}Checking out resource:${NC} $uuid"
            if make_request "POST" "${ORCH_SERVICE_URL}/api/v2/resource/${uuid}" "$output_file"; then
                echo -e "${GREEN}✓${NC} Resource checked out successfully"
            else
                echo -e "${RED}✗${NC} Failed to checkout resource"
                exit 1
            fi
            ;;
        release)
            if [ -z "$uuid" ]; then
                echo -e "${RED}Error:${NC} release command requires <uuid>"
                usage
            fi
            validate_uuid "$uuid"
            echo -e "${BLUE}Releasing resource:${NC} $uuid"
            if make_request "DELETE" "${ORCH_SERVICE_URL}/api/v2/resource/${uuid}" ""; then
                echo -e "${GREEN}✓${NC} Resource released successfully"
            else
                echo -e "${RED}✗${NC} Failed to release resource"
                exit 1
            fi
            ;;
        status)
            if [ -z "$uuid" ]; then
                echo -e "${RED}Error:${NC} status command requires <uuid>"
                usage
            fi
            validate_uuid "$uuid"
            echo -e "${BLUE}Getting status for resource:${NC} $uuid"
            make_request "GET" "${ORCH_SERVICE_URL}/api/v2/resource/${uuid}/status" "" true
            ;;
        validate)
            if [ -z "$uuid" ]; then
                echo -e "${RED}Error:${NC} validate command requires <uuid>"
                usage
            fi
            validate_uuid "$uuid"
            echo -e "${BLUE}Validating access to resource:${NC} $uuid"
            make_request "GET" "${ORCH_SERVICE_URL}/api/v2/resource/${uuid}/validate" "" true
            ;;
        health)
            echo -e "${BLUE}Checking service health...${NC}"
            if make_request "GET" "${ORCH_SERVICE_URL}/api/v2/status/health" "" true; then
                echo -e "${GREEN}✓${NC} Orch service is healthy"
            else
                echo -e "${RED}✗${NC} Orch service is not healthy"
                exit 1
            fi
            ;;
        mappings)
            echo -e "${BLUE}Getting resource mappings...${NC}"
            make_request "GET" "${ORCH_SERVICE_URL}/api/v2/status/mappings" "" true
            ;;
        docs)
            echo -e "${BLUE}Opening API documentation...${NC}"
            make_request "GET" "${ORCH_SERVICE_URL}/api/v2/docs/" "" true
            ;;
        ca-cert)
            echo -e "${BLUE}Getting CA certificate...${NC}"
            if make_request "GET" "${ORCH_SERVICE_URL}/api/v2/ca/certificate" "$output_file"; then
                echo -e "${GREEN}✓${NC} CA certificate retrieved successfully"
            else
                echo -e "${RED}✗${NC} Failed to retrieve CA certificate"
                exit 1
            fi
            ;;
        ca-info)
            echo -e "${BLUE}Getting CA certificate information...${NC}"
            make_request "GET" "${ORCH_SERVICE_URL}/api/v2/ca/info" "" true
            ;;
        ca-status)
            echo -e "${BLUE}Getting CA status...${NC}"
            make_request "GET" "${ORCH_SERVICE_URL}/api/v2/ca/status" "" true
            ;;
        ca-install)
            echo -e "${BLUE}Installing CA certificate to system trust store...${NC}"
            cmd_ca_install
            ;;
        *)
            echo -e "${RED}Error:${NC} Unknown command '$command'"
            usage
            ;;
    esac
}

main "$@"

# The end.
