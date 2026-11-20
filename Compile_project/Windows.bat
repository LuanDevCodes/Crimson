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
python -c "from PIL import Image; import glob; f = glob.glob('crimson/Icons/*Crimson*.png'); img = Image.open(f[0]).resize((256, 256)); img.save('crimson/Icons/icone.ico', format='ICO')"

REM Remove previous build artifacts to prevent packaging conflicts (same as Linux.sh)
echo [*] Cleaning previous builds...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist Crimson.spec del /Q Crimson.spec

REM Bundle the project into a standalone single-file executable (.exe) including icons and local FFmpeg
echo [*] Starting Crimson compilation (this may take one or two minutes)...
REM --name Crimson: nome do .exe | --paths .: ensina o PyInstaller a achar o pacote 'crimson' | crimson\__main__.py: ponto de entrada
REM --add-data LICENSE / THIRD_PARTY_NOTICES.md / licenses: the GPL and the bundled libraries require their license texts to travel with the executable
pyinstaller --noconsole --onefile --name Crimson --paths . --icon="crimson/Icons/icone.ico" --collect-all PIL --add-data "crimson/Icons;Icons" --add-data "ffmpeg;ffmpeg" --add-data "LICENSE;." --add-data "THIRD_PARTY_NOTICES.md;." --add-data "licenses;licenses" crimson/__main__.py

REM Release folder: the .exe and every document that must travel with it (the GPL and the bundled libraries require their license texts)
echo [*] Assembling the release folder...
set PACOTE=dist\Crimson-windows-x64
if exist %PACOTE% rmdir /S /Q %PACOTE%
mkdir %PACOTE%
copy /Y dist\Crimson.exe %PACOTE%\Crimson.exe
copy /Y LICENSE %PACOTE%\LICENSE.txt
copy /Y THIRD_PARTY_NOTICES.md %PACOTE%\THIRD_PARTY_NOTICES.md
xcopy /E /I /Y licenses %PACOTE%\licenses

REM Record exactly which FFmpeg build was bundled (the GPL requires offering the matching FFmpeg source code)
echo [*] Recording the bundled FFmpeg version...
ffmpeg\ffmpeg.exe -version > %PACOTE%\FFMPEG_VERSION.txt

REM Pack the release folder into a single ZIP, ready to be uploaded to the GitHub release
echo [*] Creating the release ZIP...
if exist dist\Crimson-windows-x64.zip del /Q dist\Crimson-windows-x64.zip
powershell -NoProfile -NonInteractive -Command "Compress-Archive -Path '%PACOTE%' -DestinationPath 'dist\Crimson-windows-x64.zip' -Force"

REM Display completion message and wait for user input before closing the window
echo [*] Compilation completed successfully!
echo [*] Release package: dist\Crimson-windows-x64.zip (upload this file to the GitHub release)
echo [!] REMINDER: also attach the FFmpeg source archive matching FFMPEG_VERSION.txt
echo [!] (see section 3 of THIRD_PARTY_NOTICES.md)
pause