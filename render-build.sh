#!/usr/bin/env bash

# Log environment variables (useful for troubleshooting)
echo "Environment Variables:"
env

# Install Google Chrome in the Render environment
echo "Installing Google Chrome..."
curl -sSLO https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get update && apt-get install -y ./google-chrome-stable_current_amd64.deb
rm ./google-chrome-stable_current_amd64.deb

# Verify Chrome installation
if [ -f "/usr/bin/google-chrome" ]; then
    echo "Google Chrome successfully installed at /usr/bin/google-chrome"
else
    echo "Error: Google Chrome installation failed."
    exit 1
fi

# Log Chrome version
/usr/bin/google-chrome --version