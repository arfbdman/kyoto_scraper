#!/usr/bin/env bash
# Download and install Chrome
CHROME_VERSION="google-chrome-stable"
echo "Installing Chrome and ChromeDriver..."
apt-get update && apt-get install -y $CHROME_VERSION
apt-get install -y chromium-driver