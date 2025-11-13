#!/bin/bash
# AtroZ Dashboard Startup Script
# ================================
# 
# Starts the AtroZ Dashboard API server with the static dashboard frontend.
#
# Usage:
#   bash scripts/start_dashboard.sh [OPTIONS]
#
# Options:
#   --port PORT       Port to run on (default: 5000)
#   --host HOST       Host to bind to (default: 0.0.0.0)
#   --debug           Enable debug mode
#   --no-auth         Disable authentication
#   --help            Show this help message

set -e

# Default values
PORT="${ATROZ_API_PORT:-5000}"
HOST="${ATROZ_API_HOST:-0.0.0.0}"
DEBUG="${ATROZ_DEBUG:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --debug)
            DEBUG="true"
            shift
            ;;
        --no-auth)
            export ATROZ_ENABLE_AUTH="false"
            shift
            ;;
        --help)
            echo "AtroZ Dashboard Startup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT       Port to run on (default: 5000)"
            echo "  --host HOST       Host to bind to (default: 0.0.0.0)"
            echo "  --debug           Enable debug mode"
            echo "  --no-auth         Disable authentication"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 AtroZ Dashboard Server                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Check if required packages are installed
echo ""
echo -e "${YELLOW}Checking dependencies...${NC}"

MISSING_DEPS=""
for pkg in flask flask_cors flask_socketio; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS $pkg"
    fi
done

# Check for jwt (pyjwt package)
if ! python3 -c "import jwt" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS pyjwt"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo -e "${YELLOW}⚠${NC}  Missing dependencies:$MISSING_DEPS"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install flask flask-cors flask-socketio pyjwt
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${GREEN}✓${NC} All dependencies are installed"
fi

# Check if static files exist
STATIC_DIR="$PROJECT_ROOT/src/saaaaaa/api/static"
if [ ! -f "$STATIC_DIR/index.html" ]; then
    echo -e "${RED}Error: Static files not found at $STATIC_DIR${NC}"
    echo -e "${YELLOW}Please ensure the dashboard files are in place${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Static files found"

# Set environment variables
export ATROZ_API_PORT="$PORT"
export ATROZ_API_HOST="$HOST"
export ATROZ_DEBUG="$DEBUG"

# Display configuration
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Host:  ${GREEN}$HOST${NC}"
echo -e "  Port:  ${GREEN}$PORT${NC}"
echo -e "  Debug: ${GREEN}$DEBUG${NC}"
echo -e "  Auth:  ${GREEN}${ATROZ_ENABLE_AUTH:-true}${NC}"
echo ""
echo -e "${BLUE}Dashboard URL:${NC}"
echo -e "  ${GREEN}http://localhost:$PORT/${NC}"
echo ""
echo -e "${BLUE}API Endpoints:${NC}"
echo -e "  ${GREEN}http://localhost:$PORT/api/v1/health${NC}"
echo -e "  ${GREEN}http://localhost:$PORT/api/v1/pdet/regions${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Start the server
python3 -m saaaaaa.api.api_server
