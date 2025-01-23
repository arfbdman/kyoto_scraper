#!/usr/bin/env bash

# Install Google Chrome in the Render environment
curl -sSLO https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get update
apt-get install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb