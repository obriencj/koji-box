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
    *)
        echo -e "${RED}Error:${NC} Unknown command '$command'"
        usage
        ;;
esac

# The end.
