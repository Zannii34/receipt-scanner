#!/bin/bash
set -e

echo "=== Building receipt-scanner ==="
echo "Python version: $(python --version)"

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Downloading Tesseract (static binary) ==="
TESSERACT_VERSION="5.4.1"
TESSERACT_DIR="$HOME/tesseract"
mkdir -p "$TESSERACT_DIR"
cd "$TESSERACT_DIR"

# Download AppImage (works on Linux, no root needed)
wget -q "https://github.com/AlexanderP/tesseract-appimage/releases/download/v${TESSERACT_VERSION}/tesseract-${TESSERACT_VERSION}-x86_64.AppImage" -O tesseract.AppImage
chmod +x tesseract.AppImage

# Extract without FUSE (AppImages need --appimage-extract in containers)
./tesseract.AppImage --appimage-extract > /dev/null 2>&1

echo "=== Tesseract extracted to $TESSERACT_DIR/squashfs-root/usr/bin/tesseract ==="
ls -la "$TESSERACT_DIR/squashfs-root/usr/bin/" || true

echo "=== Build complete ==="
