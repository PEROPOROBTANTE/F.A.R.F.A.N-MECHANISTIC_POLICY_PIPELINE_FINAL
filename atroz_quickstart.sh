#!/bin/bash
# AtroZ Dashboard Quick Start Script
# ===================================
# 
# This script sets up and runs the AtroZ Dashboard integration
# 
# Usage:
#   ./atroz_quickstart.sh [dev|prod]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MODE="${1:-dev}"
PORT="${ATROZ_API_PORT:-5000}"
STATIC_PORT="${ATROZ_STATIC_PORT:-8000}"

echo "==============================================="
echo "  AtroZ Dashboard Quick Start"
echo "  Mode: $MODE"
echo "==============================================="
echo ""

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    print_error "Python $REQUIRED_VERSION or higher required. Found: $PYTHON_VERSION"
    exit 1
fi
print_info "✓ Python $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_info "✓ Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_info "✓ Virtual environment activated"

# Install dependencies
print_info "Installing dependencies..."
if [ -f "requirements_atroz.txt" ]; then
    pip install -q -r requirements_atroz.txt
    print_info "✓ AtroZ dependencies installed"
elif [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    print_info "✓ requirements.txt dependencies installed"
else
    print_warn "requirements_atroz.txt and requirements.txt not found, skipping"
fi

# Create necessary directories
print_info "Creating directories..."
mkdir -p static/js static/css output cache logs
print_info "✓ Directories created"

# Copy HTML if needed
if [ ! -f "static/index.html" ] && [ -f "deepseek_html_20251022_29a8c3.html" ]; then
    print_info "Copying dashboard HTML..."
    cp deepseek_html_20251022_29a8c3.html static/index.html
    
    # Inject integration scripts
    print_info "Injecting integration scripts..."
    
    # Create backup
    cp static/index.html static/index.html.bak
    
    # Insert scripts before </body>
    cat >> static/index.html << 'EOF'

<!-- Socket.IO for WebSocket support -->
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>

<!-- AtroZ Data Service -->
<script src="/static/js/atroz-data-service.js"></script>

<!-- AtroZ Dashboard Integration -->
<script src="/static/js/atroz-dashboard-integration.js"></script>

<!-- Configuration -->
<script>
    window.ATROZ_API_URL = 'http://localhost:5000';
    window.ATROZ_ENABLE_REALTIME = 'true';
    window.ATROZ_ENABLE_AUTH = 'false';
    window.ATROZ_CLIENT_ID = 'atroz-dashboard-v1';
</script>
EOF
    
    print_info "✓ Dashboard HTML configured"
fi

# Create .env if doesn't exist
if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    
    # Generate secure random secrets
    API_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    cat > .env << EOF
# AtroZ Dashboard Configuration
ATROZ_API_PORT=$PORT
ATROZ_API_SECRET=$API_SECRET
ATROZ_JWT_SECRET=$JWT_SECRET
ATROZ_DEBUG=true
ATROZ_CORS_ORIGINS=http://localhost:$STATIC_PORT,http://127.0.0.1:$STATIC_PORT
ATROZ_RATE_LIMIT=false
ATROZ_CACHE_ENABLED=true
ATROZ_CACHE_TTL=300
ATROZ_DATA_DIR=output
ATROZ_CACHE_DIR=cache
ATROZ_ENABLE_REALTIME=true
EOF
    print_info "✓ .env file created with secure random secrets"
fi

# Load environment variables
if [ -f ".env" ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Check if required files exist
print_info "Checking required files..."
REQUIRED_FILES=(
    "src/saaaaaa/api/api_server.py"
    "src/saaaaaa/core/orchestrator/core.py"
    "src/saaaaaa/api/static/js/atroz-data-service.js"
    "src/saaaaaa/api/static/js/atroz-dashboard-integration.js"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file not found: $file"
        exit 1
    fi
done
print_info "✓ All required files present"

# Test imports
print_info "Testing Python imports..."
python3 -c "
import sys
sys.path.append('src')
try:
    from saaaaaa.api.api_server import app
    from saaaaaa.core.orchestrator.core import Orchestrator
    print('✓ All modules imported successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
" || exit 1

# Start services based on mode
if [ "$MODE" == "dev" ]; then
    print_info "Starting development servers..."
    
    # Create logs directory
    mkdir -p logs
    
    # Start API server in background
    print_info "Starting API server on port $PORT..."
    export FLASK_APP=src/saaaaaa/api/api_server.py
    flask run --port=$PORT > logs/api_server.log 2>&1 &
    API_PID=$!
    echo $API_PID > logs/api_server.pid
    
    # Wait for API server to start
    print_info "Waiting for API server to start..."
    sleep 15
    
    # Check if API server is running
    if ps -p $API_PID > /dev/null && curl -s http://127.0.0.1:$PORT/api/v1/health > /dev/null; then
        print_info "✓ API server started (PID: $API_PID)"
    else
        print_error "API server failed to start. Check logs/api_server.log"
        exit 1
    fi
    
    # Start static file server
    print_info "Starting static file server on port $STATIC_PORT..."
    python3 -m http.server $STATIC_PORT --directory static > logs/static_server.log 2>&1 &
    STATIC_PID=$!
    echo $STATIC_PID > logs/static_server.pid
    
    # Wait for static server to start
    sleep 2
    
    if ps -p $STATIC_PID > /dev/null; then
        print_info "✓ Static file server started (PID: $STATIC_PID)"
    else
        print_error "Static file server failed to start. Check logs/static_server.log"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
    
    echo ""
    echo "==============================================="
    echo -e "${GREEN}  AtroZ Dashboard is RUNNING!${NC}"
    echo "==============================================="
    echo ""
    echo "  Dashboard:    http://localhost:$STATIC_PORT"
    echo "  API:          http://localhost:$PORT/api/v1/health"
    echo "  API Docs:     http://localhost:$PORT/api/v1/"
    echo ""
    echo "  Logs:"
    echo "    API Server:   tail -f logs/api_server.log"
    echo "    Static:       tail -f logs/static_server.log"
    echo ""
    echo "  To stop:"
    echo "    kill \$(cat logs/api_server.pid) \$(cat logs/static_server.pid)"
    echo ""
    echo "==============================================="
    
    # Create stop script
    cat > stop_atroz.sh << 'STOPEOF'
#!/bin/bash
echo "Stopping AtroZ Dashboard..."
if [ -f "logs/api_server.pid" ]; then
    kill $(cat logs/api_server.pid) 2>/dev/null && echo "✓ API server stopped"
    rm logs/api_server.pid
fi
if [ -f "logs/static_server.pid" ]; then
    kill $(cat logs/static_server.pid) 2>/dev/null && echo "✓ Static server stopped"
    rm logs/static_server.pid
fi
echo "AtroZ Dashboard stopped"
STOPEOF
    chmod +x stop_atroz.sh
    
    print_info "Created stop_atroz.sh for easy shutdown"
    
    # Open browser (optional)
    if command -v open &> /dev/null; then
        print_info "Opening browser..."
        sleep 2
        open "http://localhost:$STATIC_PORT"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:$STATIC_PORT"
    fi
    
elif [ "$MODE" == "prod" ]; then
    print_info "Starting production server..."
    
    # Check if gunicorn is installed
    if ! command -v gunicorn &> /dev/null; then
        print_error "gunicorn not installed. Install with: pip install gunicorn gevent-websocket"
        exit 1
    fi
    
    # Start with gunicorn
    print_info "Starting gunicorn on port $PORT..."
    gunicorn --worker-class gevent \
             --workers 4 \
             --bind 0.0.0.0:$PORT \
             --access-logfile logs/access.log \
             --error-logfile logs/error.log \
             --log-level info \
             api_server:app
    
else
    print_error "Invalid mode: $MODE. Use 'dev' or 'prod'"
    exit 1
fi
