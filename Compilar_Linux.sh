#!/bin/bash

# Se foi aberto via duplo clique (sem terminal), reabre dentro do Konsole
if [ ! -t 1 ]; then
    exec konsole --hold -e bash "$0"
fi

cd "$(dirname "$0")"

echo "=================================================="
echo "       COMPILANDO O PROJETO CRIMSON (LINUX)       "
echo "=================================================="
echo ""

echo "🧹 [1/3] Limpando compilações anteriores..."
rm -rf build dist Crimson.spec

echo "📦 [2/3] Empacotando dependências com PyInstaller..."
./venv/bin/pyinstaller --noconsole --onefile \
  --collect-all customtkinter \
  --collect-all PIL \
  --add-data "Icons:Icons" \
  Crimson.py

echo "🔑 [3/3] Aplicando permissão de execução..."
chmod +x dist/Crimson

echo ""
echo "=================================================="
echo "       ✅ COMPILAÇÃO CONCLUÍDA COM SUCESSO!       "
echo "=================================================="
echo "📁 Executável disponível em: dist/Crimson"
echo ""
read -p "Pressione [Enter] para fechar esta janela..."