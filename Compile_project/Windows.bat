@echo off
REM Navigate to the project root directory (one level above Compile_project)
cd /d "%~dp0\.."

REM Activate the Python virtual environment on Windows
echo [*] Preparing build environment...
call venv\Scripts\activate.bat

REM Install or verify all required dependencies for Windows packaging
echo [*] Checking required dependencies for compilation...
pip install -r Requirements\requirements_windows.txt

REM Standardize main icon dimensions (256x256) and convert from PNG to Windows ICO format
echo [*] Standardizing dimensions and converting PNG icon to ICO...
python -c "from PIL import Image; import glob; f = glob.glob('Icons/*Crimson*.png'); img = Image.open(f[0]).resize((256, 256)); img.save('Icons/icone.ico', format='ICO')"

REM Bundle the project into a standalone single-file executable (.exe) including icons and local FFmpeg
echo [*] Starting Crimson compilation (this may take one or two minutes)...
pyinstaller --noconsole --onefile --icon="Icons/icone.ico" --collect-all PIL --add-data "Icons;Icons" --add-data "ffmpeg;ffmpeg" Crimson.py

REM Display completion message and wait for user input before closing the window
echo [*] Compilation completed successfully!
echo [*] Your executable (Crimson.exe) is available inside the 'dist' folder.
pause