# 🐧 Linux Guide — Setup, Execution, and Compilation

> 💡 **Fish Shell Tip (default on CachyOS):**
> To activate the virtual environment in Fish Shell, run:
> `source venv/bin/activate.fish`
> *(Or enter `bash` before starting to use standard Bash syntax)*

---

## ⚙️ 0. System Prerequisites

First and foremost, install FFmpeg through your distribution package manager (used to process and convert downloaded media).

**Arch Linux / CachyOS / Manjaro:**
```bash
sudo pacman -S ffmpeg
```

**Ubuntu / Linux Mint / Pop!_OS / Zorin OS:**
```bash
sudo apt install ffmpeg
```

**Fedora / AlmaLinux / Rocky Linux:**
```bash
sudo dnf install ffmpeg
```

**openSUSE:**
```bash
sudo zypper install ffmpeg
```

> 💡 Crimson utilizes **PySide6 (Qt6)** for a modern graphical interface with native anti-aliasing, which is installed automatically into the virtual environment via `pip`.

---

## ⚡ 1. Running Crimson via Terminal (Source Execution)

```bash
# 1. Create the virtual environment (only required on initial setup)
python -m venv venv

# 2. Activate the virtual environment
source venv/bin/activate        # Bash / Zsh
source venv/bin/activate.fish   # Fish Shell (CachyOS default)

# 3. Install dependencies
pip install -r Requirements/requirements_linux.txt

# 4. Run the application
python Crimson.py
```

---

## 📦 2. Compiling the Linux Executable

Crimson uses PyInstaller to bundle the application into a single standalone binary with full Qt6 interface and graphical asset support:

```bash
# With the virtual environment active, from the project root:
pyinstaller --noconsole --onefile \
  --collect-all PIL \
  --add-data "Icons:Icons" \
  Crimson.py
```

Or run the pre-configured script (recommended):

```bash
bash Compile_project/Linux.sh
```

### Testing the Compiled Binary

```bash
# Run the binary and keep terminal open to view output logs
./dist/Crimson
```

---

## 🎨 3. Creating Desktop Launcher with Icon (System Application Menu)

> 💡 **Why doesn't the compiled binary (`dist/Crimson`) display an icon?**
> On Windows, `.exe` executables embed `.ico` files internally within the binary PE header.
> On Linux, binaries (**ELF** format) **do not embed graphical icons**. No native Linux applications (neither browsers nor games) show an icon on the raw binary file in file managers (Dolphin/Nautilus).
> Official application icons on Linux are presented through a `.desktop` launcher shortcut in your desktop environment application menu or taskbar (dock).

To create the application launcher with the official icon in your desktop menu:

```bash
# 1. Grant execution permissions to the binary
chmod +x dist/Crimson

# 2. Create user applications folder (if it does not exist)
mkdir -p ~/.local/share/applications

# 3. Create desktop launcher pointing to the executable and icon
cat <<EOF > ~/.local/share/applications/Crimson.desktop
[Desktop Entry]
Type=Application
Name=Crimson
Comment=Video and Audio Downloader
Exec="$(pwd)/dist/Crimson"
Icon=$(pwd)/Icons/Crimson.png
Terminal=false
Categories=AudioVideo;Utility;Network;
StartupNotify=true
EOF

# 4. Grant execution permissions to the shortcut and refresh desktop database
chmod +x ~/.local/share/applications/Crimson.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null
```

All set! **Crimson** will now appear in your system menu (KDE/GNOME/XFCE) with its official icon and can be pinned to your dock or desktop.

---

## 🔍 4. How Crimson Adapts Automatically on Linux

The same `Crimson.py` codebase operates across both Windows and Linux. Environment detection occurs automatically via `platform.system()` upon startup.

| Feature | Windows | Linux |
|---|---|---|
| **Configuration Directory** | `%LOCALAPPDATA%\Crimson` | `~/.local/share/Crimson` |
| **FFmpeg** | Local project `ffmpeg/` directory or `PATH` | Discovered automatically in system `PATH` (`shutil.which`) |
| **Child Process Cleanup** | Scoped strictly by parent PID (`Win32_Process`) | Scoped strictly by parent PID (`pkill -P <PID> -x ffmpeg`) |
| **Graphical Interface** | `PySide6 (Qt6 - Fusion Style)` | `PySide6 (Qt6 - Fusion Style)` |
| **Launcher Icon** | `QMainWindow.setWindowIcon()` | `QMainWindow.setWindowIcon()` + `.desktop` |