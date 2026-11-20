#!/bin/bash

# If launched via double-click (without an attached terminal), reopen inside an available terminal emulator (Item M8)
if [ ! -t 1 ]; then
    if command -v konsole >/dev/null 2>&1; then
        exec konsole --hold -e bash "$0"
    elif command -v gnome-terminal >/dev/null 2>&1; then
        exec gnome-terminal -- bash -c "bash \"$0\"; read -p 'Press [Enter] to close...'"
    elif command -v xfce4-terminal >/dev/null 2>&1; then
        exec xfce4-terminal --hold -e "bash \"$0\""
    elif command -v x-terminal-emulator >/dev/null 2>&1; then
        exec x-terminal-emulator -e bash "$0"
    elif command -v xterm >/dev/null 2>&1; then
        exec xterm -hold -e bash "$0"
    fi
fi

# Navigate to the project root directory (one level above Compile_project)
cd "$(dirname "$0")/.."

echo "=================================================="
echo "       COMPILING PROJECT CRIMSON (LINUX)          "
echo "=================================================="
echo ""

# Remove previous build artifacts to prevent packaging conflicts
echo "[*] [1/4] Cleaning previous builds..."
rm -rf build dist Crimson.spec

# Bundle Python source, Pillow library, and icon assets into a single ELF binary
# --name Crimson: binary name | --paths .: lets PyInstaller find the 'crimson' package | crimson/__main__.py: entry point
echo "[*] [2/4] Packaging dependencies with PyInstaller..."
./venv/bin/pyinstaller --noconsole --onefile \
  --name Crimson \
  --paths . \
  --collect-all PIL \
  --add-data "crimson/Icons:Icons" \
  --add-data "LICENSE:." \
  --add-data "THIRD_PARTY_NOTICES.md:." \
  --add-data "licenses:licenses" \
  crimson/__main__.py

# Grant execution permission to the generated Linux binary in dist/
echo "[*] [3/4] Applying execution permissions..."
chmod +x dist/Crimson

# Release folder: the binary and every document that must travel with it
# (the GPL and the bundled libraries require their license texts to travel with the executable)
echo "[*] [4/4] Assembling the release archive..."
PACOTE="dist/Crimson-linux-x86_64"
rm -rf "$PACOTE"
mkdir -p "$PACOTE"
cp dist/Crimson "$PACOTE/Crimson"
cp LICENSE "$PACOTE/LICENSE"
cp THIRD_PARTY_NOTICES.md "$PACOTE/THIRD_PARTY_NOTICES.md"
cp -r licenses "$PACOTE/licenses"

# .tar.gz (and not .zip) keeps the executable permission of the binary, so it runs right after extracting
tar -czf dist/Crimson-linux-x86_64.tar.gz -C dist Crimson-linux-x86_64

echo ""
echo "=================================================="
echo "       [OK] COMPILATION COMPLETED SUCCESSFULLY!   "
echo "=================================================="
echo "Executable available at: dist/Crimson"
echo "Release package: dist/Crimson-linux-x86_64.tar.gz (upload this file to the GitHub release)"
echo ""
read -p "Press [Enter] to close this window..."