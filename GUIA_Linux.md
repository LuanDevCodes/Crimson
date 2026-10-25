# 🐧 Guia Linux — Configuração, Execução e Compilação

> 💡 **Dica do Fish Shell (padrão do CachyOS):**
> Para ativar o ambiente virtual no Fish Shell, use:
> `source venv/bin/activate.fish`
> *(Ou digite `bash` antes de começar para usar a sintaxe padrão do Bash)*

---

## ⚙️ 0. Pré-requisitos do Sistema

Antes de qualquer coisa, instale o FFmpeg via gerenciador de pacotes da sua distribuição (usado para processar e converter mídias baixadas).

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

> 💡 O Crimson utiliza **PySide6 (Qt6)** para a interface gráfica moderna com anti-aliasing nativo, que é instalado automaticamente no ambiente virtual via `pip`.

---

## ⚡ 1. Rodar o Crimson pelo Terminal (caso queira rodar o código em si ao invés do executável)

```bash
# 1. Crie o ambiente virtual (só na primeira vez que for rodar o código)
python -m venv venv

# 2. Ative o venv
source venv/bin/activate        # Bash / Zsh
source venv/bin/activate.fish   # Fish Shell (padrão CachyOS)

# 3. Instale as dependências
pip install -r requirements_linux.txt

# 4. Execute o aplicativo
python Crimson.py
```

---

## 📦 2. Compilar o Executável Linux

O Crimson utiliza PyInstaller para empacotar a aplicação em um único binário com interface Qt6 e suporte gráfico completo:

```bash
# Com o venv ativado, na pasta raiz do projeto:
pyinstaller --noconsole --onefile \
  --collect-all PIL \
  --add-data "Icons:Icons" \
  Crimson.py
```

Ou use o script pronto (mais simples):

```bash
bash Compilar_Linux.sh
```

### Testar o executável gerado

```bash
# Roda o executável e mantém o terminal aberto para ver logs
./dist/Crimson
```

---

## 🎨 3. Criar o Atalho com Ícone (Menu do Sistema)

> 💡 **Por que o arquivo executável compilado (`dist/Crimson`) não tem ícone?**
> No Windows, executáveis `.exe` embutem o arquivo `.ico` internamente no binário.
> No Linux, os binários (formato **ELF**) **não possuem ícones embutidos**. Nenhum aplicativo no Linux (nem navegadores, nem jogos) exibe ícone no arquivo binário cru no gerenciador de arquivos (Dolphin/Nautilus).
> O ícone oficial do aplicativo no Linux é exibido através de um atalho `.desktop` no menu de aplicativos do sistema ou na barra de tarefas (dock).

Para criar o atalho com o ícone oficial no menu de aplicativos:

```bash
# 1. Permissão de execução ao executável
chmod +x dist/Crimson

# 2. Cria a pasta de atalhos do usuário (se ainda não existir)
mkdir -p ~/.local/share/applications

# 3. Cria o atalho apontando para o executável e o ícone
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

# 4. Dá permissão ao atalho e atualiza o banco de dados de atalhos
chmod +x ~/.local/share/applications/Crimson.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null
```

Pronto! Agora o **Crimson** aparecerá no menu do sistema (KDE/GNOME) com o seu ícone oficial e poderá ser fixado na barra de tarefas ou na Área de Trabalho.

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
| **Corner radius dos botões** | `8` | `8` (padronizado para evitar artefatos no Canvas) |