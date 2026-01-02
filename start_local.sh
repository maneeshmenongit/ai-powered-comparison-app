#!/bin/bash
# Start local backend with clean environment

# Kill any existing backend
pkill -9 -f "python.*app.py" 2>/dev/null

# Unset any environment variables that might interfere
unset GOOGLE_PLACES_API_KEY
unset OPENAI_API_KEY
unset CLAUDE_API_KEY

# Load .env file
export $(grep -v '^#' .env | xargs)

echo "Starting backend on http://localhost:5001..."
echo "Google API Key (last 4): ${GOOGLE_PLACES_API_KEY: -4}"

# Start backend
./venv/bin/python api/app.py
