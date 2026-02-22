#!/bin/bash
# Apple Developer Toolkit - Setup Script
# Installs appstore and swiftship CLIs via Homebrew.
#
# What this script does:
#   1. Checks that Homebrew is installed
#   2. Shows what will be installed and from where
#   3. Asks for user confirmation before proceeding
#   4. Adds the Abdullah4AI/tap Homebrew tap (public GitHub repo)
#   5. Installs 'appstore' and 'swiftship' CLI binaries
#
# What this script does NOT do:
#   - Does not configure API keys or credentials
#   - Does not install Xcode or Xcode Command Line Tools
#   - Does not modify system files or require sudo
#
# Source code (all open source, MIT licensed):
#   - appstore: https://github.com/Abdullah4AI/appstore
#   - swiftship: https://github.com/Abdullah4AI/swiftship
#   - Homebrew tap: https://github.com/Abdullah4AI/homebrew-tap
#
# You can also install manually without this script:
#   brew tap Abdullah4AI/tap
#   brew install Abdullah4AI/tap/appstore
#   brew install Abdullah4AI/tap/swiftship

set -e

# Check if Homebrew is available
if ! command -v brew &>/dev/null; then
  echo "Homebrew required. Install: https://brew.sh"
  exit 1
fi

# Show what will be installed
echo "Apple Developer Toolkit Setup"
echo "=============================="
echo ""
echo "This script will install two CLI tools via Homebrew from a third-party tap:"
echo ""
echo "  Tap:        Abdullah4AI/tap"
echo "  Source:      https://github.com/Abdullah4AI/homebrew-tap"
echo ""
echo "  1. appstore   - App Store Connect CLI"
echo "     Source:     https://github.com/Abdullah4AI/appstore"
echo ""
echo "  2. swiftship  - iOS App Builder"
echo "     Source:     https://github.com/Abdullah4AI/swiftship"
echo ""

# Check what's already installed
NEED_TAP=true
NEED_APPSTORE=true
NEED_SWIFTSHIP=true

if brew tap 2>/dev/null | grep -q "abdullah4ai/tap"; then
  NEED_TAP=false
fi

if command -v appstore &>/dev/null; then
  NEED_APPSTORE=false
  echo "  appstore already installed: $(which appstore)"
fi

if command -v swiftship &>/dev/null; then
  NEED_SWIFTSHIP=false
  echo "  swiftship already installed: $(which swiftship)"
fi

if [ "$NEED_APPSTORE" = false ] && [ "$NEED_SWIFTSHIP" = false ]; then
  echo ""
  echo "Both tools are already installed. Nothing to do."
  exit 0
fi

# Ask for confirmation (skip if --yes flag is passed)
if [ "$1" != "--yes" ] && [ "$1" != "-y" ]; then
  echo ""
  read -p "Proceed with installation? [y/N] " confirm
  case "$confirm" in
    [yY]|[yY][eE][sS]) ;;
    *)
      echo "Installation cancelled."
      exit 0
      ;;
  esac
fi

# Add tap if not already added
if [ "$NEED_TAP" = true ]; then
  echo ""
  echo "Adding tap (source: https://github.com/Abdullah4AI/homebrew-tap)..."
  brew tap Abdullah4AI/tap
fi

# Install appstore CLI
if [ "$NEED_APPSTORE" = true ]; then
  echo "Installing appstore CLI..."
  brew install Abdullah4AI/tap/appstore
else
  echo "appstore CLI already installed."
fi

# Install swiftship CLI
if [ "$NEED_SWIFTSHIP" = true ]; then
  echo "Installing swiftship CLI..."
  brew install Abdullah4AI/tap/swiftship
else
  echo "swiftship CLI already installed."
fi

echo ""
echo "Setup complete."
echo "  appstore --help    App Store Connect CLI"
echo "  swiftship --help   iOS App Builder"
echo ""
echo "Next steps:"
echo "  - For App Store Connect: run 'appstore auth login' with your API key"
echo "  - For iOS App Builder: run 'swiftship setup' to check prerequisites"
