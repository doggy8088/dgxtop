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

# Prefer latest release from GitHub API and pick matching deb asset URL
DEFAULT_VERSION="1.2.0"
VERSION="$DEFAULT_VERSION"
DEB_URL=""

if command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1; then
    if command -v curl >/dev/null 2>&1; then
        RELEASE_JSON=$(curl -fsSL https://api.github.com/repos/doggy8088/dgxtop/releases/latest)
    else
        RELEASE_JSON=$(wget -qO- https://api.github.com/repos/doggy8088/dgxtop/releases/latest)
    fi
fi

if [ -n "$RELEASE_JSON" ]; then
    LATEST_TAG=$(printf '%s\n' "$RELEASE_JSON" | grep -m1 '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
    ASSET_URL=$(printf '%s\n' "$RELEASE_JSON" | grep '"browser_download_url"' | grep 'dgxtop_.*_all\.deb' | sed -E 's/.*"([^"]+)".*/\1/' | head -n 1)

    if [ -n "$LATEST_TAG" ] && [[ "$LATEST_TAG" =~ ^v?[0-9] ]]; then
        VERSION="${LATEST_TAG#v}"
        echo -e "${BLUE}Latest release tag: ${VERSION}${NC}"
    else
        echo -e "${BLUE}Unable to parse latest release tag; using fallback version ${DEFAULT_VERSION}${NC}"
    fi
fi

if [ -z "$ASSET_URL" ]; then
    DEB_URL="https://github.com/doggy8088/dgxtop/releases/download/v${VERSION}/dgxtop_${VERSION}-1_all.deb"
else
    DEB_URL="$ASSET_URL"
    echo -e "${BLUE}Using release asset URL: ${DEB_URL}${NC}"
fi

if [ -z "$DEB_URL" ]; then
    echo -e "${RED}Error: unable to determine download URL for DGXTOP.${NC}"
    exit 1
fi

echo -e "${BLUE}Installing version: ${VERSION}${NC}"
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
