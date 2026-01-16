#!/bin/bash
set -e

# Docker entrypoint script

# Create necessary directories
mkdir -p .cpa/memory.db
mkdir -p reports
mkdir -p screenshots
mkdir -p test-results
mkdir -p logs

# Initialize memory database if needed
if [ ! -f .cpa/memory.db ]; then
    echo "Initializing memory database..."
fi

# Set permissions
chmod -R 755 .cpa reports screenshots test-results logs

# Execute the command passed as arguments
exec "$@"
