#!/bin/bash
# Robust dependency installation script
# Ensures all core dependencies are installed with proper error handling

set -e  # Exit on error

echo "=== SAAAAAA Dependency Installation ==="
echo "Installing core runtime dependencies..."

# Configuration
MAX_RETRIES=5
TIMEOUT=300
PIP_OPTS="--timeout=${TIMEOUT} --retries=${MAX_RETRIES}"

# Install core dependencies
echo "📦 Installing from requirements-core.txt..."
pip install ${PIP_OPTS} -r requirements-core.txt

# Verify critical packages
echo ""
echo "✅ Verifying installations..."

python3 << 'EOF'
import sys

required_packages = [
    ('pyarrow', 'Arrow serialization'),
    ('pydantic', 'Data validation'),
    ('networkx', 'Graph operations'),
    ('blake3', 'Hashing'),
    ('structlog', 'Structured logging'),
    ('tenacity', 'Retry logic'),
]

failed = []
for package, purpose in required_packages:
    try:
        __import__(package)
        print(f'✓ {package:20s} - {purpose}')
    except ImportError as e:
        print(f'✗ {package:20s} - MISSING')
        failed.append(package)

if failed:
    print(f'\n❌ Missing packages: {", ".join(failed)}')
    print('Please install manually or check network connectivity')
    sys.exit(1)
else:
    print('\n✅ All core dependencies installed successfully!')
    sys.exit(0)
EOF

echo ""
echo "=== Installation Complete ==="
