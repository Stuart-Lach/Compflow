#!/bin/bash
# Smoke test for compliance-engine API

set -e

echo "🔥 Starting smoke test..."

# Start server in background
echo "📡 Starting uvicorn server..."
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to be ready..."
sleep 5

# Test health endpoint
echo "🏥 Testing /health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
echo "Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    kill $SERVER_PID
    exit 1
fi

# Test root endpoint
echo "🏠 Testing root endpoint..."
ROOT_RESPONSE=$(curl -s http://localhost:8000/)
echo "Response: $ROOT_RESPONSE"

if echo "$ROOT_RESPONSE" | grep -q "compliance-engine"; then
    echo "✅ Root endpoint passed!"
else
    echo "❌ Root endpoint failed!"
    kill $SERVER_PID
    exit 1
fi

# Test API health (with prefix)
echo "🏥 Testing /api/v1/health endpoint..."
API_HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/v1/health)
echo "Response: $API_HEALTH_RESPONSE"

if echo "$API_HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ API health check passed!"
else
    echo "❌ API health check failed!"
    kill $SERVER_PID
    exit 1
fi

# Stop server
echo "🛑 Stopping server..."
kill $SERVER_PID

echo "✨ All smoke tests passed!"
