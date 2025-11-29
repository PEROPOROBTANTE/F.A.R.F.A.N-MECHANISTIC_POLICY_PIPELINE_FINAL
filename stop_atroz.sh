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
