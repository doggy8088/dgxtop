#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== DGXTOP Installation Helper ===${NC}"

# Check if OS is Linux
if [ "$(uname)" != "Linux" ]; then
    echo -e "${RED}Error: DGXTOP is only supported on Linux (Ubuntu).${NC}"
    exit 1
fi

# Get latest release version from GitHub API (with fallback)
VERSION="1.1.0"
if command -v curl >/dev/null 2>&1; then
    LATEST_TAG=$(curl -s https://api.github.com/repos/doggy8088/dgxtop/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    if [ -n "$LATEST_TAG" ] && [[ "$LATEST_TAG" =~ ^v[0-9] ]]; then
        VERSION=${LATEST_TAG#v}
    fi
fi

DEB_URL="https://github.com/doggy8088/dgxtop/releases/download/v${VERSION}/dgxtop_${VERSION}-1_all.deb"
TEMP_DEB="/tmp/dgxtop_latest_all.deb"

# Clean up any existing temp file
rm -f "$TEMP_DEB"

# Check for download tool
if command -v wget >/dev/null 2>&1; then
    echo -e "${BLUE}Downloading package via wget...${NC}"
    wget -q --show-progress -O "$TEMP_DEB" "$DEB_URL"
elif command -v curl >/dev/null 2>&1; then
    echo -e "${BLUE}Downloading package via curl...${NC}"
    curl -L --progress-bar -o "$TEMP_DEB" "$DEB_URL"
else
    echo -e "${RED}Error: Neither wget nor curl is installed. Please install one of them first.${NC}"
    exit 1
fi

# Install the package
echo -e "${BLUE}Installing package...${NC}"
sudo apt-get update
sudo apt-get install -y "$TEMP_DEB"

# Clean up
rm -f "$TEMP_DEB"

echo -e "${GREEN}✓ DGXTOP installed successfully!${NC}"
echo -e "Start monitoring by running: ${GREEN}dgxtop${NC}"
