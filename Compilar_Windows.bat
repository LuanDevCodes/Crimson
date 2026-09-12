@echo off
echo [*] Preparando o ambiente de compilacao...
call venv\Scripts\activate.bat

echo [*] Verificando dependencias necessarias para compilacao (PyInstaller e Pillow)...
pip install pyinstaller pillow

echo [*] Padronizando as dimensoes e convertendo icone PNG para ICO...
python -c "from PIL import Image; import glob; f = glob.glob('Icons/*Crimson*.png'); img = Image.open(f[0]).resize((256, 256)); img.save('Icons/icone.ico', format='ICO')"

echo [*] Iniciando compilacao do Crimson (Isso pode levar um ou dois minutos)...
pyinstaller --noconsole --onefile --icon="Icons/icone.ico" --add-data "Icons;Icons" --add-data "ffmpeg;ffmpeg" Crimson.py

echo [*] Compilacao concluida com sucesso!
echo [*] O seu executavel (Crimson.exe) esta disponivel dentro da pasta 'dist'.
pause