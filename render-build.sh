#!/usr/bin/env bash

# Log environment variables (useful for debugging)
echo "Environment Variables:"
env

# Install Chromium as the browser
echo "Installing Chromium..."
apt-get update && apt-get install -y chromium-browser

# Verify Chromium installation
if [ -f "/usr/bin/chromium-browser" ]; then
    echo "Chromium successfully installed at /usr/bin/chromium-browser"
else
    echo "Error: Chromium installation failed."
    exit 1
fi

# Log Chromium version
/usr/bin/chromium-browser --version