# 🐧 Guia Linux — Configuração, Execução e Compilação

> 💡 **Dica do Fish Shell (padrão do CachyOS):**
> Para ativar o ambiente virtual no Fish Shell, use:
> `source venv/bin/activate.fish`
> *(Ou digite `bash` antes de começar para usar a sintaxe padrão do Bash)*

---

## ⚙️ 0. Pré-requisitos do Sistema

Antes de qualquer coisa, instale as dependências necessárias via gerenciador de pacotes.

**Arch Linux / CachyOS / Manjaro:**
```bash
sudo pacman -S ffmpeg python-tkinter
```

**Ubuntu / Linux Mint / Pop!_OS / Zorin OS:**
```bash
sudo apt install ffmpeg python3-tk
```

**Fedora / AlmaLinux / Rocky Linux:**
```bash
sudo dnf install ffmpeg python3-tkinter
```

**openSUSE:**
```bash
sudo zypper install ffmpeg python3-tk
```

> ⚠️ O `python3-tk` é obrigatório. Em muitas distros ele não vem junto com o Python padrão e precisa ser instalado separadamente.

---

## ⚡ 1. Rodar o Crimson pelo Terminal (caso queria rodar o código em si ao invés da aplicação)

```bash
# 1. Crie o ambiente virtual (só na primeira vez que for rodar o código)
python -m venv venv

# 2. Ative o venv
source venv/bin/activate        # Bash / Zsh
source venv/bin/activate.fish   # Fish Shell (padrão CachyOS)

# 3. Instale as dependências
pip install -r Linux/requirements_linux.txt

# 4. Execute o aplicativo
python Crimson.py
```

---

## 📦 2. Compilar o Executável Linux

O motivo do executável abrir e fechar rapidamente é que o **CustomTkinter** precisa ter seus arquivos internos de tema empacotados explicitamente com a flag `--collect-all customtkinter`. Sofri bastante com isso então segue como resolvi a compilação de maneira limpa:

```bash
# Com o venv ativado, na pasta raiz do projeto:
pyinstaller --noconsole --onefile \
  --collect-all customtkinter \
  --collect-all PIL \
  --add-data "Icons:Icons" \
  Crimson.py
```

Ou use o script pronto (mais simples):

```bash
bash Linux/compilar.sh
```

### Testar o executável gerado

```bash
# Roda o executável e mantém o terminal aberto para ver logs
./dist/Crimson
```

---

## 🎨 3. Criar o Atalho com Ícone (Opcional)

No Linux, ícones de aplicativos funcionam via arquivos `.desktop`. Isso coloca o Crimson no menu de aplicativos do sistema com o ícone oficial.

```bash
# 1. Permissão de execução ao executável
chmod +x dist/Crimson

# 2. Cria a pasta de atalhos (se não existir)
mkdir -p ~/.local/share/applications

# 3. Cria o atalho
cat <<EOF > ~/.local/share/applications/Crimson.desktop
[Desktop Entry]
Type=Application
Name=Crimson
Comment=Video and Audio Downloader
Exec=$(pwd)/dist/Crimson
Icon=$(pwd)/Icons/Crimson.png
Terminal=false
Categories=AudioVideo;Utility;Network;
StartupNotify=true
EOF

# 4. Permissão ao atalho
chmod +x ~/.local/share/applications/Crimson.desktop
```

Pronto! Busque por **Crimson** no menu do sistema para encontrar o atalho com ícone.

---

## 🔍 5. O que o Crimson adapta automaticamente no Linux

O mesmo `Crimson.py` funciona nos dois sistemas. A detecção é feita via `platform.system()` logo na inicialização.

| Ponto | Windows | Linux |
|---|---|---|
| **Pasta de configuração** | `%LOCALAPPDATA%\Crimson` | `~/.local/share/Crimson` |
| **FFmpeg** | Pasta local `ffmpeg/` do projeto | Instalado no sistema (`/usr/bin/ffmpeg`) |
| **Matar processos** | `taskkill /F /IM ffmpeg.exe` | `pkill -f ffmpeg` |
| **Tamanho da janela** | `600×300` | `700×360` (compensar DPI) |
| **Ícone do lançador** | `iconphoto()` | `wm_iconphoto()` |
| **Corner radius dos botões** | `8` | `18–20` (X11 renderiza diferente) |