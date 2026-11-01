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
echo "[*] [1/3] Cleaning previous builds..."
rm -rf build dist Crimson.spec

# Bundle Python source, Pillow library, and icon assets into a single ELF binary
echo "[*] [2/3] Packaging dependencies with PyInstaller..."
./venv/bin/pyinstaller --noconsole --onefile \
  --collect-all PIL \
  --add-data "Icons:Icons" \
  Crimson.py

# Grant execution permission to the generated Linux binary in dist/
echo "[*] [3/3] Applying execution permissions..."
chmod +x dist/Crimson

echo ""
echo "=================================================="
echo "       [OK] COMPILATION COMPLETED SUCCESSFULLY!   "
echo "=================================================="
echo "Executable available at: dist/Crimson"
echo ""
read -p "Press [Enter] to close this window..."