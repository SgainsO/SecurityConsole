#!/bin/bash

echo "===================================="
echo "API Connection Diagnostic & Fix"
echo "===================================="
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "Server IP Address: $SERVER_IP"
echo "Frontend URL (local): http://localhost:3001"
echo "Frontend URL (remote): http://$SERVER_IP:3001"
echo "Backend URL (local): http://localhost:8000"
echo "Backend URL (remote): http://$SERVER_IP:8000"
echo ""

# Test backend connectivity
echo "Testing backend connectivity..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✓ Backend is running and accessible locally"
else
    echo "✗ Backend is NOT accessible"
    exit 1
fi

echo ""
echo "===================================="
echo "SOLUTION"
echo "===================================="
echo ""
echo "If accessing the app LOCALLY (on this machine):"
echo "  1. Open browser: http://localhost:3001"
echo "  2. No changes needed - should work!"
echo ""
echo "If accessing the app REMOTELY (from another machine):"
echo "  1. Open browser: http://$SERVER_IP:3001"
echo "  2. Update API URL by running:"
echo ""
echo "     export NEXT_PUBLIC_API_URL=http://$SERVER_IP:8000"
echo "     cd /root/SecurityConsole/Frontend/my-app"
echo "     # Restart the frontend (Ctrl+C and npm run dev again)"
echo ""
echo "Or manually edit Frontend/my-app/lib/api.ts line 1:"
echo "  Change: const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'"
echo "  To:     const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://$SERVER_IP:8000'"
echo ""

