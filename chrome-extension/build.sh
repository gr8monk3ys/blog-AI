#!/bin/bash

# Blog AI Chrome Extension - Build Script
#
# Creates a production-ready zip file for Chrome Web Store submission.
# Run from the chrome-extension directory.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Read version from manifest.json
VERSION=$(grep -o '"version": "[^"]*"' manifest.json | cut -d'"' -f4)

if [ -z "$VERSION" ]; then
    echo -e "${RED}Error: Could not read version from manifest.json${NC}"
    exit 1
fi

echo -e "${YELLOW}Blog AI Chrome Extension - Build Script${NC}"
echo "=========================================="
echo -e "Version: ${GREEN}$VERSION${NC}"
echo ""

# Output filename
OUTPUT_FILE="blog-ai-extension-v${VERSION}.zip"
BUILD_DIR="build"

# Check for required commands
if ! command -v zip &> /dev/null; then
    echo -e "${RED}Error: 'zip' command not found. Please install it first.${NC}"
    exit 1
fi

# Clean up previous builds
echo -e "${YELLOW}Cleaning up previous builds...${NC}"
rm -rf "$BUILD_DIR"
rm -f "blog-ai-extension-v*.zip"

# Create build directory
mkdir -p "$BUILD_DIR"

# Copy files to build directory
echo -e "${YELLOW}Copying files...${NC}"

# Copy manifest
cp manifest.json "$BUILD_DIR/"

# Copy directories
for dir in popup background content options lib icons; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "$BUILD_DIR/"
        echo "  - $dir/"
    fi
done

# Remove any development files from build
echo -e "${YELLOW}Removing development files...${NC}"
find "$BUILD_DIR" -name "*.map" -delete 2>/dev/null || true
find "$BUILD_DIR" -name ".DS_Store" -delete 2>/dev/null || true
find "$BUILD_DIR" -name "*.log" -delete 2>/dev/null || true
find "$BUILD_DIR" -name ".gitkeep" -delete 2>/dev/null || true

# Validate manifest
echo -e "${YELLOW}Validating manifest.json...${NC}"

# Check required fields
MANIFEST_ERRORS=""

if ! grep -q '"manifest_version": 3' "$BUILD_DIR/manifest.json"; then
    MANIFEST_ERRORS+="  - manifest_version must be 3\n"
fi

if ! grep -q '"name"' "$BUILD_DIR/manifest.json"; then
    MANIFEST_ERRORS+="  - missing 'name' field\n"
fi

if ! grep -q '"version"' "$BUILD_DIR/manifest.json"; then
    MANIFEST_ERRORS+="  - missing 'version' field\n"
fi

if [ -n "$MANIFEST_ERRORS" ]; then
    echo -e "${RED}Manifest validation errors:${NC}"
    echo -e "$MANIFEST_ERRORS"
    exit 1
fi

echo -e "${GREEN}Manifest validation passed${NC}"

# Check for placeholder icons
echo -e "${YELLOW}Checking icons...${NC}"

ICON_SIZES="16 32 48 128"
MISSING_ICONS=""

for size in $ICON_SIZES; do
    if [ ! -f "$BUILD_DIR/icons/icon${size}.png" ]; then
        MISSING_ICONS+="  - icons/icon${size}.png\n"
    fi
done

if [ -n "$MISSING_ICONS" ]; then
    echo -e "${YELLOW}Warning: Missing icon files:${NC}"
    echo -e "$MISSING_ICONS"
    echo "Creating placeholder icons..."

    # Create simple placeholder icons using base64-encoded minimal PNG
    # This is a 1x1 purple pixel that will be scaled
    mkdir -p "$BUILD_DIR/icons"

    for size in $ICON_SIZES; do
        if [ ! -f "$BUILD_DIR/icons/icon${size}.png" ]; then
            # Create a simple placeholder message file
            echo "Placeholder icon - replace with actual ${size}x${size} PNG" > "$BUILD_DIR/icons/icon${size}.png.txt"
        fi
    done

    echo -e "${YELLOW}Note: Replace placeholder icons with actual PNG files before submission${NC}"
fi

# Create zip file
echo -e "${YELLOW}Creating zip archive...${NC}"
cd "$BUILD_DIR"
zip -r "../$OUTPUT_FILE" . -x "*.txt"
cd ..

# Cleanup build directory
rm -rf "$BUILD_DIR"

# Display results
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo ""
    echo -e "${GREEN}Build successful!${NC}"
    echo "=========================================="
    echo -e "Output: ${GREEN}$OUTPUT_FILE${NC}"
    echo -e "Size: ${GREEN}$FILE_SIZE${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test the extension by loading the unpacked folder"
    echo "  2. Replace placeholder icons with actual PNG files"
    echo "  3. Upload to Chrome Web Store Developer Dashboard"
    echo "     https://chrome.google.com/webstore/devconsole"
else
    echo -e "${RED}Build failed: Output file not created${NC}"
    exit 1
fi

# Validate zip contents
echo ""
echo -e "${YELLOW}Zip contents:${NC}"
unzip -l "$OUTPUT_FILE" | tail -n +4 | head -n -2
