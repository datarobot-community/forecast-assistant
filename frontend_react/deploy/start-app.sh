#!/usr/bin/env bash

# Define a custom Node.js install directory in /tmp
NODE_DIR="/tmp/node"
NODE_VERSION="18.16.0" 

# Check if Node.js is already installed
if [ ! -d "$NODE_DIR" ]; then
    echo "Node.js is not installed. Installing Node.js to $NODE_DIR..."
    
    # Create the directory in /tmp if it doesn't exist
    mkdir -p "$NODE_DIR"
    
    # Download and extract Node.js
    curl -o node.tar.xz "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.xz"
    tar -xf node.tar.xz --strip-components=1 -C "$NODE_DIR"
    rm node.tar.xz

    # Update PATH to include the custom Node.js directory
    export PATH="$NODE_DIR/bin:$PATH"
fi

# Verify Node.js installation
if ! command -v node &> /dev/null; then
    echo "Node.js installation failed."
    exit 1
else
    echo "Node.js successfully installed: $(node -v)"
fi

# Set npm cache directory to avoid permission issues
export NPM_CONFIG_CACHE="/tmp/.npm"

# Ensure the npm cache directory exists with appropriate permissions
mkdir -p "$NPM_CONFIG_CACHE"
chmod -R 777 "$NPM_CONFIG_CACHE"  # Adjust permissions to avoid permission issues

# Install the required Node.js packages
if [ -f "package.json" ]; then
    echo "Installing Node.js dependencies from package.json..."
    npm install --unsafe-perm
else
    echo "No package.json found. Skipping npm install."
fi

# Run the server
node server.js &

# Run fastapi server
uvicorn forecastic.rest_api:app --host 0.0.0.0 --port 8001
