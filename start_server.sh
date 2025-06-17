#!/bin/bash

# Every Intelligence Server Startup Script
# Usage: ./start_server.sh

echo "🚀 Starting Every Intelligence Server..."

# Navigate to the correct directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "every_env" ]; then
    echo "📦 Activating virtual environment..."
    source every_env/bin/activate
else
    echo "❌ Virtual environment not found! Run 'python -m venv every_env' first."
    exit 1
fi

# Start the server
echo "🌐 Starting server on http://localhost:3000"
python src/web/server.py 