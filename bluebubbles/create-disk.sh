#!/bin/bash

# Script to create the macOS virtual disk using Docker
# This eliminates the need to install qemu on the host

set -e

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found. Please copy .env.example to .env first."
    exit 1
fi

# Check if CONFIG_PATH is set
if [ -z "$CONFIG_PATH" ]; then
    echo "Error: CONFIG_PATH not set in .env file"
    exit 1
fi

# Default disk size (can be overridden by passing argument)
DISK_SIZE=${1:-128G}

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_PATH"

echo "Creating macOS virtual disk at: ${CONFIG_PATH}/maindisk.qcow2"
echo "Disk size: ${DISK_SIZE}"
echo ""

# Run qemu-img in a container
docker run --rm \
    -v "${CONFIG_PATH}:/data" \
    alpine:latest \
    sh -c "apk add --no-cache qemu-img && qemu-img create -f qcow2 /data/maindisk.qcow2 ${DISK_SIZE}"

echo ""
echo "✓ Disk created successfully at: ${CONFIG_PATH}/maindisk.qcow2"
echo ""
echo "Next steps:"
echo "1. Run: docker compose -f docker-compose.setup.yml up"
echo "2. Connect via VNC to complete macOS installation"
