#!/usr/bin/env bash
# Install Google Chrome for Selenium
curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb
apt-get update
apt-get -y install ./chrome.deb
rm chrome.deb