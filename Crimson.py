# Projeto Crimson - Uma interface capaz de baixar vídeos de diversas plataformas de forma simples
# Criei esse projeto pela necessidade de uma ferramenta útil e confiável para tal, nascendo assim ele :D
#
# Copyright (C) 2026 LuanDevCodes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import os  # Biblioteca para interagir com o sistema operacional (ex: navegar entre pastas, verificar se um arquivo existe, criar pastas e ler variáveis)
import sys  # Necessário para identificar se está rodando como .exe
import glob  # Para manipulação dos caminhos dos arquivos, além de ajudar na exclusão dos arquivos residuais
import threading  # Biblioteca para criar rotinas em segundo plano (evita que a tela trave)
import time  # Controle de intervalos e throttling para manter a UI leve
import gc  # Coleta de lixo forçada para liberar memória imediatamente em máquinas modestas
import re  # Usado para limpar textos gerados pelo yt-dlp
import subprocess  # Usado para executar comandos do sistema (como atualizar o yt-dlp ou finalizar processos)
import webbrowser  # Usado para abrir links na internet (como no caso dos links dos repositórios usados)
import json  # Biblioteca nativa para salvar e ler dados configurados usando esse formato de arquivo
import urllib.request  # Biblioteca nativa para baixar arquivos da internet
import zipfile  # Biblioteca nativa para extrair arquivos compactados
import shutil  # Usado para limpeza segura de pastas temporárias e localização de binários no sistema
import importlib  # Permite recarregar o motor yt-dlp em memória após atualização sem reiniciar o app
import platform  # Detecta o sistema operacional para adaptar os caminhos
import random  # Usado para gerar posições e tamanhos aleatórios das bolhas Frutiger Aero
import math  # Usado para a oscilação senoidal das bolhas
from datetime import datetime  # Usado para carimbar data e hora nos registros de erro
from PIL import Image  # Biblioteca 'Pillow', ajuda na manipulação de canais RGBA e recoloração dinâmica dos ícones

# Bibliotecas do PySide6 (Qt6) para uma interface gráfica moderna, com anti-aliasing nativo no Windows e Linux
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QProgressBar, QDialog, QTabWidget, QFrame, QMessageBox,
    QFileDialog, QMenu, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QSize, Signal, QObject, QPointF, QTimer, QRectF, QEvent, QStandardPaths
from PySide6.QtGui import (
    QIcon, QPixmap, QImage, QColor, QCursor, QAction,
    QPainter, QPen, QPainterPath, QPalette, QLinearGradient, QRadialGradient, QConicalGradient, QBrush
)

# Constante única de versão para manter sincronia em toda a aplicação
VERSAO_APP = "V.3.0.0"

# -------------------------------
# --- Setup de Diretórios do Aplicativo (AppData) e Persistência ---

SISTEMA = platform.system()  # Retorna 'Windows', 'Linux' ou 'Darwin' (macOS)

# No Windows: usa a pasta oficial LocalAppData (ex: C:\Users\Luan\AppData\Local\Crimson)
# No Linux:   segue o padrão XDG, que é ~/.local/share/Crimson
if SISTEMA == 'Windows':
    appdata_local = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
else:
    appdata_local = os.path.join(os.path.expanduser('~'), '.local', 'share')

crimson_dir = os.path.join(appdata_local, 'Crimson')
lib_dir = os.path.join(crimson_dir, 'Lib')
config_dir = os.path.join(crimson_dir, 'Config')
config_file = os.path.join(config_dir, 'config.json')
errors_file = os.path.join(config_dir, 'errors_crimson.log')

# Cria as pastas caso elas não existam no computador desse usuário
os.makedirs(lib_dir, exist_ok=True)
os.makedirs(config_dir, exist_ok=True)

# --- Função de Registro de Erros ---
def registrar_erro(contexto, erro):
    
    # Salva falhas técnicas em arquivo dedicado na pasta Config para diagnóstico sem expor dados sensíveis
    try:
        os.makedirs(config_dir, exist_ok=True)
        carimbo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(errors_file, 'a', encoding='utf-8') as f:
            f.write(f"[{carimbo}] [{contexto}] {repr(erro)}\n")
    except Exception:
        pass

# --- Injeção de Dependência Modular com Autorrecuperação ---
# Procura se o motor do yt-dlp já foi baixado na pasta Lib
# Se existir, força o Python a ler as bibliotecas dessa pasta antes das bibliotecas congeladas (PyInstaller)
path_yt_dlp = os.path.join(lib_dir, 'yt-dlp-master')

if os.path.exists(path_yt_dlp):
    sys.path.insert(0, path_yt_dlp)  # O insert 0 diz basicamente "olhe aqui antes de qualquer outro lugar"

try:
    import yt_dlp  # Tenta importar o motor atualizado (ou local se a pasta externa não existir)
except Exception as erro_import_ytdlp:
    
    # Se a pasta externa estiver corrompida por queda de energia/rede anterior, limpa e usa o motor nativo
    registrar_erro("import_yt_dlp_externo", erro_import_ytdlp)
    
    if path_yt_dlp in sys.path:
        sys.path.remove(path_yt_dlp)
    for modulo_nome in list(sys.modules.keys()):
        if modulo_nome == "yt_dlp" or modulo_nome.startswith("yt_dlp."):
            sys.modules.pop(modulo_nome, None)
    shutil.rmtree(path_yt_dlp, ignore_errors=True)
    import yt_dlp

# -------------------------------
# *******************************
# -------------------------------

# --- Funções de Leitura e Escrita do JSON ---
def carregar_configuracoes():
    
    padrao = {"idioma": "English", "tema": "Frutiger Aero", "desativar_animacoes": False}
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                return dados
        except Exception as erro_json:
            registrar_erro("carregar_configuracoes", erro_json)
    return padrao

def salvar_configuracoes(idioma, tema, desativar_anim=False):
    try:
        os.makedirs(config_dir, exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    "idioma": idioma,
                    "tema": tema,
                    "desativar_animacoes": bool(desativar_anim)
                },
                f,
                indent=4
            )
        return True
    except Exception as erro_salvar:
        registrar_erro("salvar_configuracoes", erro_salvar)
        return False

# Dicionário global de configurações ativas
config_atual = carregar_configuracoes()
idioma_atual = config_atual.get("idioma", "English")
tema_atual = config_atual.get("tema", "Frutiger Aero")
desativar_animacoes = bool(config_atual.get("desativar_animacoes", False))

# Definindo cores nos temas do Crimson
TEMAS = {
    "Frutiger Aero": {
        "cor_fundo_janela":             "#DDF2FF",  # azul suave aqua cristalino
        "cor_card":                     "#F0F9FF",  # placa translúcida de vidro
        "cor_borda_card":               "#96D2FF",  # borda luminosa celeste
        "cor_do_texto":                 "#0C2D48",  # azul marinho profundo de alto contraste
        "cor_texto_secundario":         "#1D5E85",  # azul oceano secundário
        "cor_botao_audio":              "#0088FF",  # azul aqua cristalino
        "cor_botao_audio_hover":        "#1FA3FF",  # hover áudio
        "cor_botao_video":              "#22A645",  # verde tropical vibrante
        "cor_botao_video_hover":        "#2BC253",  # hover vídeo
        "cor_fonte_botoes":             "#FFFFFF",  # texto branco puro
        "cor_barra_de_pesquisa":        "#EAF6FF",  # barra azul-gelo suave (sem branco estourado)
        "cor_texto_caixa_de_pesquisa":  "#0C2D48",  # texto da barra
        "cor_de_fundo_dropdown":        "#EAF6FF",  # fundo dropdown azul-gelo suave
        "cor_do_hover_dropdown":        "#C8E8FF",  # hover dropdown celeste vítreo
        "cor_da_borda_botao_video":     "#188634",  # borda vídeo
        "cor_da_borda_botao_audio":     "#006ECC",  # borda áudio
        "cor_do_texto_magua":           "#4682A9",  # marca d'água
        "cor_progresso_fundo":          "#D4EFFF",  # trilho
        "cor_progresso_barra":          "#0088FF"   # barra de progresso
    },

    "Egg": {
        "cor_fundo_janela":             "#E9E3BC",  # cor de fundo da janela
        "cor_card":                     "#F3EED2",  # cor de superfície dos cards
        "cor_borda_card":               "#DCD3A3",  # cor sutil da borda dos cards
        "cor_do_texto":                 "#333333",  # cor do texto principal
        "cor_texto_secundario":         "#635E46",  # cor de subtítulos e dicas
        "cor_botao_audio":              "#F2CC8F",  # cor do botão de áudio
        "cor_botao_audio_hover":        "#E6BC7A",  # cor do botão de áudio no hover
        "cor_botao_video":              "#EDD66F",  # cor do botão de vídeo
        "cor_botao_video_hover":        "#DFC658",  # cor do botão de vídeo no hover
        "cor_fonte_botoes":             "#2B2618",  # cor da fonte dos botões
        "cor_barra_de_pesquisa":        "#FCF8E9",  # cor da barra de pesquisa
        "cor_texto_caixa_de_pesquisa":  "#5A4908",  # cor do texto dentro da barra de pesquisa
        "cor_de_fundo_dropdown":        "#FAF4DC",  # cor de fundo dentro do dropdown
        "cor_do_hover_dropdown":        "#E5DAAA",  # cor quando o mouse passa por cima no dropdown
        "cor_da_borda_botao_video":     "#D9C052",  # cor da borda do vídeo
        "cor_da_borda_botao_audio":     "#DFB878",  # cor da borda do áudio
        "cor_do_texto_magua":           "#787259",  # cor da marca d'água
        "cor_progresso_fundo":          "#DDD5A8",  # trilho da barra de progresso
        "cor_progresso_barra":          "#D4A73F"   # preenchimento da barra de progresso
    },

    "Dark": {
        "cor_fundo_janela":             "#24252D",  # cor de fundo da janela
        "cor_card":                     "#2E303B",  # cor de superfície dos cards
        "cor_borda_card":               "#3D404F",  # cor sutil da borda dos cards
        "cor_do_texto":                 "#EDF2F4",  # cor do texto principal
        "cor_texto_secundario":         "#A4ACB8",  # cor de subtítulos e dicas
        "cor_botao_audio":              "#6C7D97",  # cor do botão de áudio
        "cor_botao_audio_hover":        "#7E90AC",  # cor do botão de áudio no hover
        "cor_botao_video":              "#457B9D",  # cor do botão de vídeo
        "cor_botao_video_hover":        "#568CAE",  # cor do botão de vídeo no hover
        "cor_fonte_botoes":             "#FFFFFF",  # cor da fonte dos botões
        "cor_barra_de_pesquisa":        "#1D1E25",  # cor da barra de pesquisa
        "cor_texto_caixa_de_pesquisa":  "#EDF2F4",  # cor do texto dentro da barra de pesquisa
        "cor_de_fundo_dropdown":        "#353846",  # cor de fundo dentro do dropdown
        "cor_do_hover_dropdown":        "#484C5E",  # cor quando o mouse passa por cima no dropdown
        "cor_da_borda_botao_video":     "#568CAE",  # cor da borda do vídeo
        "cor_da_borda_botao_audio":     "#8091AC",  # cor da borda do áudio
        "cor_do_texto_magua":           "#8C93A0",  # cor da marca d'água
        "cor_progresso_fundo":          "#1D1E25",  # trilho da barra de progresso
        "cor_progresso_barra":          "#568CAE"   # preenchimento da barra de progresso
    },

    "Matcha": {
        "cor_fundo_janela":             "#B2CC8E",  # cor de fundo da janela
        "cor_card":                     "#C2D9A3",  # cor de superfície dos cards
        "cor_borda_card":               "#9AB675",  # cor sutil da borda dos cards
        "cor_do_texto":                 "#1B272C",  # cor do texto principal
        "cor_texto_secundario":         "#3B512B",  # cor de subtítulos e dicas
        "cor_botao_audio":              "#5C7341",  # cor do botão de áudio
        "cor_botao_audio_hover":        "#6B864B",  # cor do botão de áudio no hover
        "cor_botao_video":              "#4B7321",  # cor do botão de vídeo
        "cor_botao_video_hover":        "#5C8B29",  # cor do botão de vídeo no hover
        "cor_fonte_botoes":             "#FFFFFF",  # cor da fonte dos botões
        "cor_barra_de_pesquisa":        "#E2EDD8",  # cor da barra de pesquisa
        "cor_texto_caixa_de_pesquisa":  "#213313",  # cor do texto dentro da barra de pesquisa
        "cor_de_fundo_dropdown":        "#D4E4C3",  # cor de fundo dentro do dropdown
        "cor_do_hover_dropdown":        "#B3CA9A",  # cor quando o mouse passa por cima no dropdown
        "cor_da_borda_botao_video":     "#43671D",  # cor da borda do vídeo
        "cor_da_borda_botao_audio":     "#506638",  # cor da borda do áudio
        "cor_do_texto_magua":           "#375223",  # cor da marca d'água
        "cor_progresso_fundo":          "#9AB578",  # trilho da barra de progresso
        "cor_progresso_barra":          "#4B7321"   # preenchimento da barra de progresso
    },

    "Savage": {
        "cor_fundo_janela":             "#190507",  # preto carmesim profundo e puro
        "cor_card":                     "#27090D",  # vermelho escuro de superfície
        "cor_borda_card":               "#4D1219",  # contorno vermelho escuro nobre
        "cor_do_texto":                 "#F5F5F7",  # branco puro límpido sem tom rosa
        "cor_texto_secundario":         "#A89295",  # cinza quente suave
        "cor_botao_audio":              "#800E13",  # vermelho escuro sangue
        "cor_botao_audio_hover":        "#9E1319",  # hover áudio
        "cor_botao_video":              "#C1121F",  # vermelho puro vivo esplendoroso
        "cor_botao_video_hover":        "#DF1827",  # hover vídeo
        "cor_fonte_botoes":             "#FFFFFF",  # texto branco puro
        "cor_barra_de_pesquisa":        "#120305",  # fundo da barra de pesquisa
        "cor_texto_caixa_de_pesquisa":  "#F5F5F7",  # texto barra
        "cor_de_fundo_dropdown":        "#330B10",  # dropdown fechado
        "cor_do_hover_dropdown":        "#4A1017",  # hover dropdown
        "cor_da_borda_botao_video":     "#DF1827",  # borda vídeo
        "cor_da_borda_botao_audio":     "#9E1319",  # borda áudio
        "cor_do_texto_magua":           "#8F7578",  # marca d'água
        "cor_progresso_fundo":          "#120305",  # trilho
        "cor_progresso_barra":          "#C1121F"   # barra de progresso
    },

    "Platinum Disc": {
        "cor_fundo_janela":             "#181B22",  # fundo aço platina escovado profundo
        "cor_card":                     "#252B37",  # placa metálica de platina escovada
        "cor_borda_card":               "#8FA3BF",  # borda cromo escovado reluzente
        "cor_do_texto":                 "#F8FAFC",  # texto prata de alto contraste
        "cor_texto_secundario":         "#94A3B8",  # texto secundário estanho acetinado
        "cor_botao_audio":              "#52647E",  # botão áudio aço escovado
        "cor_botao_audio_hover":        "#657997",  # hover áudio
        "cor_botao_video":              "#607E9E",  # botão vídeo platina polida
        "cor_botao_video_hover":        "#7394B7",  # hover vídeo
        "cor_fonte_botoes":             "#FFFFFF",  # texto branco puro
        "cor_barra_de_pesquisa":        "#161920",  # barra aço grafite
        "cor_texto_caixa_de_pesquisa":  "#F8FAFC",  # texto barra
        "cor_de_fundo_dropdown":        "#232934",  # fundo dropdown metal escovado
        "cor_do_hover_dropdown":        "#384252",  # hover dropdown
        "cor_da_borda_botao_video":     "#A2B9D7",  # borda vídeo platina reluzente
        "cor_da_borda_botao_audio":     "#8FA3BF",  # borda áudio aço polido
        "cor_do_texto_magua":           "#7A8B9E",  # marca d'água
        "cor_progresso_fundo":          "#161920",  # trilho
        "cor_progresso_barra":          "#8EA7C7"   # preenchimento platina lustrosa
    }
}

IDIOMAS_SUPORTADOS = [
    "Arabic",
    "Bambara",
    "Bengali",
    "Chinese",
    "Dutch",
    "English",
    "Filipino",
    "French",
    "German",
    "Hausa",
    "Hindi",
    "Indonesian",
    "Italian",
    "Japanese",
    "Korean",
    "Latin",
    "Norwegian",
    "Persian",
    "Polish",
    "Portuguese",
    "Russian",
    "Spanish",
    "Turkish",
    "Ukrainian",
    "Vietnamese"
]

# Validação defensiva contra valores inválidos ou adulterados manualmente no config.json
if idioma_atual not in IDIOMAS_SUPORTADOS:
    idioma_atual = "English"
if tema_atual not in TEMAS:
    tema_atual = "Frutiger Aero"

DICIONARIO_IDIOMAS = {
    "instrucao_init": {
        "Portuguese": "Procurando atualizações de segurança...",
        "English": "Checking for security updates...",
        "Spanish": "Buscando actualizaciones de seguridad...",
        "Chinese": "正在检查安全更新...",
        "Japanese": "セキュリティアップデートを確認中...",
        "Korean": "보안 업데이트 확인 중...",
        "Russian": "Поиск обновлений безопасности...",
        "Ukrainian": "Перевірка оновлень безпеки...",
        "Indonesian": "Memeriksa pembaruan keamanan...",
        "Filipino": "Nagsusuri para sa mga update sa seguridad...",
        "Vietnamese": "Đang kiểm tra cập nhật bảo mật...",
        "Norwegian": "Ser etter sikkerhetsoppdateringer...",
        "Hausa": "Ana duba sabuntawar tsaro...",
        "Bambara": "Kalan kɛnɛya lakodɔn kɔlɔsili sen bɛ kɛ...",
        "Latin": "Securitatis renovatio quaeritur...",
        "Arabic": "جارٍ البحث عن تحديثات الأمان...",
        "Bengali": "নিরাপত্তা আপডেটের খোঁজ করা হচ্ছে...",
        "Dutch": "Zoeken naar beveiligingsupdates...",
        "French": "Recherche des mises à jour de sécurité...",
        "German": "Nach Sicherheitsupdates suchen...",
        "Hindi": "सुरक्षा अपडेट की जाँच की जा रही है...",
        "Italian": "Ricerca aggiornamenti di sicurezza...",
        "Persian": "در حال بررسی به‌روزرسانی‌های امنیتی...",
        "Polish": "Szukanie aktualizacji zabezpieczeń...",
        "Turkish": "Güvenlik güncellemeleri kontrol ediliyor..."
    },
    "instrucao_ready": {
        "Portuguese": "Insira a URL do vídeo:",
        "English": "Enter the video URL:",
        "Spanish": "Introduce la URL del vídeo:",
        "Chinese": "请输入视频链接：",
        "Japanese": "動画のURLを入力してください:",
        "Korean": "동영상 URL을 입력하세요:",
        "Russian": "Введите URL-адрес видео:",
        "Ukrainian": "Введіть URL-адресу відео:",
        "Indonesian": "Masukkan URL video:",
        "Filipino": "Ilagay ang URL ng video:",
        "Vietnamese": "Nhập URL video:",
        "Norwegian": "Skriv inn video-URL:",
        "Hausa": "Shigar da adireshin bidiyo (URL):",
        "Bambara": "Wideyo URL bila yan:",
        "Latin": "Inscriptionem (URL) cinematographi insere:...",
        "Arabic": "أدخل رابط الفيديو:",
        "Bengali": "ভিডিওর URL লিখুন:",
        "Dutch": "Voer de video-URL in:",
        "French": "Entrez l'URL de la vidéo :",
        "German": "Video-URL eingeben:",
        "Hindi": "वीडियो का URL दर्ज करें:",
        "Italian": "Inserisci l'URL del video:",
        "Persian": "نشانی اینترنتی (URL) ویدیو را وارد کنید:",
        "Polish": "Wprowadź adres URL wideo:",
        "Turkish": "Video bağlantısını (URL) girin:"
    },
    "placeholder_url": {
        "Portuguese": "Cole aqui o link do vídeo ou música",
        "English": "Paste the video or music link here",
        "Spanish": "Pega aquí el enlace del vídeo o música",
        "Chinese": "在此粘贴视频或音乐链接",
        "Japanese": "動画または音楽のリンクをここに貼り付け",
        "Korean": "동영상 또는 음악 링크를 여기에 붙여넣으세요",
        "Russian": "Вставьте ссылку на видео или музыку",
        "Ukrainian": "Вставте посилання на видео або музику",
        "Indonesian": "Tempel tautan video atau musik di sini",
        "Filipino": "I-paste dito ang link ng video o musika",
        "Vietnamese": "Dán liên kết video hoặc âm nhạc vào đây",
        "Norwegian": "Lim inn lenken til video eller musikk her",
        "Hausa": "Manna mahadar bidiyo ko kiɗa a nan",
        "Bambara": "Wideyo walima dɔnkili sirilen bila yan",
        "Latin": "Hic nexum cinematographi vel soni insere",
        "Arabic": "الصق رابط الفيديو أو الموسيقى هنا",
        "Bengali": "এখানে ভিডিও বা গানের লিঙ্ক পেস্ট করুন",
        "Dutch": "Plak hier de link van de video of muziek",
        "French": "Collez le lien de la vidéo ou de la musique ici",
        "German": "Video- oder Musiklink hier einfügen",
        "Hindi": "यहाँ वीडियो या संगीत का लिंक चिपकाएँ",
        "Italian": "Incolla qui il link del video o della musica",
        "Persian": "پیوند ویدیو یا موسیقی را اینجا جای‌گذاری کنید",
        "Polish": "Wklej tutaj link do filmu lub muzyki",
        "Turkish": "Video veya müzik bağlantısını buraya yapıştırın"
    },
    "titulo_card_audio": {
        "Portuguese": "ÁUDIO",
        "English": "AUDIO",
        "Spanish": "AUDIO",
        "Chinese": "音频",
        "Japanese": "音声",
        "Korean": "오디오",
        "Russian": "АУДИО",
        "Ukrainian": "АУДІО",
        "Indonesian": "AUDIO",
        "Filipino": "AUDIO",
        "Vietnamese": "ÂM THANH",
        "Norwegian": "LYD",
        "Hausa": "SAUTI",
        "Bambara": "MANKAN",
        "Latin": "SONUS",
        "Arabic": "صوت",
        "Bengali": "অডিও",
        "Dutch": "AUDIO",
        "French": "AUDIO",
        "German": "AUDIO",
        "Hindi": "ऑडियो",
        "Italian": "AUDIO",
        "Persian": "صوتی",
        "Polish": "AUDIO",
        "Turkish": "SES"
    },
    "titulo_card_video": {
        "Portuguese": "VÍDEO",
        "English": "VIDEO",
        "Spanish": "VÍDEO",
        "Chinese": "视频",
        "Japanese": "動画",
        "Korean": "비디오",
        "Russian": "ВИДЕО",
        "Ukrainian": "ВІДЕО",
        "Indonesian": "VIDEO",
        "Filipino": "VIDEO",
        "Vietnamese": "VIDEO",
        "Norwegian": "VIDEO",
        "Hausa": "BIDIYO",
        "Bambara": "WIDEYO",
        "Latin": "VISIO",
        "Arabic": "فيديو",
        "Bengali": "ভিডিও",
        "Dutch": "VIDEO",
        "French": "VIDÉO",
        "German": "VIDEO",
        "Hindi": "वीडियो",
        "Italian": "VIDEO",
        "Persian": "ویدیو",
        "Polish": "WIDEO",
        "Turkish": "VİDEO"
    },
    "cor_botao_audio": {
        "Portuguese": "Baixar Áudio",
        "English": "Download Audio",
        "Spanish": "Descargar Audio",
        "Chinese": "下载音频",
        "Japanese": "音声をダウンロード",
        "Korean": "오디오 다운로드",
        "Russian": "Скачать аудио",
        "Ukrainian": "Завантажити аудіо",
        "Indonesian": "Unduh Audio",
        "Filipino": "I-download ang Audio",
        "Vietnamese": "Tải âm thanh",
        "Norwegian": "Last ned lyd",
        "Hausa": "Zazzage Sauti",
        "Bambara": "Mankan Ladon",
        "Latin": "Sonum Depromere",
        "Arabic": "تحميل الصوت",
        "Bengali": "অডিও ডাউনলোড করুন",
        "Dutch": "Audio Downloaden",
        "French": "Télécharger l'audio",
        "German": "Audio herunterladen",
        "Hindi": "ऑडियो डाउनलोड करें",
        "Italian": "Scarica Audio",
        "Persian": "دانلود صدا",
        "Polish": "Pobierz audio",
        "Turkish": "Sesi İndir"
    },
    "cor_botao_video": {
        "Portuguese": "Baixar Vídeo",
        "English": "Download Video",
        "Spanish": "Descargar Vídeo",
        "Chinese": "下载视频",
        "Japanese": "動画をダウンロード",
        "Korean": "비디오 다운로드",
        "Russian": "Скачать видео",
        "Ukrainian": "Завантажити відео",
        "Indonesian": "Unduh Video",
        "Filipino": "I-download ang Video",
        "Vietnamese": "Tải video",
        "Norwegian": "Last ned video",
        "Hausa": "Zazzage Bidiyo",
        "Bambara": "Wideyo Ladon",
        "Latin": "Visionem Depromere",
        "Arabic": "تحميل الفيديو",
        "Bengali": "ভিডিও ডাউনলোড করুন",
        "Dutch": "Video Downloaden",
        "French": "Télécharger la vidéo",
        "German": "Video herunterladen",
        "Hindi": "वीडियो डाउनलोड करें",
        "Italian": "Scarica Video",
        "Persian": "دانلود ویدیو",
        "Polish": "Pobierz wideo",
        "Turkish": "Videoyu İndir"
    },
    "aba_sistema": {
        "Portuguese": "Sistema",
        "English": "System",
        "Spanish": "Sistema",
        "Chinese": "系统",
        "Japanese": "システム",
        "Korean": "시스템",
        "Russian": "Система",
        "Ukrainian": "Система",
        "Indonesian": "Sistem",
        "Filipino": "Sistema",
        "Vietnamese": "Hệ thống",
        "Norwegian": "System",
        "Hausa": "Tsarin Aiki",
        "Bambara": "Labɛn Cogo",
        "Latin": "Systema",
        "Arabic": "النظام",
        "Bengali": "সিস্টেম",
        "Dutch": "Systeem",
        "French": "Système",
        "German": "System",
        "Hindi": "सिस्टम",
        "Italian": "Sistema",
        "Persian": "سیستم",
        "Polish": "System",
        "Turkish": "Sistem"
    },
    "aba_sobre": {
        "Portuguese": "Sobre",
        "English": "About",
        "Spanish": "Acerca de",
        "Chinese": "关于",
        "Japanese": "概要",
        "Korean": "정보",
        "Russian": "О программе",
        "Ukrainian": "Про програму",
        "Indonesian": "Tentang",
        "Filipino": "Tungkol",
        "Vietnamese": "Giới thiệu",
        "Norwegian": "Om",
        "Hausa": "Game da",
        "Bambara": "Koo La",
        "Latin": "De Hoc",
        "Arabic": "حول",
        "Bengali": "সম্পর্কে",
        "Dutch": "Over",
        "French": "À propos",
        "German": "Über",
        "Hindi": "के बारे में",
        "Italian": "Informazioni",
        "Persian": "درباره",
        "Polish": "O programie",
        "Turkish": "Hakkında"
    },
    "lbl_idioma": {
        "Portuguese": "Idioma do Aplicativo:",
        "English": "Application Language:",
        "Spanish": "Idioma de la Aplicación:",
        "Chinese": "应用语言：",
        "Japanese": "アプリの言語:",
        "Korean": "애플리케이션 언어:",
        "Russian": "Язык приложения:",
        "Ukrainian": "Мова програми:",
        "Indonesian": "Bahasa Aplikasi:",
        "Filipino": "Wika ng Application:",
        "Vietnamese": "Ngôn ngữ ứng dụng:",
        "Norwegian": "Applikasjonsspråk:",
        "Hausa": "Yaren Manhaja:",
        "Bambara": "Porogaramu Kan:",
        "Latin": "Applicatio Lingua:",
        "Arabic": "لغة التطبيق:",
        "Bengali": "অ্যাপ্লিকেশনের ভাষা:",
        "Dutch": "Applicatietaal:",
        "French": "Langue de l'application :",
        "German": "Anwendungssprache:",
        "Hindi": "एप्लिकेशन की भाषा:",
        "Italian": "Lingua dell'applicazione:",
        "Persian": "زبان برنامه:",
        "Polish": "Język aplikacji:",
        "Turkish": "Uygulama Dili:"
    },
    "lbl_tema": {
        "Portuguese": "Tema da Interface:",
        "English": "Interface Theme:",
        "Spanish": "Tema de la Interfaz:",
        "Chinese": "界面主题：",
        "Japanese": "テーマ:",
        "Korean": "인터페이스 테마:",
        "Russian": "Тема интерфейса:",
        "Ukrainian": "Тема інтерфейсу:",
        "Indonesian": "Tema Tampilan:",
        "Filipino": "Tema ng Interface:",
        "Vietnamese": "Giao diện chủ đề:",
        "Norwegian": "Grensesnittema:",
        "Hausa": "Kalar Fuskantar Aiki:",
        "Bambara": "Jateminɛ Kulɛri:",
        "Latin": "Forma Argumenti:",
        "Arabic": "سمة الواجهة:",
        "Bengali": "ইন্টারফেসের থিম:",
        "Dutch": "Interfacethema:",
        "French": "Thème de l'interface :",
        "German": "Oberflächendesign:",
        "Hindi": "इंटरफ़ेस थीम:",
        "Italian": "Tema interfaccia:",
        "Persian": "پوسته رابط کاربری:",
        "Polish": "Motyw interfejsu:",
        "Turkish": "Arayüz Teması:"
    },
    "lbl_versao": {
        "Portuguese": f"Versão atual: {VERSAO_APP}",
        "English": f"Current version: {VERSAO_APP}",
        "Spanish": f"Versión actual: {VERSAO_APP}",
        "Chinese": f"当前版本：{VERSAO_APP}",
        "Japanese": f"現在のバージョン: {VERSAO_APP}",
        "Korean": f"현재 버전: {VERSAO_APP}",
        "Russian": f"Текущая версия: {VERSAO_APP}",
        "Ukrainian": f"Поточна версія: {VERSAO_APP}",
        "Indonesian": f"Versi saat ini: {VERSAO_APP}",
        "Filipino": f"Kasalukuyang bersyon: {VERSAO_APP}",
        "Vietnamese": f"Phiên bản hiện tại: {VERSAO_APP}",
        "Norwegian": f"Gjeldende versjon: {VERSAO_APP}",
        "Hausa": f"Fasalin yanzu: {VERSAO_APP}",
        "Bambara": f"Sisan kɔnɔko: {VERSAO_APP}",
        "Latin": f"Editio currens: {VERSAO_APP}",
        "Arabic": f"الإصدار الحالي: {VERSAO_APP}",
        "Bengali": f"বর্তমান সংস্করণ: {VERSAO_APP}",
        "Dutch": f"Huidige versie: {VERSAO_APP}",
        "French": f"Version actuelle : {VERSAO_APP}",
        "German": f"Aktuelle Version: {VERSAO_APP}",
        "Hindi": f"वर्तमान संस्करण: {VERSAO_APP}",
        "Italian": f"Versione attuale: {VERSAO_APP}",
        "Persian": f"نسخه فعلی: {VERSAO_APP}",
        "Polish": f"Aktualna wersja: {VERSAO_APP}",
        "Turkish": f"Mevcut sürüm: {VERSAO_APP}"
    },
    "txt_disclaimer": {
        "Portuguese": "Desenvolvido sem fins comerciais\nQualquer distribuição deve ser gratuita\ne livre para todos",
        "English": "Developed for non-commercial purposes\nAny distribution must be free\nand available to everyone",
        "Spanish": "Desarrollado sin fines comerciales\nCualquier distribución debe ser gratuita\ny accesible para todos",
        "Chinese": "非商业目的开发\n任何分发必须免费\n并对所有人开放",
        "Japanese": "非営利目的で開発されました\nすべての配布は無料であり\n誰でも利用可能である必要があります",
        "Korean": "비영리 목적으로 개발되었습니다\n모든 배포는 무료여야 하며\n누구에게나 공개되어야 합니다",
        "Russian": "Разработано в некоммерческих целях\nЛюбое распространение должно быть бесплатным\nи доступным для всех",
        "Ukrainian": "Розроблено в некомерційних цілях\nБудь-яке розповсюдження має бути безкоштовним\nі доступним для кожного",
        "Indonesian": "Dikembangkan untuk tujuan non-komersial\nSetiap distribusi harus gratis\ndan terbuka untuk semua orang",
        "Filipino": "Binuo para sa hindi pang-komersyal na layunin\nAng anumang pamamahagi ay dapat libre\nat bukas para sa lahat",
        "Vietnamese": "Được phát triển cho mục đích phi thương mại\nMọi phân phối phải hoàn toàn miễn phí\nvà dành cho tất cả mọi người",
        "Norwegian": "Utviklet for ikke-kommersielle formål\nEnhver distribusjon må være gratis\nog tilgjengelig for alle",
        "Hausa": "An ƙirƙira don amfanin jama'a ba don kasuwanci ba\nDuk wani rarrabawa dole ya zama kyauta\nkuma ga kowa da kowa",
        "Bambara": "A dabɔra dɔrɔn maana tɛ sɔrɔ la\nA tila bɛɛ ye fuu ye\nka kɛ bɛɛ ta ye lakika",
        "Latin": "Sine quaestu mercatorio creatum\nOmnis distributio gratuita ac libera\nomnibus esse debet",
        "Arabic": "طُوّر لأغراض غير تجارية\nيجب أن يكون أي توزيع مجانيًا\nومتاحًا للجميع",
        "Bengali": "অবাণিজ্যিক উদ্দেশ্যে তৈরি\nযেকোনো বিতরণ বিনামূল্যে\nএবং সবার জন্য উন্মুক্ত হতে হবে",
        "Dutch": "Ontwikkeld voor niet-commerciële doeleinden\nElke distributie moet gratis zijn\nen voor iedereen toegankelijk",
        "French": "Développé à des fins non commerciales\nToute distribution doit être gratuite\net accessible à tous",
        "German": "Entwickelt für nicht-kommerzielle Zwecke\nJede Weitergabe muss kostenlos\nund für alle frei zugänglich sein",
        "Hindi": "गैर-व्यावसायिक उद्देश्यों के लिए विकसित\nकोई भी वितरण निःशुल्क\nऔर सभी के लिए उपलब्ध होना चाहिए",
        "Italian": "Sviluppato per scopi non commerciali\nQualsiasi distribuzione deve essere gratuita\ne accessibile a tutti",
        "Persian": "توسعه‌یافته برای اهداف غیرتجاری\nهرگونه توزیع باید رایگان\nو در دسترس همگان باشد",
        "Polish": "Opracowano w celach niekomercyjnych\nKażda dystrybucja musi być bezpłatna\ni dostępna dla wszystkich",
        "Turkish": "Ticari olmayan amaçlarla geliştirilmiştir\nHer türlü dağıtım ücretsiz\nve herkes için erişilebilir olmalıdır"
    },
    "lbl_creditos": {
        "Portuguese": "Créditos e agradecimentos à comunidade Open Source",
        "English": "Credits and thanks to the Open Source community",
        "Spanish": "Créditos y agradecimentos a la comunidad Open Source",
        "Chinese": "致谢开源社区",
        "Japanese": "オープンソースコミュニティへのクレジットと感謝",
        "Korean": "오픈 소스 커뮤니티에 대한 크레딧 및 감사",
        "Russian": "Благодарности сообществу Open Source",
        "Ukrainian": "Подяки спільноті Open Source",
        "Indonesian": "Kredit dan terima kasih kepada komunitas Open Source",
        "Filipino": "Mga kredito at pasasalamat sa komunidad ng Open Source",
        "Vietnamese": "Ghi nhận và cảm ơn cộng đồng Mã nguồn mở",
        "Norwegian": "Kreditt og takk til Open Source-fellesskapet",
        "Hausa": "Yabo da godiya ga al'ummar Open Source",
        "Bambara": "Tandoli ni foobali Open Source jɛkulu ma",
        "Latin": "Gratiae et laus communitati Open Source",
        "Arabic": "الشكر والتقدير لمجتمع المصادر المفتوحة",
        "Bengali": "ওপেন সোর্স সম্প্রদায়ের প্রতি কৃতজ্ঞতা ও ধন্যবাদ",
        "Dutch": "Credits en dank aan de Open Source-gemeenschap",
        "French": "Crédits et remerciements à la communauté Open Source",
        "German": "Danksagung an die Open-Source-Community",
        "Hindi": "ओपन सोर्स समुदाय को श्रेय और धन्यवाद",
        "Italian": "Ringraziamenti alla comunità Open Source",
        "Persian": "تقدیر و سپاس از جامعه متن‌باز (Open Source)",
        "Polish": "Podziękowania dla społeczności Open Source",
        "Turkish": "Açık Kaynak topluluğuna teşekkürler ve katkılar"
    },
    "link_crimson": {
        "Portuguese": "  Repositório Crimson",
        "English": "  Crimson Repository",
        "Spanish": "  Repositorio Crimson",
        "Chinese": "  Crimson 仓库",
        "Japanese": "  Crimson リポジトリ",
        "Korean": "  Crimson 저장소",
        "Russian": "  Репозиторий Crimson",
        "Ukrainian": "  Репозиторій Crimson",
        "Indonesian": "  Repositori Crimson",
        "Filipino": "  Crimson Repository",
        "Vietnamese": "  Kho lưu trữ Crimson",
        "Norwegian": "  Crimson-depot",
        "Hausa": "  Ma'ajiyar Crimson",
        "Bambara": "  Crimson Marayɔrɔ",
        "Latin": "  Repositorium Crimson",
        "Arabic": "  مستودع Crimson",
        "Bengali": "  Crimson সংগ্রহস্থল",
        "Dutch": "  Crimson-repository",
        "French": "  Dépôt Crimson",
        "German": "  Crimson-Repository",
        "Hindi": "  Crimson रिपॉजिटरी",
        "Italian": "  Repository Crimson",
        "Persian": "  مخزن Crimson",
        "Polish": "  Repozytorium Crimson",
        "Turkish": "  Crimson Deposu"
    },
    "link_ytdlp": {
        "Portuguese": "  Repositório yt-dlp",
        "English": "  yt-dlp Repository",
        "Spanish": "  Repositorio yt-dlp",
        "Chinese": "  yt-dlp 仓库",
        "Japanese": "  yt-dlp リポジトリ",
        "Korean": "  yt-dlp 저장소",
        "Russian": "  Репозиторий yt-dlp",
        "Ukrainian": "  Репозиторій yt-dlp",
        "Indonesian": "  Repositori yt-dlp",
        "Filipino": "  yt-dlp Repository",
        "Vietnamese": "  Kho lưu trữ yt-dlp",
        "Norwegian": "  yt-dlp-depot",
        "Hausa": "  Ma'ajiyar yt-dlp",
        "Bambara": "  yt-dlp Marayɔrɔ",
        "Latin": "  Repositorium yt-dlp",
        "Arabic": "  مستودع yt-dlp",
        "Bengali": "  yt-dlp সংগ্রহস্থল",
        "Dutch": "  yt-dlp-repository",
        "French": "  Dépôt yt-dlp",
        "German": "  yt-dlp-Repository",
        "Hindi": "  yt-dlp रिपॉजिटरी",
        "Italian": "  Repository yt-dlp",
        "Persian": "  مخزن yt-dlp",
        "Polish": "  Repozytorium yt-dlp",
        "Turkish": "  yt-dlp Deposu"
    },
    "link_ffmpeg": {
        "Portuguese": "  Repositório FFmpeg",
        "English": "  FFmpeg Repository",
        "Spanish": "  Repositorio FFmpeg",
        "Chinese": "  FFmpeg 仓库",
        "Japanese": "  FFmpeg リポジトリ",
        "Korean": "  FFmpeg 저장소",
        "Russian": "  Репозиторий FFmpeg",
        "Ukrainian": "  Репозиторій FFmpeg",
        "Indonesian": "  Repositori FFmpeg",
        "Filipino": "  FFmpeg Repository",
        "Vietnamese": "  Kho lưu trữ FFmpeg",
        "Norwegian": "  FFmpeg-depot",
        "Hausa": "  Ma'ajiyar FFmpeg",
        "Bambara": "  FFmpeg Marayɔrɔ",
        "Latin": "  Repositorium FFmpeg",
        "Arabic": "  مستودع FFmpeg",
        "Bengali": "  FFmpeg সংগ্রহস্থল",
        "Dutch": "  FFmpeg-repository",
        "French": "  Dépôt FFmpeg",
        "German": "  FFmpeg-Repository",
        "Hindi": "  FFmpeg रिपॉजिटरी",
        "Italian": "  Repository FFmpeg",
        "Persian": "  مخزن FFmpeg",
        "Polish": "  Repozytorium FFmpeg",
        "Turkish": "  FFmpeg Deposu"
    },
    "plataformas_titulo": {
        "Portuguese": "Plataformas Suportadas",
        "English": "Supported Platforms",
        "Spanish": "Plataformas Compatibles",
        "Chinese": "支持的平台",
        "Japanese": "対応プラットフォーム",
        "Korean": "지원되는 플랫폼",
        "Russian": "Поддерживаемые платформы",
        "Ukrainian": "Підтримувані платформи",
        "Indonesian": "Platform yang Didukung",
        "Filipino": "Mga Suportadong Platform",
        "Vietnamese": "Nền tảng được hỗ trợ",
        "Norwegian": "Støttede plattformer",
        "Hausa": "Dandalin da ake Tallafawa",
        "Bambara": "Dɛmɛbagaw Sigiyɔrɔ",
        "Latin": "Suggesta Fulta",
        "Arabic": "المنصات المدعومة",
        "Bengali": "সমর্থিত প্ল্যাটফর্ম",
        "Dutch": "Ondersteunde platforms",
        "French": "Plateformes prises en charge",
        "German": "Unterstützte Plattformen",
        "Hindi": "समर्थित प्लेटफ़ॉर्म",
        "Italian": "Piattaforme supportate",
        "Persian": "پلتفرم‌های پشتیبانی‌شده",
        "Polish": "Obsługiwane platformy",
        "Turkish": "Desteklenen Platformlar"
    },
    "plataformas_texto": {
        "Portuguese": "  Consultar lista oficial de sites suportados (yt-dlp)",
        "English": "  View official list of supported sites (yt-dlp)",
        "Spanish": "  Consultar lista oficial de sitios compatibles (yt-dlp)",
        "Chinese": "  查看官方支持的网站列表 (yt-dlp)",
        "Japanese": "  対応サイトの公式リストを見る (yt-dlp)",
        "Korean": "  지원되는 사이트 공식 목록 보기 (yt-dlp)",
        "Russian": "  Открыть официальный список поддерживаемых сайтов (yt-dlp)",
        "Ukrainian": "  Переглянути офіційний список підтримуваних сайтів (yt-dlp)",
        "Indonesian": "  Lihat daftar resmi situs yang didukung (yt-dlp)",
        "Filipino": "  Tingnan ang opisyal na listahan ng mga suportadong site (yt-dlp)",
        "Vietnamese": "  Xem danh sách trang web được hỗ trợ chính thức (yt-dlp)",
        "Norwegian": "  Se offisiell liste over støttede nettsteder (yt-dlp)",
        "Hausa": "  Duba jerin shafukan da ake tallafawa a hukumance (yt-dlp)",
        "Bambara": "  Siti dɛmɛnenw قائمة (yt-dlp) lajɛ",
        "Latin": "  Indicem officialem locorum fultorum videre (yt-dlp)",
        "Arabic": "  عرض القائمة الرسمية للمواقع المدعومة (yt-dlp)",
        "Bengali": "  সমর্থিত সাইটের অফিসিয়াল তালিকা দেখুন (yt-dlp)",
        "Dutch": "  Officiële lijst met ondersteunde sites bekijken (yt-dlp)",
        "French": "  Voir la liste officielle des sites pris en charge (yt-dlp)",
        "German": "  Offizielle Liste unterstützter Seiten ansehen (yt-dlp)",
        "Hindi": "  समर्थित साइटों की आधिकारिक सूची देखें (yt-dlp)",
        "Italian": "  Consulta l'elenco ufficiale dei siti supportati (yt-dlp)",
        "Persian": "  مشاهده فهرست رسمی سایت‌های پشتیبانی‌شده (yt-dlp)",
        "Polish": "  Zobacz oficjalną listę obsługiwanych stron (yt-dlp)",
        "Turkish": "  Desteklenen sitelerin resmi listesini görüntüle (yt-dlp)"
    },
    "plataformas_aviso": {
        "Portuguese": "Aviso: O motor yt-dlp possui suporte nativo para centenas de serviços públicos de mídia. O usuário é integralmente responsável por respeitar os termos de uso e os direitos autorais de cada conteúdo.",
        "English": "Notice: The yt-dlp engine natively supports hundreds of public media services. The user is solely responsible for respecting the terms of use and copyright laws of each content.",
        "Spanish": "Aviso: El motor yt-dlp admite de forma nativa cientos de servicios públicos de medios. El usuario es totalmente responsable de respetar los términos de uso y los derechos de autor de cada contenido.",
        "Chinese": "提示：yt-dlp 引擎原生支持数百个公共媒体服务。用户需自行负责遵守各项内容的使用条款与版权法规。",
        "Japanese": "注意: yt-dlp エンジンは多数の公開メディアサービスをネイティブにサポートしています。各コンテンツの利用規約および著作権法の遵守はユーザー自身の責任となります。",
        "Korean": "알림: yt-dlp 엔진은 수백 개의 공개 미디어 서비스를 기본적으로 지원합니다. 각 콘텐츠의 이용 약관 및 저작권법을 준수할 책임은 전적으로 사용자에게 있습니다.",
        "Russian": "Примечание: Движок yt-dlp поддерживает сотни публичных медиасервисов. Пользователь несет полную ответственность за соблюдение условий использования и авторских прав.",
        "Ukrainian": "Примітка: Двигун yt-dlp підтримує сотні публічних медіасервісів. Користувач несе повну відповідальність за дотримання умов використання та авторських прав.",
        "Indonesian": "Pemberitahuan: Mesin yt-dlp mendukung ratusan layanan media publik secara bawaan. Pengguna sepenuhnya bertanggung jawab untuk mematuhi ketentuan layanan dan hak cipta setiap konten.",
        "Filipino": "Paunawa: Katutubong sinusuportahan ng yt-dlp engine ang daan-daang pampublikong serbisyo ng media. Ang user ay may buong responsibilidad sa pagsunod sa mga tuntunin ng paggamit at karapatang-ari.",
        "Vietnamese": "Lưu ý: Công cụ yt-dlp hỗ trợ hàng trăm dịch vụ truyền thông công cộng. Người dùng hoàn toàn chịu trách nhiệm tuân thủ điều khoản sử dụng và bản quyền của từng nội dung.",
        "Norwegian": "Merk: yt-dlp-motoren støtter hundrevis av offentlige medietjenester. Brukeren er selv ansvarlig for å overholde bruksvilkår og opphavsrett for alt innhold.",
        "Hausa": "Sanarwa: Injin yt-dlp yana tallafawa daruruwan shafukan kafofin watsa labarai. Mai amfani yana da cikakken alhakin bin dokokin amfani da haƙƙin mallaka na kowane abun ciki.",
        "Bambara": "Kɔlɔsili: yt-dlp masini bɛ dɛmɛ di siti caman ma. Baarakɛla yɛrɛ de bɛ sariyaw ani josariyaw labato.",
        "Latin": "Monitum: Instrumentum yt-dlp multa loca publica mediorum indigenice sustinet. Usor ipse tenetur leges usus et iura auctoris cuiusque operis observare.",
        "Arabic": "تنبيه: يدعم محرك yt-dlp مئات خدمات الوسائط العامة بشكل أصلي.يتحمل المستخدم وحده مسؤولية احترام شروط الاستخدام وحقوق النشر الخاصة بكل محتوى.",
        "Bengali": "সতর্কতা: yt-dlp ইঞ্জিন শত শত পাবলিক মিডিয়া পরিষেবা সমর্থন করে। প্রতিটি কন্টেন্টের ব্যবহারের শর্তাবলী এবং কপিরাইট আইন মেনে চলার সম্পূর্ণ দায়িত্ব ব্যবহারকারীর।",
        "Dutch": "Opmerking: De yt-dlp-engine ondersteunt honderden openbare mediadiensten. De gebruiker is zelf verantwoordelijk voor het naleven van de gebruiksvoorwaarden en auteursrechten.",
        "French": "Remarque : Le moteur yt-dlp prend en charge des centaines de services médias publics. L'utilisateur est seul responsable du respect des conditions d'utilisation et des droits d'auteur.",
        "German": "Hinweis: Die yt-dlp-Engine unterstützt hunderte öffentliche Mediendienste nativ. Der Nutzer ist allein dafür verantwortlich, Nutzungsbedingungen und Urheberrechte einzuhalten.",
        "Hindi": "सूचना: yt-dlp इंजन सैकड़ों सार्वजनिक मीडिया सेवाओं का मूल रूप से समर्थन करता है। प्रत्येक सामग्री की उपयोग की शर्तों और कॉपीराइट कानूनों का पालन करने की पूरी जिम्मेदारी उपयोगकर्ता की है।",
        "Italian": "Avviso: Il motore yt-dlp supporta nativamente centinaia di servizi multimediali pubblici. L'utente è pienamente responsabile del rispetto dei termini di utilizzo e del diritto d'autore.",
        "Persian": "توجه: موتور yt-dlp به‌طور پیش‌فرض از صدها سرویس رسانه عمومی پشتیبانی می‌کند .مسئولیت رعایت شرایط استفاده و قوانین حق نشر هر محتوا کاملاً بر عهده کاربر است.",
        "Polish": "Uwaga: Silnik yt-dlp natywnie obsługuje setki publicznych serwisów multimedialnych. Użytkownik ponosi pełną odpowiedzialność za przestrzeganie warunków korzystania i praw autorskich.",
        "Turkish": "Uyarı: yt-dlp motoru yüzlerce genel medya hizmetini yerel olarak destekler. Her içeriğin kullanım koşullarına ve telif hakkı yasalarına uymak tamamen kullanıcının sorumluluğundadır."
    },
    "marca_dagua": {
        "Portuguese": "Desenvolvido por LuanDevCodes",
        "English": "Developed by LuanDevCodes",
        "Spanish": "Desarrollado por LuanDevCodes",
        "Chinese": "由 LuanDevCodes 开发",
        "Japanese": "開発者: LuanDevCodes",
        "Korean": "개발자: LuanDevCodes",
        "Russian": "Разработчик: LuanDevCodes",
        "Ukrainian": "Розробник: LuanDevCodes",
        "Indonesian": "Dikembangkan oleh LuanDevCodes",
        "Filipino": "Binuo ni LuanDevCodes",
        "Vietnamese": "Phát triển bởi LuanDevCodes",
        "Norwegian": "Utviklet av LuanDevCodes",
        "Hausa": "LuanDevCodes ne ya ƙirƙira",
        "Bambara": "LuanDevCodes le y'a dabɔ",
        "Latin": "A LuanDevCodes elaboratum",
        "Arabic": "تم التطوير بواسطة LuanDevCodes",
        "Bengali": "LuanDevCodes দ্বারা তৈরি",
        "Dutch": "Ontwikkeld door LuanDevCodes",
        "French": "Développé par LuanDevCodes",
        "German": "Entwickelt von LuanDevCodes",
        "Hindi": "LuanDevCodes द्वारा विकसित",
        "Italian": "Sviluppato da LuanDevCodes",
        "Persian": "توسعه‌یافته توسط LuanDevCodes",
        "Polish": "Opracowane przez LuanDevCodes",
        "Turkish": "LuanDevCodes tarafından geliştirildi"
    },
    "msg_sucesso_titulo": {
        "Portuguese": "Sucesso",
        "English": "Success",
        "Spanish": "Éxito",
        "Chinese": "成功",
        "Japanese": "成功",
        "Korean": "성공",
        "Russian": "Успешно",
        "Ukrainian": "Успішно",
        "Indonesian": "Berhasil",
        "Filipino": "Tagumpay",
        "Vietnamese": "Thành công",
        "Norwegian": "Suksess",
        "Hausa": "Nasarar Aiki",
        "Bambara": "Ɲɛtaa",
        "Latin": "Feliciter",
        "Arabic": "نجاح",
        "Bengali": "সফল",
        "Dutch": "Succes",
        "French": "Succès",
        "German": "Erfolg",
        "Hindi": "सफलता",
        "Italian": "Successo",
        "Persian": "موفقیت",
        "Polish": "Sukces",
        "Turkish": "Başarılı"
    },
    "msg_sucesso_texto": {
        "Portuguese": "Download e conversão concluídos com sucesso",
        "English": "Download and conversion completed successfully",
        "Spanish": "Descarga y conversión completadas con éxito",
        "Chinese": "下载和转换已成功完成",
        "Japanese": "ダウンロードと変換が正常に完了しました",
        "Korean": "다운로드 및 변환이 성공적으로 완료되었습니다",
        "Russian": "Скачивание и конвертация успешно завершены",
        "Ukrainian": "Завантаження та конвертацію успішно завершено",
        "Indonesian": "Pengunduhan dan konversi selesai dengan sukses",
        "Filipino": "Matagumpay na natapos ang pag-download at conversion",
        "Vietnamese": "Tải xuống và chuyển đổi thành công",
        "Norwegian": "Nedlasting og konvertering fullført",
        "Hausa": "An kammala zazzagewa da sauyawa cikin nasara",
        "Bambara": "Ladonni ani yɛlɛmali dafara ka ɲa",
        "Latin": "Deportatio atque conversio feliciter perfecta est",
        "Arabic": "تم التنزيل والتحويل بنجاح",
        "Bengali": "ডাউনলোড এবং রূপান্তর সফলভাবে সম্পন্ন হয়েছে",
        "Dutch": "Downloaden en converteren succesvol voltooid",
        "French": "Téléchargement et conversion terminés avec succès",
        "German": "Download und Konvertierung erfolgreich abgeschlossen",
        "Hindi": "डाउनलोड और रूपांतरण सफलतापूर्वक पूरा हुआ",
        "Italian": "Download e conversione completati con successo",
        "Persian": "دانلود و تبدیل با موفقیت انجام شد",
        "Polish": "Pobieranie i konwersja zakończone pomyślnie",
        "Turkish": "İndirme ve dönüştürme başarıyla tamamlandı"
    },
    "msg_erro_titulo": {
        "Portuguese": "Erro",
        "English": "Error",
        "Spanish": "Error",
        "Chinese": "错误",
        "Japanese": "エラー",
        "Korean": "오류",
        "Russian": "Ошибка",
        "Ukrainian": "Помилка",
        "Indonesian": "Kesalahan",
        "Filipino": "Error",
        "Vietnamese": "Lỗi",
        "Norwegian": "Feil",
        "Hausa": "Kuskure",
        "Bambara": "Fili",
        "Latin": "Error",
        "Arabic": "خطأ",
        "Bengali": "ত্রুটি",
        "Dutch": "Fout",
        "French": "Erreur",
        "German": "Fehler",
        "Hindi": "त्रुटि",
        "Italian": "Errore",
        "Persian": "خطا",
        "Polish": "Błąd",
        "Turkish": "Hata"
    },
    "msg_erro_generico": {
        "Portuguese": "Ocorreu um erro durante o download:\n",
        "English": "An error occurred during the download:\n",
        "Spanish": "Ocurrió un error durante la descarga:\n",
        "Chinese": "下载时发生错误：\n",
        "Japanese": "ダウンロード中にエラーが発生しました:\n",
        "Korean": "다운로드 중 오류가 발생했습니다:\n",
        "Russian": "Произошла ошибка при скачивании:\n",
        "Ukrainian": "Під час завантаження сталася помилка:\n",
        "Indonesian": "Terjadi kesalahan saat mengunduh:\n",
        "Filipino": "May naganap na error habang nagda-download:\n",
        "Vietnamese": "Đã xảy ra lỗi trong quá trình tải xuống:\n",
        "Norwegian": "Det oppstod en feil under nedlastingen:\n",
        "Hausa": "An sami kuskure yayin zazzagewa:\n",
        "Bambara": "Fili dɔ kɛra ladonni wagati:\n",
        "Latin": "Error quidam in deponendo accidit:\n",
        "Arabic": "حدث خطأ أثناء التنزيل:\n",
        "Bengali": "ডাউনলোড করার সময় একটি ত্রুটি ঘটেছে:\n",
        "Dutch": "Er is een fout opgetreden tijdens het downloaden:\n",
        "French": "Une erreur est survenue lors du téléchargement :\n",
        "German": "Beim Download ist ein Fehler aufgetreten:\n",
        "Hindi": "डाउनलोड के दौरान एक त्रुटि हुई:\n",
        "Italian": "Si è verificato un errore durante il download:\n",
        "Persian": "هنگام دانلود خطایی رخ داد:\n",
        "Polish": "Wystąpił błąd podczas pobierania:\n",
        "Turkish": "İndirme sırasında bir hata oluştu:\n"
    },
    "msg_aviso_titulo": {
        "Portuguese": "Aviso",
        "English": "Warning",
        "Spanish": "Aviso",
        "Chinese": "警告",
        "Japanese": "警告",
        "Korean": "경고",
        "Russian": "Внимание",
        "Ukrainian": "Увага",
        "Indonesian": "Peringatan",
        "Filipino": "Babala",
        "Vietnamese": "Cảnh báo",
        "Norwegian": "Advarsel",
        "Hausa": "Gargaɗi",
        "Bambara": "Kɔlɔsili",
        "Latin": "Monitum",
        "Arabic": "تنبيه",
        "Bengali": "সতর্কতা",
        "Dutch": "Waarschuwing",
        "French": "Avertissement",
        "German": "Warnung",
        "Hindi": "चेतावनी",
        "Italian": "Avviso",
        "Persian": "هشدار",
        "Polish": "Ostrzeżenie",
        "Turkish": "Uyarı"
    },
    "msg_aviso_url": {
        "Portuguese": "Por favor, insira uma URL válida",
        "English": "Please enter a valid URL",
        "Spanish": "Por favor, introduce una URL válida",
        "Chinese": "请输入有效的链接",
        "Japanese": "有効なURLを入力してください",
        "Korean": "유효한 URL을 입력해 주세요",
        "Russian": "Пожалуйста, введите корректный URL-адрес",
        "Ukrainian": "Будь ласка, введіть дійсну URL-адресу",
        "Indonesian": "Harap masukkan URL yang valid",
        "Filipino": "Mangyaring maglagay ng wastong URL",
        "Vietnamese": "Vui lòng nhập URL hợp lệ",
        "Norwegian": "Vennligst oppgi en gyldig URL",
        "Hausa": "Da fatan za a shigar da ingantaccen URL",
        "Bambara": "URL bɛrɛbɛn bila yan foyi tɛ",
        "Latin": "Quaesumus, validam inscriptionem (URL) insere",
        "Arabic": "يرجى إدخال رابط صالح",
        "Bengali": "দয়া করে একটি বৈধ URL লিখুন",
        "Dutch": "Voer een geldige URL in",
        "French": "Veuillez entrer une URL valide",
        "German": "Bitte geben Sie eine gültige URL ein",
        "Hindi": "कृपया एक मान्य URL दर्ज करें",
        "Italian": "Inserisci un URL valido",
        "Persian": "لطفاً یک نشانی اینترنتی (URL) معتبر وارد کنید",
        "Polish": "Proszę wprowadzić prawidłowy adres URL",
        "Turkish": "Lütfen geçerli bir URL girin"
    },
    "progresso_baixando": {
        "Portuguese": "Baixando",
        "English": "Downloading",
        "Spanish": "Descargando",
        "Chinese": "下载中",
        "Japanese": "ダウンロード中",
        "Korean": "다운로드 중",
        "Russian": "Скачивание",
        "Ukrainian": "Завантаження",
        "Indonesian": "Mengunduh",
        "Filipino": "Nagda-download",
        "Vietnamese": "Đang tải xuống",
        "Norwegian": "Laster ned",
        "Hausa": "Ana zazzagewa",
        "Bambara": "Ladonni bɛ kɛ",
        "Latin": "Depromens",
        "Arabic": "جارٍ التنزيل",
        "Bengali": "ডাউনলোড হচ্ছে",
        "Dutch": "Downloaden",
        "French": "Téléchargement",
        "German": "Herunterladen",
        "Hindi": "डाउनलोड हो रहा है",
        "Italian": "Download in corso",
        "Persian": "در حال دانلود",
        "Polish": "Pobieranie",
        "Turkish": "İndiriliyor"
    },
    "progresso_vel": {
        "Portuguese": "Velocidade",
        "English": "Speed",
        "Spanish": "Velocidad",
        "Chinese": "速度",
        "Japanese": "速度",
        "Korean": "속도",
        "Russian": "Скорость",
        "Ukrainian": "Швидкість",
        "Indonesian": "Kecepatan",
        "Filipino": "Bilis",
        "Vietnamese": "Tốc độ",
        "Norwegian": "Hastighet",
        "Hausa": "Gudun Aiki",
        "Bambara": "Teliya",
        "Latin": "Velocitas",
        "Arabic": "السرعة",
        "Bengali": "গতি",
        "Dutch": "Snelheid",
        "French": "Vitesse",
        "German": "Geschwindigkeit",
        "Hindi": "गति",
        "Italian": "Velocità",
        "Persian": "سرعت",
        "Polish": "Prędkość",
        "Turkish": "Hız"
    },
    "progresso_tempo": {
        "Portuguese": "Tempo Restante",
        "English": "ETA",
        "Spanish": "Tiempo restante",
        "Chinese": "剩余时间",
        "Japanese": "残り時間",
        "Korean": "남은 시간",
        "Russian": "Осталось времени",
        "Ukrainian": "Залишилося часу",
        "Indonesian": "Sisa Waktu",
        "Filipino": "Natitirang Oras",
        "Vietnamese": "Thời gian còn lại",
        "Norwegian": "Gjenværende tid",
        "Hausa": "Lokacin da ya rage",
        "Bambara": "Tuma Tolen",
        "Latin": "Tempus residuum",
        "Arabic": "الوقت المتبقي",
        "Bengali": "বাকি সময়",
        "Dutch": "Resterende tijd",
        "French": "Temps restant",
        "German": "Verbleibende Zeit",
        "Hindi": "शेष समय",
        "Italian": "Tempo rimanente",
        "Persian": "زمان باقی‌مانده",
        "Polish": "Pozostały czas",
        "Turkish": "Kalan Süre"
    },
    "progresso_init": {
        "Portuguese": "Iniciando Download...",
        "English": "Starting Download...",
        "Spanish": "Iniciando descarga...",
        "Chinese": "正在启动下载...",
        "Japanese": "ダウンロード開始中...",
        "Korean": "다운로드 시작 중...",
        "Russian": "Запуск скачивания...",
        "Ukrainian": "Початок завантаження...",
        "Indonesian": "Memulai Pengunduhan...",
        "Filipino": "Sinisimulan ang Pag-download...",
        "Vietnamese": "Bắt đầu tải xuống...",
        "Norwegian": "Starter nedlasting...",
        "Hausa": "Ana fara zazzagewa...",
        "Bambara": "Ladonni daminɛna...",
        "Latin": "Deportatio incipitur...",
        "Arabic": "بدء التنزيل...",
        "Bengali": "ডাউনলোড শুরু হচ্ছে...",
        "Dutch": "Download starten...",
        "French": "Démarrage du téléchargement...",
        "German": "Download wird gestartet...",
        "Hindi": "डाउनलोड प्रारंभ हो रहा है...",
        "Italian": "Avvio del download...",
        "Persian": "شروع دانلود...",
        "Polish": "Rozpoczynanie pobierania...",
        "Turkish": "İndirme başlatılıyor..."
    },
    "progresso_convertendo": {
        "Portuguese": "Baixado - Aguarde a conversão (FFmpeg)...",
        "English": "Downloaded - Please wait for conversion (FFmpeg)...",
        "Spanish": "Descargado - Espere la conversión (FFmpeg)...",
        "Chinese": "已下载 - 请等待转换 (FFmpeg)...",
        "Japanese": "完了 - 変換をお待ちください (FFmpeg)...",
        "Korean": "다운로드 완료 - 변환 대기 중 (FFmpeg)...",
        "Russian": "Скачано - Ожидайте конвертации (FFmpeg)...",
        "Ukrainian": "Завантажено - Очікуйте конвертації (FFmpeg)...",
        "Indonesian": "Terunduh - Menunggu konversi (FFmpeg)...",
        "Filipino": "Na-download na - Naghihintay sa conversion (FFmpeg)...",
        "Vietnamese": "Đã tải xong - Vui lòng chờ chuyển đổi (FFmpeg)...",
        "Norwegian": "Nedlastet - Vennligst vent på konvertering (FFmpeg)...",
        "Hausa": "An zazzage - Da fatan a jira sauyawa (FFmpeg)...",
        "Bambara": "A ladonna - Makɔnɔ k'a yɛlɛma (FFmpeg)...",
        "Latin": "Depromptum - Conversio exspectatur (FFmpeg)...",
        "Arabic": "تم التنزيل - يرجى انتظار التحويل (FFmpeg)...",
        "Bengali": "ডাউনলোড সম্পন্ন - রূপান্তরের জন্য অপেক্ষা করুন (FFmpeg)...",
        "Dutch": "Gedownload - Wachten op conversie (FFmpeg)...",
        "French": "Téléchargé - Veuillez attendre la conversion (FFmpeg)...",
        "German": "Heruntergeladen - Bitte auf Konvertierung warten (FFmpeg)...",
        "Hindi": "डाउनलोड हो गया - रूपांतरण की प्रतीक्षा करें (FFmpeg)...",
        "Italian": "Scaricato - Attendi la conversione (FFmpeg)...",
        "Persian": "دانلود شد - لطفاً منتظر تبدیل بمانید (FFmpeg)...",
        "Polish": "Pobrano - Proszę czekać na konwersję (FFmpeg)...",
        "Turkish": "İndirildi - Dönüştürme bekleniyor (FFmpeg)..."
    },
    "btn_baixar_inativo": {
        "Portuguese": "Preparando...",
        "English": "Preparing...",
        "Spanish": "Preparando...",
        "Chinese": "准备中...",
        "Japanese": "準備中...",
        "Korean": "준비 중...",
        "Russian": "Подготовка...",
        "Ukrainian": "Підготовка...",
        "Indonesian": "Menyiapkan...",
        "Filipino": "Naghahanda...",
        "Vietnamese": "Đang chuẩn bị...",
        "Norwegian": "Forbereder...",
        "Hausa": "Ana shiryawa...",
        "Bambara": "Labɛn bɛ kɛ...",
        "Latin": "Parans...",
        "Arabic": "جارٍ التحضير...",
        "Bengali": "প্রস্তুত হচ্ছে...",
        "Dutch": "Voorbereiden...",
        "French": "Préparation...",
        "German": "Vorbereitung...",
        "Hindi": "तैयार हो रहा है...",
        "Italian": "Preparazione...",
        "Persian": "در حال آماده‌سازی...",
        "Polish": "Przygotowywanie...",
        "Turkish": "Hazırlanıyor..."
    },
    "msg_excluir_titulo": {
        "Portuguese": "Excluir Download",
        "English": "Delete Download",
        "Spanish": "Eliminar Descarga",
        "Chinese": "删除下载",
        "Japanese": "ダウンロードを削除",
        "Korean": "다운로드 삭제",
        "Russian": "Удалить загрузку",
        "Ukrainian": "Видалити завантаження",
        "Indonesian": "Hapus Unduhan",
        "Filipino": "Tanggalin ang Pag-download",
        "Vietnamese": "Xóa lượt tải",
        "Norwegian": "Slett nedlasting",
        "Hausa": "Share Zazzagewa",
        "Bambara": "Ladonni bosi",
        "Latin": "Deportationem Delere",
        "Arabic": "حذف التنزيل",
        "Bengali": "ডাউনলোড মুছুন",
        "Dutch": "Download Verwijderen",
        "French": "Supprimer le téléchargement",
        "German": "Download löschen",
        "Hindi": "डाउनलोड हटाएं",
        "Italian": "Elimina Download",
        "Persian": "حذف دانلود",
        "Polish": "Usuń pobieranie",
        "Turkish": "İndirmeyi Sil"
    },
    "msg_excluir_texto": {
        "Portuguese": "Tem certeza que deseja cancelar e excluir o progresso desse download?",
        "English": "Are you sure you want to cancel and delete the progress of this download?",
        "Spanish": "¿Está seguro de que desea cancelar y eliminar el progreso de esta descarga?",
        "Chinese": "确定要取消并删除此下载的进度吗？",
        "Japanese": "ダウンロードをキャンセルして進捗を削除しますか？",
        "Korean": "다운로드를 취소하고 진행 상황을 삭제하시겠습니까?",
        "Russian": "Вы уверены, что хотите отменить и удалить эту загрузку?",
        "Ukrainian": "Ви впевнені, що хочете скасувати та видалити це завантаження?",
        "Indonesian": "Apakah Anda yakin ingin membatalkan dan menghapus progres unduhan ini?",
        "Filipino": "Sigurado ka bang gusto mong kanselahin at tanggalin ang pag-unlad ng pag-download na ito?",
        "Vietnamese": "Bạn có chắc chắn muốn hủy và xóa tiến trình tải này không?",
        "Norwegian": "Er du sikker på at du vil avbryte og slette fremdriften for denne nedlastingen?",
        "Hausa": "Kun tabbata kuna son soke tare da share wannan zazzagewar?",
        "Bambara": "I dalen b'a la ko i b'a fɛ ka ladonni in bali k'a bosi wa?",
        "Latin": "Certusne es te velle hanc deportationem abrumpere ac delere?",
        "Arabic": "هل أنت متأكد من رغبتك في إلغاء وحذف تقدم هذا التنزيل؟",
        "Bengali": "আপনি কি নিশ্চিত যে আপনি এই ডাউনলোডের অগ্রগতি বাতিল এবং মুছে ফেলতে চান?",
        "Dutch": "Weet u zeker dat u de voortgang van deze download wilt annuleren en verwijderen?",
        "French": "Êtes-vous sûr de vouloir annuler et supprimer la progression de ce téléchargement ?",
        "German": "Sind Sie sicher, dass Sie diesen Download abbrechen und löschen möchten?",
        "Hindi": "क्या आप वाकई इस डाउनलोड की प्रगति को रद्द और हटाना चाहते हैं?",
        "Italian": "Sei sicuro di voler annullare ed eliminare lo stato di questo download?",
        "Persian": "آیا مطمئن هستید که می‌خواهید پیشرفت این دانلود را لغو کرده و حذف کنید؟",
        "Polish": "Czy na pewno chcesz anulować i usunąć postęp tego pobierania?",
        "Turkish": "Bu indirmenin ilerlemesini iptal etmek ve silmek istediğinizden emin misiniz?"
    },
    "msg_salvar_como": {
        "Portuguese": "Salvar como...",
        "English": "Save as...",
        "Spanish": "Guardar como...",
        "Chinese": "另存为...",
        "Japanese": "名前を付けて保存...",
        "Korean": "다른 이름으로 저장...",
        "Russian": "Сохранить как...",
        "Ukrainian": "Зберегти як...",
        "Indonesian": "Simpan sebagai...",
        "Filipino": "I-save bilang...",
        "Vietnamese": "Lưu dưới dạng...",
        "Norwegian": "Lagre som...",
        "Hausa": "Ajiye a matsayin...",
        "Bambara": "Mara i n'a fɔ...",
        "Latin": "Servare sub nomine...",
        "Arabic": "حفظ باسم...",
        "Bengali": "হিসাবে সংরক্ষণ করুন...",
        "Dutch": "Opslaan als...",
        "French": "Enregistrer sous...",
        "German": "Speichern unter...",
        "Hindi": "इस रूप में सहेजें...",
        "Italian": "Salva con nome...",
        "Persian": "ذخیره به عنوان...",
        "Polish": "Zapisz jako...",
        "Turkish": "Farklı kaydet..."
    },
    "menu_colar": {
        "Portuguese": "Colar",
        "English": "Paste",
        "Spanish": "Pegar",
        "Chinese": "粘贴",
        "Japanese": "貼り付け",
        "Korean": "붙여넣기",
        "Russian": "Вставить",
        "Ukrainian": "Вставити",
        "Indonesian": "Tempel",
        "Filipino": "I-paste",
        "Vietnamese": "Dán",
        "Norwegian": "Lim inn",
        "Hausa": "Manna",
        "Bambara": "Nɔrɔ",
        "Latin": "Glutinare",
        "Arabic": "لصق",
        "Bengali": "পেস্ট করুন",
        "Dutch": "Plakken",
        "French": "Coller",
        "German": "Einfügen",
        "Hindi": "चिपकाएँ",
        "Italian": "Incolla",
        "Persian": "چسباندن",
        "Polish": "Wklej",
        "Turkish": "Yapıştır"
    },
    "menu_apagar": {
        "Portuguese": "Apagar",
        "English": "Delete",
        "Spanish": "Borrar",
        "Chinese": "删除",
        "Japanese": "消去",
        "Korean": "지우기",
        "Russian": "Очистить",
        "Ukrainian": "Очистити",
        "Indonesian": "Hapus",
        "Filipino": "Burahin",
        "Vietnamese": "Xóa",
        "Norwegian": "Slett",
        "Hausa": "Goge",
        "Bambara": "Bosi",
        "Latin": "Delere",
        "Arabic": "مسح",
        "Bengali": "মুছুন",
        "Dutch": "Wissen",
        "French": "Effacer",
        "German": "Löschen",
        "Hindi": "मिटाएँ",
        "Italian": "Cancella",
        "Persian": "پاک کردن",
        "Polish": "Wyczyść",
        "Turkish": "Temizle"
    },
    "btn_limpar_processos": {
        "Portuguese": "Finalizar processos fantasmas",
        "English": "Kill ghost processes",
        "Spanish": "Finalizar procesos fantasma",
        "Chinese": "结束幽灵进程",
        "Japanese": "ゴーストプロセスを終了",
        "Korean": "유령 프로세스 종료",
        "Russian": "Завершить фоновые процессы",
        "Ukrainian": "Завершити фонові процеси",
        "Indonesian": "Hentikan proses latar belakang",
        "Filipino": "Tapusin ang mga ghost process",
        "Vietnamese": "Dọn dẹp tiến trình chạy ngầm",
        "Norwegian": "Avslutt spøkelsesprosesser",
        "Hausa": "Kawar da ɓoyayyun ayyukan baya",
        "Bambara": "Baara dogolenw datugu",
        "Latin": "Processus umbraticos delere",
        "Arabic": "إنهاء العمليات الخلفية الشبحية",
        "Bengali": "অপ্রয়োজনীয় ব্যাকগ্রাউন্ড প্রক্রিয়া বন্ধ করুন",
        "Dutch": "Spookprocessen beëindigen",
        "French": "Terminer les processus fantômes",
        "German": "Geisterprozesse beenden",
        "Hindi": "अनावश्यक बैकग्राउंड प्रक्रियाएं समाप्त करें",
        "Italian": "Termina processi fantasma",
        "Persian": "بستن فرآیندهای پس‌زمینه معلق",
        "Polish": "Zakończ procesy w tle",
        "Turkish": "Askıdaki arka plan süreçlerini sonlandır"
    },
    "msg_confirm_limpeza_titulo": {
        "Portuguese": "Limpeza de Processos",
        "English": "Process Cleanup",
        "Spanish": "Limpieza de Procesos",
        "Chinese": "进程清理",
        "Japanese": "プロセスのクリーンアップ",
        "Korean": "프로세스 정리",
        "Russian": "Очистка процессов",
        "Ukrainian": "Очищення процесів",
        "Indonesian": "Pembersihan Proses",
        "Filipino": "Paglilinis ng Proseso",
        "Vietnamese": "Dọn dẹp tiến trình",
        "Norwegian": "Prosessrensing",
        "Hausa": "Share Ayyukan Baya",
        "Bambara": "Baara Saniyali",
        "Latin": "Processuum Purgatio",
        "Arabic": "تنظيف العمليات",
        "Bengali": "প্রক্রিয়া পরিষ্কার",
        "Dutch": "Processen Opschonen",
        "French": "Nettoyage des processus",
        "German": "Prozessbereinigung",
        "Hindi": "प्रक्रिया सफाई",
        "Italian": "Pulizia Processi",
        "Persian": "پاک‌سازی فرآیندها",
        "Polish": "Czyszczenie procesów",
        "Turkish": "Süreç Temizleme"
    },
    "msg_confirm_limpeza_texto": {
        "Portuguese": "Tem certeza que deseja finalizar os processos em segundo plano da aplicação?",
        "English": "Are you sure you want to terminate background application processes?",
        "Spanish": "¿Está seguro de que desea finalizar los procesos en segundo plano de la aplicación?",
        "Chinese": "确定要终止应用程序的后台进程吗？",
        "Japanese": "アプリのバックグラウンドプロセスを終了しますか？",
        "Korean": "애플리케이션 백그라운드 프로세스를 종료하시겠습니까?",
        "Russian": "Вы уверены, что хотите завершить фоновые процессы приложения?",
        "Ukrainian": "Ви впевнені, що хочете завершити фонові процеси програми?",
        "Indonesian": "Apakah Anda yakin ingin menghentikan proses latar belakang aplikasi?",
        "Filipino": "Sigurado ka bang gusto mong tapusin ang mga background process ng application?",
        "Vietnamese": "Bạn có chắc chắn muốn kết thúc các tiến trình nền của ứng dụng không?",
        "Norwegian": "Er du sikker på at du vil avslutte bakgrunnsprosessene til applikasjonen?",
        "Hausa": "Kun tabbata kuna son dakatar da ayyukan bayan fage na manhaja?",
        "Bambara": "I dalen b'a la ko i b'a fɛ ka kɔfɛ baara kɛbagaw datugu wa?",
        "Latin": "Certusne es te velle processus posticos applicationis finire?",
        "Arabic": "هل أنت متأكد من رغبتك في إنهاء العمليات الخلفية للتطبيق؟",
        "Bengali": "আপনি কি নিশ্চিত যে আপনি অ্যাপ্লিকেশনের ব্যাকগ্রাউন্ড প্রক্রিয়াগুলি বন্ধ করতে চান?",
        "Dutch": "Weet u zeker dat u de achtergrondprocessen van de applicatie wilt beëindigen?",
        "French": "Êtes-vous sûr de vouloir terminer les processus en arrière-plan de l'application ?",
        "German": "Sind Sie sicher, dass Sie die Hintergrundprozesse der Anwendung beenden möchten?",
        "Hindi": "क्या आप वाकई एप्लिकेशन की बैकग्राउंड प्रक्रियाओं को समाप्त करना चाहते हैं?",
        "Italian": "Sei sicuro di voler terminare i processi in background dell'applicazione?",
        "Persian": "آیا مطمئن هستید که می‌خواهید فرآیندهای پس‌زمینه برنامه را ببندید؟",
        "Polish": "Czy na pewno chcesz zakończyć procesy aplikacji działające w tle?",
        "Turkish": "Uygulamanın arka plan süreçlerini sonlandırmak istediğinizden emin misiniz?"
    },
    "msg_sucesso_limpeza_titulo": {
        "Portuguese": "Sucesso",
        "English": "Success",
        "Spanish": "Éxito",
        "Chinese": "成功",
        "Japanese": "成功",
        "Korean": "성공",
        "Russian": "Успешно",
        "Ukrainian": "Успішно",
        "Indonesian": "Berhasil",
        "Filipino": "Tagumpay",
        "Vietnamese": "Thành công",
        "Norwegian": "Suksess",
        "Hausa": "Nasarar Aiki",
        "Bambara": "Ɲɛtaa",
        "Latin": "Feliciter",
        "Arabic": "نجاح",
        "Bengali": "সফল",
        "Dutch": "Succes",
        "French": "Succès",
        "German": "Erfolg",
        "Hindi": "सफलता",
        "Italian": "Successo",
        "Persian": "موفقیت",
        "Polish": "Sukces",
        "Turkish": "Başarılı"
    },
    "msg_sucesso_limpeza_texto": {
        "Portuguese": "Processos secundários finalizados",
        "English": "Secondary processes terminated",
        "Spanish": "Procesos secundarios finalizados",
        "Chinese": "后台进程已终止",
        "Japanese": "バックグラウンドプロセスを終了しました",
        "Korean": "보조 프로세스가 종료되었습니다",
        "Russian": "Вторичные процессы успешно завершены",
        "Ukrainian": "Вторинні процеси завершено",
        "Indonesian": "Proses latar belakang dihentikan",
        "Filipino": "Matagumpay na natapos ang mga pangalawang proseso",
        "Vietnamese": "Các tiến trình phụ đã được kết thúc",
        "Norwegian": "Sekundære prosesser avsluttet",
        "Hausa": "An dakatar da ayyukan bayan fage cikin nasara",
        "Bambara": "Kɔfɛ baara kɛbagaw datugula",
        "Latin": "Processus posteriores finiti sunt",
        "Arabic": "تم إنهاء العمليات الثانوية",
        "Bengali": "গৌণ প্রক্রিয়াগুলি বন্ধ করা হয়েছে",
        "Dutch": "Secundaire processen beëindigd",
        "French": "Processus secondaires terminés",
        "German": "Sekundäre Prozesse beendet",
        "Hindi": "द्वितीयक प्रक्रियाएं समाप्त हो गईं",
        "Italian": "Processi secondari terminati",
        "Persian": "فرآیندهای فرعی پایان یافتند",
        "Polish": "Procesy drugorzędne zostały zakończone",
        "Turkish": "İkincil süreçler sonlandırıldı"
    },
    "btn_salvar_config": {
        "Portuguese": "Salvar e Aplicar",
        "English": "Save and Apply",
        "Spanish": "Guardar y Aplicar",
        "Chinese": "保存并应用",
        "Japanese": "保存して適用",
        "Korean": "저장 및 적용",
        "Russian": "Сохранить и применить",
        "Ukrainian": "Зберегти та застосувати",
        "Indonesian": "Simpan dan Terapkan",
        "Filipino": "I-save at Ilapat",
        "Vietnamese": "Lưu và Áp dụng",
        "Norwegian": "Lagre og bruk",
        "Hausa": "Ajiye kuma Aiwatar",
        "Bambara": "A mara k'a labaara",
        "Latin": "Servare et Adhibere",
        "Arabic": "حفظ وتطبيق",
        "Bengali": "সংরক্ষণ ও প্রয়োগ করুন",
        "Dutch": "Opslaan en Toepassen",
        "French": "Enregistrer et appliquer",
        "German": "Speichern und anwenden",
        "Hindi": "सहेजें और लागू करें",
        "Italian": "Salva e Applica",
        "Persian": "ذخیره و اعمال",
        "Polish": "Zapisz i zastosuj",
        "Turkish": "Kaydet ve Uygula"
    },
    "msg_confirm_salvar_titulo": {
        "Portuguese": "Confirmar",
        "English": "Confirm",
        "Spanish": "Confirmar",
        "Chinese": "确认",
        "Japanese": "確認",
        "Korean": "확인",
        "Russian": "Подтверждение",
        "Ukrainian": "Підтвердження",
        "Indonesian": "Konfirmasi",
        "Filipino": "Kumpirmahin",
        "Vietnamese": "Xác nhận",
        "Norwegian": "Bekreft",
        "Hausa": "Tabbatarwa",
        "Bambara": "Dalenya",
        "Latin": "Confirmare",
        "Arabic": "تأكيد",
        "Bengali": "নিশ্চিত করুন",
        "Dutch": "Bevestigen",
        "French": "Confirmer",
        "German": "Bestätigen",
        "Hindi": "पुष्टि करें",
        "Italian": "Conferma",
        "Persian": "تأیید",
        "Polish": "Potwierdź",
        "Turkish": "Onayla"
    },
    "msg_confirm_salvar_texto": {
        "Portuguese": "Tem certeza que deseja salvar as configurações atuais?",
        "English": "Are you sure you want to save the current settings?",
        "Spanish": "¿Está seguro de que desea guardar la configuración actual?",
        "Chinese": "确定要保存当前设置吗？",
        "Japanese": "現在の設定を保存してもよろしいですか？",
        "Korean": "현재 설정을 저장하시겠습니까?",
        "Russian": "Вы уверены, что хотите сохранить текущие настройки?",
        "Ukrainian": "Ви впевнені, що хочете зберегти поточні налаштування?",
        "Indonesian": "Apakah Anda yakin ingin menyimpan pengaturan saat ini?",
        "Filipino": "Sigurado ka bang gusto mong i-save ang kasalukuyang mga setting?",
        "Vietnamese": "Bạn có chắc chắn muốn lưu các cài đặt hiện tại không?",
        "Norwegian": "Er du sikker på at du vil lagre de gjeldende innstillingene?",
        "Hausa": "Kun tabbata kuna son ajiye saitunan yanzu?",
        "Bambara": "I dalen b'a la ko i b'a fɛ ka labɛnw mara sisan wa?",
        "Latin": "Certusne es te optata hodierna servare velle?",
        "Arabic": "هل أنت متأكد من رغبتك في حفظ الإعدادات الحالية؟",
        "Bengali": "আপনি কি নিশ্চিত যে আপনি বর্তমান সেটিংস সংরক্ষণ করতে চান?",
        "Dutch": "Weet u zeker dat u de huidige instellingen wilt opslaan?",
        "French": "Êtes-vous sûr de vouloir enregistrer les paramètres actuels ?",
        "German": "Sind Sie sicher, dass Sie die aktuellen Einstellungen speichern möchten?",
        "Hindi": "क्या आप वाकई वर्तमान सेटिंग्स सहेजना चाहते हैं?",
        "Italian": "Sei sicuro di voler salvare le impostazioni correnti?",
        "Persian": "آیا مطمئن هستید که می‌خواهید تنظیمات فعلی را ذخیره کنید؟",
        "Polish": "Czy na pewno chcesz zapisać bieżące ustawienia?",
        "Turkish": "Mevcut ayarları kaydetmek istediğinizden emin misiniz?"
    },
    "msg_sucesso_salvar_texto": {
        "Portuguese": "Configurações salvas com sucesso",
        "English": "Settings saved successfully",
        "Spanish": "Configuración guardada con éxito",
        "Chinese": "设置已成功保存",
        "Japanese": "設定が正常に保存されました",
        "Korean": "설정이 성공적으로 저장되었습니다",
        "Russian": "Настройки успешно сохранены",
        "Ukrainian": "Налаштування успішно збережено",
        "Indonesian": "Pengaturan berhasil disimpan",
        "Filipino": "Matagumpay na na-save ang mga setting",
        "Vietnamese": "Đã lưu cài đặt thành công",
        "Norwegian": "Innstillingene ble lagret",
        "Hausa": "An ajiye saitunan cikin nasara",
        "Bambara": "Labɛnw marana ka ɲa",
        "Latin": "Optata feliciter servata sunt",
        "Arabic": "تم حفظ الإعدادات بنجاح",
        "Bengali": "সেটিংস সফলভাবে সংরক্ষিত হয়েছে",
        "Dutch": "Instellingen succesvol opgeslagen",
        "French": "Paramètres enregistrés avec succès",
        "German": "Einstellungen erfolgreich gespeichert",
        "Hindi": "सेटिंग्स सफलतापूर्वक सहेजी गईं",
        "Italian": "Impostazioni salvate con successo",
        "Persian": "تنظیمات با موفقیت ذخیره شد",
        "Polish": "Ustawienia zostały pomyślnie zapisane",
        "Turkish": "Ayarlar başarıyla kaydedildi"
    },
    "lbl_desativar_animacoes": {
        "Portuguese": "Desativar animações",
        "English": "Disable animations",
        "Spanish": "Desactivar animaciones",
        "Chinese": "禁用动画",
        "Japanese": "アニメーションを無効化",
        "Korean": "애니메이션 비활성화",
        "Russian": "Отключить анимацию",
        "Ukrainian": "Вимкнути анімацію",
        "Indonesian": "Nonaktifkan animasi",
        "Filipino": "Huwag paganahin ang mga animasyon",
        "Vietnamese": "Tắt hiệu ứng động",
        "Norwegian": "Deaktiver animasjoner",
        "Hausa": "Kashe motsin hoto",
        "Bambara": "Lamagaliw dabɔ",
        "Latin": "Animationes disactivare",
        "Arabic": "تعطيل الرسوم المتحركة",
        "Bengali": "অ্যানিমেশন নিষ্ক্রিয় করুন",
        "Dutch": "Animaties uitschakelen",
        "French": "Désactiver les animations",
        "German": "Animationen deaktivieren",
        "Hindi": "एनिमेशन अक्षम करें",
        "Italian": "Disattiva animazioni",
        "Persian": "غیرفعال کردن انیمیشن‌ها",
        "Polish": "Wyłącz animacje",
        "Turkish": "Animasyonları devre dışı bırak"
    }
}

# Função auxiliar com fallback para Inglês caso alguma chave de idioma não exista
def traduzir(chave):
    bloco = DICIONARIO_IDIOMAS.get(chave, {})
    return bloco.get(idioma_atual, bloco.get("English", chave))

# -------------------------------
# *******************************
# -------------------------------

caminho_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
caminho_icons = os.path.join(caminho_base, "Icons")

# Localização dinâmica do FFmpeg compatível com diferentes distros Linux, Flatpak, Homebrew e Windows
if SISTEMA == 'Windows':
    caminho_ffmpeg_local = os.path.join(caminho_base, 'ffmpeg')
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + caminho_ffmpeg_local
    binario_ffmpeg = shutil.which("ffmpeg")
    caminho_ffmpeg_dir = os.path.dirname(binario_ffmpeg) if binario_ffmpeg else caminho_ffmpeg_local
else:
    binario_ffmpeg = shutil.which("ffmpeg")
    caminho_ffmpeg_dir = os.path.dirname(binario_ffmpeg) if binario_ffmpeg else '/usr/bin'

# --- Limpeza Segura de Processos Filhos ---
def encerrar_processos_filhos():
    
    # Finaliza apenas processos do FFmpeg criados por esta instância do Crimson (preservando outros apps do usuário)
    meu_pid = os.getpid()
    
    try:
        if SISTEMA == 'Windows':
            cmd_ps = (
                f"Get-CimInstance Win32_Process -Filter \"ParentProcessId = {meu_pid}\" | "
                "ForEach-Object { "
                "if ($_.Name -ieq 'ffmpeg.exe' -or $_.Name -ieq 'ffprobe.exe') { "
                "Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue "
                "} "
                "Get-CimInstance Win32_Process -Filter \"ParentProcessId = $($_.ProcessId)\" | "
                "Where-Object { $_.Name -ieq 'ffmpeg.exe' -or $_.Name -ieq 'ffprobe.exe' } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } "
                "}"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd_ps],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            subprocess.run(
                ["pkill", "-KILL", "-P", str(meu_pid), "-x", "ffmpeg"],
                capture_output=True
            )
            subprocess.run(
                ["pkill", "-KILL", "-P", str(meu_pid), "-x", "ffprobe"],
                capture_output=True
            )
            res = subprocess.run(["pgrep", "-P", str(meu_pid)], capture_output=True, text=True)
            for linha in res.stdout.splitlines():
                pid_filho = linha.strip()
                if pid_filho.isdigit():
                    subprocess.run(
                        ["pkill", "-KILL", "-P", pid_filho, "-x", "ffmpeg"],
                        capture_output=True
                    )
    except Exception as erro_proc:
        registrar_erro("encerrar_processos_filhos", erro_proc)

# --------------------------------------------------------------------------------------------------------------------
# --- Mecanismo de Pausa Customizado (O Truque da Exceção) ---
# O yt-dlp é excelente, mas não possui uma função nativa de "pausa"
# Para contornar isso, nós criamos nossa própria Classe de Erro (Exception) abaixo. A lógica funciona em 4 passos:
# 1. O yt-dlp aciona o "espião" (a função atualizar_progresso) a cada avanço percentual do download
# 2. Se o usuário tiver clicado no botão Pausa, o espião dispara esse erro abaixo intencionalmente (raise DownloadPausado)
# 3. O disparo do erro corta a linha de execução do yt-dlp na mesma hora, forçando ele a parar e deixar o arquivo '.part' salvo na pasta
# 4. A função 'thread_download' pega esse erro no bloco 'try...except' e simplesmente dá um "pass" (ignora), evitando que o aplicativo quebre ou trave
# Quando o usuário clica em "Continuar", apenas mando ele baixar novamente. O yt-dlp acha o arquivo '.part' na pasta e retoma de onde o corte ocorreu
class DownloadPausado(Exception):
    pass

estado_download = "parado"  # "rodando", "pausado", "cancelado"
url_atual = ""
caminho_salvamento_atual = ""
tipo_atual = ""
formato_atual = ""

def baixar_midia(url, tipo, formato, hook_progresso, caminho_completo):
    # Configurações base de Download (ydl_opts)
    ydl_opts = {
        # Define o caminho exato de saída já com nome e extensão que o usuário escolheu
        'outtmpl': caminho_completo,

        # Conecta a função da nossa barra de progresso no sistema do yt-dlp
        'progress_hooks': [hook_progresso],

        # Indica para o yt-dlp onde encontrar o executável do ffmpeg
        'ffmpeg_location': caminho_ffmpeg_dir,

        # Garante que links contendo listas de reprodução baixem apenas o vídeo individual
        'noplaylist': True,

        # Mostra o progresso no console
        'quiet': False,
        'no_warnings': True,

        # Desativa códigos de cores (ANSI) para que o texto da barra de progresso fique limpo
        'color': 'no_color',

        # Otimização de rede por divisão de blocos e múltiplas conexões
        'concurrent_fragment_downloads': 5,  # Usa 5 conexões simultâneas para baixar os pedaços
        'http_chunk_size': 10485760,         # Divide em blocos de 10MB para download estável
    }

    # Se o usuário escolheu áudio, configuro para extrair o áudio
    if tipo == 'audio':
        ydl_opts['format'] = 'bestaudio/best'  # Pega a melhor qualidade de áudio
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': formato,
            'preferredquality': '192',  # Qualidade do áudio (192kbps é um bom padrão)
        }]

    # Se o usuário escolheu vídeo, configuro para baixar vídeo e áudio juntos
    elif tipo == 'video':
        # Força o download de formatos que sejam naturalmente compatíveis
        # evitando que o FFmpeg precise re-renderizar o vídeo (poupando 100% de CPU)
        if formato == 'mp4':
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

        # O merge_output_format diz ao FFmpeg apenas para juntar o áudio e o vídeo (Muxing)
        ydl_opts['merge_output_format'] = formato

    # Evita exibir a URL bruta no terminal para proteger tokens/links privado
    print(f"[*] Preparando para baixar mídia ({tipo} - {formato})...")

    # Inicializa o yt-dlp com as configurações preparadas e dispara o download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("[*] Download concluído com sucesso")


# --------------------------------------------------------------------------------------------------------------------
# --- Utilitários Visuais (Manipulação de Ícones com Pillow + Qt e Cache de CPU) ---
# --------------------------------------------------------------------------------------------------------------------

# Expressões regulares pré-compiladas para evitar overhead de compilação em loops de alta frequência
RE_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[mK]')
RE_ESPACO_VELOCIDADE = re.compile(r'(?<=\d)(?=[a-zA-Z])')

# Caches em RAM para eliminar completamente I/O de disco e processamento gráfico repetitivo
_CACHE_PIXMAPS = {}
_CACHE_ICONES = {}

def hex_para_rgb(cor_hex):
    
    """Converte uma cor hexadecimal (ex: '#EDF2F4') em tupla (R, G, B)."""
    
    cor_hex = cor_hex.lstrip('#')
    return tuple(int(cor_hex[i:i + 2], 16) for i in (0, 2, 4))

def carregar_pixmap_icone(nome_arquivo, tamanho=(96, 96), cor_hex=None, opacidade=1.0):
    
    """
    Carrega um ícone da pasta Icons/ usando Pillow, aplica recoloração temática opcional
    e ajuste de opacidade no canal Alpha, retornando um QPixmap em alta resolução com anti-aliasing
    Se cor_hex for None, mantém a cor estática e original do ícone sem alteração
    Utiliza cache em memória para evitar leituras de disco repetidas e economizar CPU
    """
    
    chave = (nome_arquivo, tamanho, cor_hex, opacidade)
    if chave in _CACHE_PIXMAPS:
        return _CACHE_PIXMAPS[chave]

    caminho = os.path.join(caminho_icons, nome_arquivo)
    if not os.path.exists(caminho):
        return QPixmap()

    try:
        img = Image.open(caminho).convert("RGBA")
        if tamanho:
            img = img.resize(tamanho, Image.Resampling.LANCZOS)

        # Recolore os pixels apenas se uma cor específica for informada
        if cor_hex:
            r, g, b, a = img.split()
            cr, cg, cb = hex_para_rgb(cor_hex)
            img_colorida = Image.new("RGBA", img.size, (cr, cg, cb, 255))
            r, g, b, _ = img_colorida.split()

            if opacidade < 1.0:
                a = a.point(lambda p: int(p * opacidade))

            img_final = Image.merge("RGBA", (r, g, b, a))
        else:
            if opacidade < 1.0:
                r, g, b, a = img.split()
                a = a.point(lambda p: int(p * opacidade))
                img_final = Image.merge("RGBA", (r, g, b, a))
            else:
                img_final = img

        dados = img_final.tobytes("raw", "RGBA")
        qimg = QImage(dados, img_final.width, img_final.height, img_final.width * 4, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg.copy())
        _CACHE_PIXMAPS[chave] = pixmap
        return pixmap
    except Exception:
        return QPixmap()

def carregar_icone_tematico(nome_arquivo, tamanho=(96, 96), cor_hex=None, opacidade=1.0):
    
    """Retorna um QIcon em alta resolução pronto para uso em QPushButton com cache em RAM"""
    
    chave = (nome_arquivo, tamanho, cor_hex, opacidade)
    if chave in _CACHE_ICONES:
        return _CACHE_ICONES[chave]

    pixmap = carregar_pixmap_icone(nome_arquivo, tamanho, cor_hex, opacidade)
    icone = QIcon(pixmap) if not pixmap.isNull() else QIcon()
    _CACHE_ICONES[chave] = icone
    return icone

def aplicar_paleta_global(cor):
    
    """
    Aplica as cores do tema na paleta global do aplicativo
    Sem isso, os pop-ups (QMessageBox) e a janela de salvar herdam a cor do texto do sistema
    (ex: texto branco do KDE Breeze Dark sobre o fundo creme do tema Egg = texto ilegível)
    """
    
    app = QApplication.instance()
    if app is None:
        return

    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(cor["cor_fundo_janela"]))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(cor["cor_do_texto"]))
    paleta.setColor(QPalette.ColorRole.Base, QColor(cor["cor_barra_de_pesquisa"]))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(cor["cor_card"]))
    paleta.setColor(QPalette.ColorRole.Text, QColor(cor["cor_texto_caixa_de_pesquisa"]))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor(cor["cor_texto_secundario"]))
    paleta.setColor(QPalette.ColorRole.Button, QColor(cor["cor_card"]))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(cor["cor_do_texto"]))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(cor["cor_botao_video"]))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(cor["cor_fonte_botoes"]))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor(cor["cor_card"]))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor(cor["cor_do_texto"]))
    paleta.setColor(QPalette.ColorRole.Link, QColor(cor["cor_botao_video"]))

    # Textos desativados ficam com a cor secundária (suave, mas ainda legível)
    for papel in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        paleta.setColor(QPalette.ColorGroup.Disabled, papel, QColor(cor["cor_texto_secundario"]))

    app.setPalette(paleta)

class ComboBoxModerno(QComboBox):
    
    """
    QComboBox customizado que desenha uma seta (chevron 'v') vetorial com anti-aliasing
    perfeito tanto no Windows quanto no Linux
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # Limita a quantidade de itens visíveis para acionar a barra de rolagem estilizada
        self.setMaxVisibleItems(7)
        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # O delegate padrão do QComboBox ignora as regras '::item' do stylesheet (hover, altura, cantos)
        # Com o QStyledItemDelegate, a lista passa a obedecer o visual definido em estilo_lista_dropdown()
        self.setItemDelegate(QStyledItemDelegate(self))
        self.view().viewport().setAutoFillBackground(False)

        # A lista aberta mora dentro de uma "janelinha" popup separada (container)
        # Por padrão ela é quadrada e pintada com a cor de fundo da janela, criando aquela moldura "quebrada"
        # ao redor da lista arredondada, deixo o container sem borda e transparente para só a lista aparecer
        container = self.view().window()
        container.setObjectName("popupDropdown")
        container.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        )
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cor_seta = QColor(TEMAS[tema_atual]["cor_fonte_botoes"])
        pen = QPen(cor_seta, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        cx = self.width() - 18
        cy = self.height() / 2.0

        caminho = QPainterPath()
        caminho.moveTo(QPointF(cx - 4.5, cy - 2.0))
        caminho.lineTo(QPointF(cx, cy + 2.5))
        caminho.lineTo(QPointF(cx + 4.5, cy - 2.0))
        painter.drawPath(caminho)
        painter.end()

class BarraProgressoModerna(QProgressBar):
    
    """
    QProgressBar customizado com renderização em cápsula e anti-aliasing
    Utiliza clipping por QPainterPath para garantir que o preenchimento (chunk)
    nunca apresente cantos retos/quadrados ao atingir as bordas da barra, seja
    no carregamento inicial (indeterminado) ou no progresso de downloads (0 a 100%)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self._pos_indeterminada = 0.0
        self._direcao = 1.0
        self._timer_indeterminado = QTimer(self)
        self._timer_indeterminado.timeout.connect(self._avancar_animacao)

    def _deve_animar(self):
        janela = self.window()
        minimizada = bool(janela and janela.isMinimized())
        return (self.minimum() == 0 and self.maximum() == 0) and (not desativar_animacoes) and (not minimizada)

    def sincronizar_animacao(self):
        if self._deve_animar() and self.isVisible():
            if not self._timer_indeterminado.isActive():
                self._timer_indeterminado.start(25)  # 40 FPS suave
        else:
            if self._timer_indeterminado.isActive():
                self._timer_indeterminado.stop()
            if desativar_animacoes:
                self._pos_indeterminada = 0.5
        self.update()

    def _avancar_animacao(self):
        if self._deve_animar():
            self._pos_indeterminada += 0.018 * self._direcao
            if self._pos_indeterminada >= 1.0:
                self._pos_indeterminada = 1.0
                self._direcao = -1.0
            elif self._pos_indeterminada <= 0.0:
                self._pos_indeterminada = 0.0
                self._direcao = 1.0
            self.update()
        else:
            if self._timer_indeterminado.isActive():
                self._timer_indeterminado.stop()

    def setRange(self, minimo, maximo):
        super().setRange(minimo, maximo)
        self.sincronizar_animacao()

    def showEvent(self, event):
        super().showEvent(event)
        self.sincronizar_animacao()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._timer_indeterminado.isActive():
            self._timer_indeterminado.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        raio = h / 2.0

        # Caminho exato da cápsula do trilho com recuo para a borda
        ret_trilho = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        caminho_capsula = QPainterPath()
        caminho_capsula.addRoundedRect(ret_trilho, raio - 1.0, raio - 1.0)

        cor = TEMAS[tema_atual]

        # Fundo e borda do trilho conforme o tema
        if tema_atual == "Frutiger Aero":
            grad_trilho = QLinearGradient(0, 0, 0, h)
            grad_trilho.setColorAt(0.0, QColor(200, 235, 255, 190))
            grad_trilho.setColorAt(0.5, QColor(235, 248, 255, 230))
            grad_trilho.setColorAt(1.0, QColor(190, 230, 255, 204))
            brush_trilho = QBrush(grad_trilho)
            pen_borda = QPen(QColor(115, 195, 250, 230), 1.5)
        elif tema_atual == "Platinum Disc":
            grad_trilho = QLinearGradient(0, 0, 0, h)
            grad_trilho.setColorAt(0.0, QColor("#1A1E26"))
            grad_trilho.setColorAt(0.5, QColor("#282E3A"))
            grad_trilho.setColorAt(1.0, QColor("#1A1E26"))
            brush_trilho = QBrush(grad_trilho)
            pen_borda = QPen(QColor("#64748B"), 1.2)
        else:
            brush_trilho = QBrush(QColor(cor["cor_progresso_fundo"]))
            pen_borda = QPen(QColor(cor["cor_borda_card"]), 1.0)

        painter.fillPath(caminho_capsula, brush_trilho)

        # Clipping geométrico, garante que o chunk nunca ultrapasse a curvatura da cápsula
        painter.save()
        painter.setClipPath(caminho_capsula)

        largura_util = w - 4.0
        if self.minimum() == 0 and self.maximum() == 0:
            largura_chunk = max(90.0, largura_util * 0.32)
            deslocamento = (largura_util - largura_chunk) * self._pos_indeterminada
            ret_chunk = QRectF(2.0 + deslocamento, 2.0, largura_chunk, h - 4.0)
        else:
            val = max(self.minimum(), min(self.maximum(), self.value()))
            faixa = self.maximum() - self.minimum()
            fracao = (val - self.minimum()) / faixa if faixa > 0 else 0.0
            largura_chunk = largura_util * fracao
            ret_chunk = QRectF(2.0, 2.0, largura_chunk, h - 4.0)

        if ret_chunk.width() > 0:
            if tema_atual == "Frutiger Aero":
                grad_chunk = QLinearGradient(0, 0, 0, h)
                grad_chunk.setColorAt(0.0, QColor("#AFF4FF"))
                grad_chunk.setColorAt(0.12, QColor("#52C5FF"))
                grad_chunk.setColorAt(0.48, QColor("#1AA5FF"))
                grad_chunk.setColorAt(0.52, QColor("#0087F0"))
                grad_chunk.setColorAt(1.0, QColor("#006DCF"))
                brush_chunk = QBrush(grad_chunk)
            elif tema_atual == "Platinum Disc":
                grad_chunk = QLinearGradient(0, 0, 0, h)
                grad_chunk.setColorAt(0.0, QColor("#E2E8F0"))
                grad_chunk.setColorAt(0.20, QColor("#94A3B8"))
                grad_chunk.setColorAt(0.50, QColor("#64748B"))
                grad_chunk.setColorAt(0.52, QColor("#475569"))
                grad_chunk.setColorAt(1.0, QColor("#708CAE"))
                brush_chunk = QBrush(grad_chunk)
            else:
                brush_chunk = QBrush(QColor(cor["cor_progresso_barra"]))

            caminho_chunk = QPainterPath()
            caminho_chunk.addRoundedRect(ret_chunk, raio - 2.0, raio - 2.0)
            painter.fillPath(caminho_chunk, brush_chunk)

        painter.restore()

        # Borda externa com anti-aliasing
        painter.setPen(pen_borda)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(caminho_capsula)
        painter.end()

def estilo_lista_dropdown(cor):
    
    """
    Estilo da lista aberta dos dropdowns, compartilhado pela janela principal e pela de Configurações
    """
    
    # Se o tema for Frutiger Aero ou Platinum Disc, personaliza a barra de rolagem com gradiente temático
    if tema_atual == "Frutiger Aero":
        bg_handle = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6ECBFF, stop:0.5 #0088FF, stop:1 #005FB8)"
        bg_handle_hover = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8CE0FF, stop:0.5 #1FA3FF, stop:1 #0077E6)"
    elif tema_atual == "Platinum Disc":
        bg_handle = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #A2B9D7, stop:0.5 #657997, stop:1 #475467)"
        bg_handle_hover = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C8DAF2, stop:0.5 #7D93B3, stop:1 #5B6B82)"
    else:
        bg_handle = cor["cor_botao_audio"]
        bg_handle_hover = cor["cor_botao_audio_hover"]

    return f"""
            QComboBox {{
                combobox-popup: 0;  /* Abre a lista abaixo do botão (o Fusion abre por cima, cobrindo ele) */
            }}
            QFrame#popupDropdown {{
                background: transparent;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {cor["cor_de_fundo_dropdown"]};
                color: {cor["cor_do_texto"]};
                border: 1.5px solid {cor["cor_borda_card"]};
                border-radius: 10px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView QWidget {{
                background: transparent;
            }}
            QComboBox QAbstractItemView::item {{
                color: {cor["cor_do_texto"]};
                min-height: 28px;
                padding: 0px 10px;
                border-radius: 6px;
            }}
            QComboBox QAbstractItemView::item:hover,
            QComboBox QAbstractItemView::item:selected {{
                background-color: {cor["cor_do_hover_dropdown"]};
                color: {cor["cor_do_texto"]};
            }}
            /* Barra de rolagem vertical personalizada: largura 10px com margem 2px = 6px úteis para border-radius 3px (cápsula perfeita) */
            QComboBox QAbstractItemView QScrollBar:vertical,
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 10px;
                margin: 4px 2px 4px 2px;
            }}
            QComboBox QAbstractItemView QScrollBar::track:vertical,
            QScrollBar::track:vertical,
            QComboBox QAbstractItemView QScrollBar::groove:vertical,
            QScrollBar::groove:vertical {{
                border: none;
                background: transparent;
            }}
            QComboBox QAbstractItemView QScrollBar::handle:vertical,
            QScrollBar::handle:vertical {{
                background: {bg_handle};
                min-height: 28px;
                border-radius: 3px;
                border: none;
            }}
            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover,
            QScrollBar::handle:vertical:hover {{
                background: {bg_handle_hover};
            }}
            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                width: 0px;
                background: transparent;
                border: none;
            }}
            QComboBox QAbstractItemView QScrollBar::add-page:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-page:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
                border: none;
            }}
    """

class BotaoSwitchTema(QPushButton):

    """
    Interruptor (Switch) estilizado dinamicamente de acordo com o tema ativo
    Responsável por controlar se as animações do tema devem tocar ou ficar estáticas
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(48, 24)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        raio = h / 2.0
        ativo = self.isChecked()
        cor = TEMAS[tema_atual]

        ret_trilho = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        caminho_trilho = QPainterPath()
        caminho_trilho.addRoundedRect(ret_trilho, raio - 1.0, raio - 1.0)

        if tema_atual == "Frutiger Aero":
            if ativo:
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor("#46DC70"))
                grad_trilho.setColorAt(0.5, QColor("#24B84D"))
                grad_trilho.setColorAt(1.0, QColor("#1A9E3D"))
                pen_borda = QPen(QColor(24, 134, 52, 230), 1.3)
            else:
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor(195, 230, 255, 210))
                grad_trilho.setColorAt(0.5, QColor(225, 244, 255, 235))
                grad_trilho.setColorAt(1.0, QColor(180, 222, 250, 220))
                pen_borda = QPen(QColor(110, 182, 235, 220), 1.3)
            brush_trilho = QBrush(grad_trilho)
        elif tema_atual == "Platinum Disc":
            if ativo:
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor("#8BA7CE"))
                grad_trilho.setColorAt(0.5, QColor("#547298"))
                grad_trilho.setColorAt(1.0, QColor("#405C80"))
                pen_borda = QPen(QColor("#C4D7F0"), 1.2)
            else:
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor("#181C24"))
                grad_trilho.setColorAt(0.5, QColor("#252B37"))
                grad_trilho.setColorAt(1.0, QColor("#181C24"))
                pen_borda = QPen(QColor("#64748B"), 1.2)
            brush_trilho = QBrush(grad_trilho)
        else:
            if ativo:
                brush_trilho = QBrush(QColor(cor["cor_botao_video"]))
                pen_borda = QPen(QColor(cor["cor_da_borda_botao_video"]), 1.2)
            else:
                brush_trilho = QBrush(QColor(cor["cor_progresso_fundo"]))
                pen_borda = QPen(QColor(cor["cor_borda_card"]), 1.2)

        painter.setPen(pen_borda)
        painter.setBrush(brush_trilho)
        painter.drawPath(caminho_trilho)

        diametro_pino = h - 6.0
        pos_x = (w - diametro_pino - 3.0) if ativo else 3.0
        ret_pino = QRectF(pos_x, 3.0, diametro_pino, diametro_pino)

        grad_pino = QLinearGradient(0, 3.0, 0, 3.0 + diametro_pino)
        if tema_atual == "Platinum Disc":
            grad_pino.setColorAt(0.0, QColor("#FFFFFF"))
            grad_pino.setColorAt(0.5, QColor("#E2E8F0"))
            grad_pino.setColorAt(1.0, QColor("#94A3B8"))
            pen_pino = QPen(QColor("#475569"), 1.0)
        else:
            grad_pino.setColorAt(0.0, QColor("#FFFFFF"))
            grad_pino.setColorAt(1.0, QColor("#E6F2FA"))
            pen_pino = QPen(QColor(0, 0, 0, 45), 1.0)

        painter.setPen(pen_pino)
        painter.setBrush(QBrush(grad_pino))
        painter.drawEllipse(ret_pino)
        painter.end()

# --------------------------------------------------------------------------------------------------------------------
# --- Ponte de Sinais Assíncronos (Thread-Safe UI Updates) ---
# --------------------------------------------------------------------------------------------------------------------

class SinaisDownload(QObject):

    """
    No Qt (PySide6), threads em segundo plano não devem alterar widgets diretamente
    Esses sinais enviam os eventos com segurança para a thread principal da interface
    """

    progresso = Signal(float, str)
    etapa_conversao = Signal()
    sucesso = Signal(str, str)
    erro = Signal(str)
    loading_concluido = Signal()

# --------------------------------------------------------------------------------------------------------------------
# --- Janela Modal: Plataformas Suportadas ---
# --------------------------------------------------------------------------------------------------------------------

class DialogoPlataformas(QDialog):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(470)
        self.construir_ui()
        self.atualizar_textos_e_tema()

    def construir_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(24, 22, 24, 20)
        layout_principal.setSpacing(14)

        self.lbl_titulo = QLabel()
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setObjectName("tituloModal")
        layout_principal.addWidget(self.lbl_titulo)

        # Card que direciona para a documentação oficial de sites suportados do yt-dlp sem listar marcas comerciais
        self.card_plataformas = QFrame()
        self.card_plataformas.setObjectName("cardInterno")
        layout_card = QVBoxLayout(self.card_plataformas)
        layout_card.setContentsMargins(20, 20, 20, 20)
        layout_card.setSpacing(12)

        self.botao_lista_oficial = QPushButton()
        self.botao_lista_oficial.setObjectName("botaoListaOficial")
        self.botao_lista_oficial.setMinimumHeight(42)
        self.botao_lista_oficial.setIconSize(QSize(26, 26))
        self.botao_lista_oficial.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_lista_oficial.clicked.connect(
            lambda: webbrowser.open("https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md")
        )
        layout_card.addWidget(self.botao_lista_oficial)

        layout_principal.addWidget(self.card_plataformas)

        self.lbl_aviso = QLabel()
        self.lbl_aviso.setWordWrap(True)
        self.lbl_aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_aviso.setObjectName("textoAviso")
        layout_principal.addWidget(self.lbl_aviso)

    def atualizar_textos_e_tema(self):
        cor = TEMAS[tema_atual]
        self.setWindowTitle(DICIONARIO_IDIOMAS["plataformas_titulo"][idioma_atual])
        self.lbl_titulo.setText(DICIONARIO_IDIOMAS["plataformas_titulo"][idioma_atual])
        self.botao_lista_oficial.setText(DICIONARIO_IDIOMAS["plataformas_texto"][idioma_atual])
        self.botao_lista_oficial.setIcon(carregar_icone_tematico("github.png", cor_hex=None))
        self.lbl_aviso.setText(DICIONARIO_IDIOMAS["plataformas_aviso"][idioma_atual])

        if tema_atual == "Frutiger Aero":
            estilo_fundo = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #BEE5FF, stop:0.5 #DEF3FF, stop:1 #C2F2D7);"
            estilo_card = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(235, 248, 255, 0.78), stop:0.5 rgba(210, 240, 255, 0.58), stop:1 rgba(190, 232, 255, 0.72)); border: 1.5px solid rgba(135, 200, 245, 0.80); border-radius: 14px;"
            estilo_btn = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(238, 249, 255, 0.94), stop:0.5 rgba(215, 240, 255, 0.88), stop:1 rgba(195, 230, 255, 0.92)); color: #0C2D48; border: 1px solid rgba(110, 182, 235, 0.85); border-radius: 10px; padding: 8px 16px; font-weight: bold;"
            estilo_btn_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(248, 253, 255, 0.98), stop:0.5 rgba(228, 246, 255, 0.95), stop:1 rgba(208, 238, 255, 0.96)); border: 1px solid rgba(80, 165, 230, 0.95);"
        elif tema_atual == "Platinum Disc":
            estilo_fundo = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222733, stop:0.5 #1A1E26, stop:1 #14171E);"
            estilo_card = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(46, 54, 68, 0.90), stop:0.5 rgba(34, 40, 52, 0.84), stop:1 rgba(24, 28, 38, 0.92)); border: 1px solid rgba(162, 185, 215, 0.85); border-radius: 14px;"
            estilo_btn = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #647796, stop:0.48 #485975, stop:0.52 #37465F, stop:1 #435470); color: #FFFFFF; border: 1px solid #8FA3BF; border-radius: 10px; padding: 8px 16px; font-weight: bold;"
            estilo_btn_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #788EAF, stop:0.48 #586C8C, stop:0.52 #455776, stop:1 #536886); border: 1px solid #B0C4DE;"
        else:
            estilo_fundo = f"background-color: {cor['cor_fundo_janela']};"
            estilo_card = f"background-color: {cor['cor_card']}; border: 1px solid {cor['cor_borda_card']}; border-radius: 14px;"
            estilo_btn = f"background-color: {cor['cor_fundo_janela']}; color: {cor['cor_do_texto']}; border: 1px solid {cor['cor_borda_card']}; border-radius: 10px; padding: 8px 16px; font-weight: bold;"
            estilo_btn_hover = f"background-color: {cor['cor_do_hover_dropdown']};"

        self.setStyleSheet(f"""
            QDialog {{
                {estilo_fundo}
            }}
            QLabel {{
                background: transparent;
            }}
            QLabel#tituloModal {{
                color: {cor["cor_do_texto"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 17px;
                font-weight: bold;
            }}
            QFrame#cardInterno {{
                {estilo_card}
            }}
            QPushButton#botaoListaOficial {{
                {estilo_btn}
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
            }}
            QPushButton#botaoListaOficial:hover {{
                {estilo_btn_hover}
            }}
            QLabel#textoAviso {{
                color: {cor["cor_texto_secundario"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 11px;
                font-style: italic;
                padding-top: 4px;
            }}
        """)

# --------------------------------------------------------------------------------------------------------------------
# --- Janela Modal: Configurações e Sobre ---
# --------------------------------------------------------------------------------------------------------------------

class DialogoConfiguracoes(QDialog):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.janela_mae = parent_window
        self.setModal(True)
        self.setMinimumSize(450, 500)
        self.construir_ui()
        self.atualizar_textos_e_tema()

    def construir_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(10)

        self.abas = QTabWidget()
        self.abas.tabBar().setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout_principal.addWidget(self.abas)

        # --- Sistema ---
        self.aba_sistema = QWidget()
        self.aba_sistema.setObjectName("abaSistema")
        layout_sistema = QVBoxLayout(self.aba_sistema)
        layout_sistema.setContentsMargins(16, 20, 16, 16)
        layout_sistema.setSpacing(16)

        # Card de Preferências
        self.card_prefs = QFrame()
        self.card_prefs.setObjectName("cardInterno")
        layout_prefs = QVBoxLayout(self.card_prefs)
        layout_prefs.setContentsMargins(20, 20, 20, 22)
        layout_prefs.setSpacing(10)

        self.label_idioma = QLabel()
        self.label_idioma.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_idioma.setObjectName("labelSecao")
        layout_prefs.addWidget(self.label_idioma)

        self.dropdown_idioma = ComboBoxModerno()
        self.dropdown_idioma.addItems(IDIOMAS_SUPORTADOS)
        self.dropdown_idioma.setCurrentText(idioma_atual)
        self.dropdown_idioma.setFixedWidth(190)
        self.dropdown_idioma.setFixedHeight(38)
        self.dropdown_idioma.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout_prefs.addWidget(self.dropdown_idioma, alignment=Qt.AlignmentFlag.AlignCenter)

        layout_prefs.addSpacing(8)

        self.label_tema = QLabel()
        self.label_tema.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_tema.setObjectName("labelSecao")
        layout_prefs.addWidget(self.label_tema)

        self.dropdown_tema = ComboBoxModerno()
        
        # Organiza a lista de temas pelo tamanho do nome (quantidade de caracteres) de forma crescente
        self.dropdown_tema.addItems(sorted(list(TEMAS.keys()), key=len))
        self.dropdown_tema.setCurrentText(tema_atual)
        self.dropdown_tema.setFixedWidth(190)
        self.dropdown_tema.setFixedHeight(38)
        self.dropdown_tema.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout_prefs.addWidget(self.dropdown_tema, alignment=Qt.AlignmentFlag.AlignCenter)

        layout_sistema.addWidget(self.card_prefs)
        layout_sistema.addStretch(1)

        # Card do Switch de Desativar Animações posicionado entre as preferências e a limpeza
        self.card_animacoes = QFrame()
        self.card_animacoes.setObjectName("cardInterno")
        self.card_animacoes.setMinimumWidth(250)
        self.card_animacoes.setFixedHeight(44)
        layout_anim = QHBoxLayout(self.card_animacoes)
        layout_anim.setContentsMargins(16, 6, 14, 6)
        layout_anim.setSpacing(14)

        self.label_animacoes = QLabel()
        self.label_animacoes.setObjectName("labelSecao")
        layout_anim.addWidget(self.label_animacoes)
        layout_anim.addStretch(1)

        self.switch_animacoes = BotaoSwitchTema()
        self.switch_animacoes.setChecked(desativar_animacoes)
        layout_anim.addWidget(self.switch_animacoes)

        layout_sistema.addWidget(self.card_animacoes, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_sistema.addStretch(1)

        # Botão de Limpeza de Processos
        self.botao_limpar = QPushButton()
        self.botao_limpar.setObjectName("botaoSecundario")
        self.botao_limpar.setFixedHeight(42)
        self.botao_limpar.setMinimumWidth(250)
        self.botao_limpar.setIconSize(QSize(22, 22))
        self.botao_limpar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_limpar.clicked.connect(self.limpar_processos)
        layout_sistema.addWidget(self.botao_limpar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Botão Salvar e Aplicar
        self.botao_salvar = QPushButton()
        self.botao_salvar.setObjectName("botaoPrimario")
        self.botao_salvar.setFixedHeight(42)
        self.botao_salvar.setMinimumWidth(190)
        self.botao_salvar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_salvar.clicked.connect(self.confirmar_e_salvar)
        layout_sistema.addWidget(self.botao_salvar, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Sobre ---
        self.aba_sobre = QWidget()
        self.aba_sobre.setObjectName("abaSobre")
        layout_sobre = QVBoxLayout(self.aba_sobre)
        layout_sobre.setContentsMargins(16, 18, 16, 10)
        layout_sobre.setSpacing(10)

        self.label_versao = QLabel()
        self.label_versao.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_versao.setObjectName("labelVersao")
        layout_sobre.addWidget(self.label_versao)

        self.label_disclaimer = QLabel()
        self.label_disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_disclaimer.setWordWrap(True)
        self.label_disclaimer.setObjectName("labelDisclaimer")
        layout_sobre.addWidget(self.label_disclaimer)

        self.icone_comunidade = QLabel()
        self.icone_comunidade.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_sobre.addWidget(self.icone_comunidade)

        self.label_creditos = QLabel()
        self.label_creditos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_creditos.setWordWrap(True)
        self.label_creditos.setObjectName("labelCreditos")
        layout_sobre.addWidget(self.label_creditos)

        # Card com links dos repositórios
        self.card_repos = QFrame()
        self.card_repos.setObjectName("cardInterno")
        layout_repos = QVBoxLayout(self.card_repos)
        layout_repos.setContentsMargins(16, 12, 16, 12)
        layout_repos.setSpacing(6)

        self.link_crimson = QPushButton()
        self.link_crimson.setObjectName("botaoLinkRepo")
        self.link_crimson.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.link_crimson.setIconSize(QSize(28, 28))
        self.link_crimson.clicked.connect(lambda: webbrowser.open("https://github.com/LuanDevCodes/Crimson"))
        layout_repos.addWidget(self.link_crimson)

        self.link_ytdlp = QPushButton()
        self.link_ytdlp.setObjectName("botaoLinkRepo")
        self.link_ytdlp.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.link_ytdlp.setIconSize(QSize(28, 28))
        self.link_ytdlp.clicked.connect(lambda: webbrowser.open("https://github.com/yt-dlp/yt-dlp"))
        layout_repos.addWidget(self.link_ytdlp)

        self.link_ffmpeg = QPushButton()
        self.link_ffmpeg.setObjectName("botaoLinkRepo")
        self.link_ffmpeg.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.link_ffmpeg.setIconSize(QSize(28, 28))
        self.link_ffmpeg.clicked.connect(lambda: webbrowser.open("https://github.com/BtbN/FFmpeg-Builds"))
        layout_repos.addWidget(self.link_ffmpeg)

        layout_sobre.addWidget(self.card_repos)
        layout_sobre.addStretch(1)

        self.marca_dagua = QLabel()
        self.marca_dagua.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.marca_dagua.setObjectName("marcaDagua")
        layout_sobre.addWidget(self.marca_dagua)

        self.abas.addTab(self.aba_sistema, "")
        self.abas.addTab(self.aba_sobre, "")

    def limpar_processos(self):
        resposta = QMessageBox.question(
            self,
            DICIONARIO_IDIOMAS["msg_confirm_limpeza_titulo"][idioma_atual],
            DICIONARIO_IDIOMAS["msg_confirm_limpeza_texto"][idioma_atual],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                encerrar_processos_filhos()
                gc.collect()

                QMessageBox.information(
                    self,
                    DICIONARIO_IDIOMAS["msg_sucesso_limpeza_titulo"][idioma_atual],
                    DICIONARIO_IDIOMAS["msg_sucesso_limpeza_texto"][idioma_atual]
                )
            except Exception as erro_limpeza:
                registrar_erro("limpar_processos", erro_limpeza)

    def confirmar_e_salvar(self):
        global idioma_atual, tema_atual, desativar_animacoes

        novo_idioma = self.dropdown_idioma.currentText()
        novo_tema = self.dropdown_tema.currentText()
        novo_desativar_anim = self.switch_animacoes.isChecked()

        titulo_msg = DICIONARIO_IDIOMAS["msg_confirm_salvar_titulo"].get(idioma_atual, "Confirm")
        texto_msg = DICIONARIO_IDIOMAS["msg_confirm_salvar_texto"].get(idioma_atual, "Are you sure you want to save?")

        resposta = QMessageBox.question(
            self,
            titulo_msg,
            texto_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            idioma_atual = novo_idioma
            tema_atual = novo_tema
            desativar_animacoes = novo_desativar_anim

            salvar_configuracoes(idioma_atual, tema_atual, desativar_animacoes)

            # Atualiza a janela principal e a janela de configurações em tempo real
            self.janela_mae.atualizar_idioma_ui()
            self.janela_mae.aplicar_tema()
            self.atualizar_textos_e_tema()

            texto_sucesso = DICIONARIO_IDIOMAS["msg_sucesso_salvar_texto"].get(idioma_atual, "Settings saved successfully")

            QMessageBox.information(self, titulo_msg, texto_sucesso)

    def atualizar_textos_e_tema(self):
        cor = TEMAS[tema_atual]

        self.setWindowTitle(f"{DICIONARIO_IDIOMAS['aba_sistema'][idioma_atual]} / {DICIONARIO_IDIOMAS['aba_sobre'][idioma_atual]}")
        self.abas.setTabText(0, DICIONARIO_IDIOMAS["aba_sistema"][idioma_atual])
        self.abas.setTabText(1, DICIONARIO_IDIOMAS["aba_sobre"][idioma_atual])

        self.label_idioma.setText(DICIONARIO_IDIOMAS["lbl_idioma"][idioma_atual])
        self.label_tema.setText(DICIONARIO_IDIOMAS["lbl_tema"][idioma_atual])
        self.label_animacoes.setText(DICIONARIO_IDIOMAS["lbl_desativar_animacoes"][idioma_atual])
        self.switch_animacoes.update()
        self.botao_limpar.setText("  " + DICIONARIO_IDIOMAS["btn_limpar_processos"][idioma_atual])
        self.botao_salvar.setText(DICIONARIO_IDIOMAS["btn_salvar_config"][idioma_atual])

        self.label_versao.setText(DICIONARIO_IDIOMAS["lbl_versao"][idioma_atual])
        self.label_disclaimer.setText(DICIONARIO_IDIOMAS["txt_disclaimer"][idioma_atual])
        self.label_creditos.setText(DICIONARIO_IDIOMAS["lbl_creditos"][idioma_atual])
        self.link_crimson.setText(DICIONARIO_IDIOMAS["link_crimson"][idioma_atual])
        self.link_ytdlp.setText(DICIONARIO_IDIOMAS["link_ytdlp"][idioma_atual])
        self.link_ffmpeg.setText(DICIONARIO_IDIOMAS["link_ffmpeg"][idioma_atual])
        self.marca_dagua.setText(DICIONARIO_IDIOMAS["marca_dagua"][idioma_atual])

        # Ícones recoloridos de acordo com o tema
        self.botao_limpar.setIcon(carregar_icone_tematico("limpar.png", cor_hex=cor["cor_fonte_botoes"]))
        pix_comm = carregar_pixmap_icone("comunidade.png", tamanho=(72, 72), cor_hex=cor["cor_do_texto"])
        if not pix_comm.isNull():
            self.icone_comunidade.setPixmap(pix_comm)

        # O ícone do GitHub é estático e preserva sua arte e transparência originais sem recoloração dinâmica
        icone_git = carregar_icone_tematico("github.png", cor_hex=None)
        self.link_crimson.setIcon(icone_git)
        self.link_ytdlp.setIcon(icone_git)
        self.link_ffmpeg.setIcon(icone_git)

        self.dropdown_idioma.update()
        self.dropdown_tema.update()

        if tema_atual == "Frutiger Aero":
            estilo_fundo = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #BEE5FF, stop:0.5 #DEF3FF, stop:1 #C2F2D7);"
            estilo_card = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(235, 248, 255, 0.78), stop:0.5 rgba(210, 240, 255, 0.58), stop:1 rgba(190, 232, 255, 0.72)); border: 1.5px solid rgba(135, 200, 245, 0.80); border-radius: 14px;"
            estilo_tab = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(238, 249, 255, 0.94), stop:0.48 rgba(220, 242, 255, 0.90), stop:0.52 rgba(205, 235, 255, 0.86), stop:1 rgba(192, 228, 255, 0.92)); color: #0C2D48; border: 1px solid rgba(110, 182, 235, 0.85); border-radius: 9px;"
            estilo_tab_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(248, 253, 255, 0.98), stop:0.48 rgba(232, 247, 255, 0.95), stop:0.52 rgba(218, 241, 255, 0.92), stop:1 rgba(205, 235, 255, 0.96)); color: #0C2D48; border: 1px solid rgba(110, 182, 235, 0.85);"
            estilo_tab_selected = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #46DC70, stop:0.48 #2BC455, stop:0.52 #20B046, stop:1 #1A9E3D); color: #FFFFFF; border: 1px solid rgba(30, 168, 64, 0.90); border-radius: 9px;"
            estilo_combo = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #48BAFF, stop:0.48 #22A2FF, stop:0.52 #0E8CF2, stop:1 #097CE0); color: #FFFFFF; border: 1px solid rgba(32, 140, 230, 0.90); border-radius: 9px; padding: 4px 30px 4px 14px;"
            estilo_combo_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60C5FF, stop:0.48 #36ADFF, stop:0.52 #1C98FA, stop:1 #1288EB); border: 1px solid rgba(32, 140, 230, 0.90);"
            estilo_btn_sec = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #48BAFF, stop:0.48 #22A2FF, stop:0.52 #0E8CF2, stop:1 #097CE0); color: #FFFFFF; border: 1px solid rgba(32, 140, 230, 0.90); border-radius: 10px; padding: 8px 18px;"
            estilo_btn_sec_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60C5FF, stop:0.48 #36ADFF, stop:0.52 #1C98FA, stop:1 #1288EB); border: 1px solid rgba(32, 140, 230, 0.90);"
            estilo_btn_prim = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #46DC70, stop:0.48 #2BC455, stop:0.52 #20B046, stop:1 #1A9E3D); color: #FFFFFF; border: 1px solid rgba(30, 168, 64, 0.90); border-radius: 10px; padding: 8px 22px;"
            estilo_btn_prim_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5CE482, stop:0.48 #3AD063, stop:0.52 #2BBE52, stop:1 #22AC47); border: 1px solid rgba(30, 168, 64, 0.90);"
        elif tema_atual == "Platinum Disc":
            estilo_fundo = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222733, stop:0.5 #1A1E26, stop:1 #14171E);"
            estilo_card = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(46, 54, 68, 0.90), stop:0.5 rgba(34, 40, 52, 0.84), stop:1 rgba(24, 28, 38, 0.92)); border: 1px solid rgba(162, 185, 215, 0.85); border-radius: 14px;"
            estilo_tab = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3D4759, stop:0.48 #2B3342, stop:0.52 #202633, stop:1 #283140); color: #CBD5E1; border: 1px solid #64748B; border-radius: 9px;"
            estilo_tab_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #505E75, stop:0.48 #3A4557, stop:0.52 #2B3545, stop:1 #354254); color: #FFFFFF; border: 1px solid #8FA3BF;"
            estilo_tab_selected = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7592B8, stop:0.48 #547298, stop:0.52 #405C80, stop:1 #4D6B90); color: #FFFFFF; border: 1px solid #A2B9D7; border-radius: 9px;"
            estilo_combo = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #647796, stop:0.48 #485975, stop:0.52 #37465F, stop:1 #435470); color: #FFFFFF; border: 1px solid #8FA3BF; border-radius: 9px; padding: 4px 30px 4px 14px;"
            estilo_combo_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #788EAF, stop:0.48 #586C8C, stop:0.52 #455776, stop:1 #536886); border: 1px solid #B0C4DE;"
            estilo_btn_sec = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #647796, stop:0.48 #485975, stop:0.52 #37465F, stop:1 #435470); color: #FFFFFF; border: 1px solid #8FA3BF; border-radius: 10px; padding: 8px 18px;"
            estilo_btn_sec_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #788EAF, stop:0.48 #586C8C, stop:0.52 #455776, stop:1 #536886); border: 1px solid #B0C4DE;"
            estilo_btn_prim = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7592B8, stop:0.48 #547298, stop:0.52 #405C80, stop:1 #4D6B90); color: #FFFFFF; border: 1px solid #A2B9D7; border-radius: 10px; padding: 8px 22px;"
            estilo_btn_prim_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8BA7CE, stop:0.48 #6584AB, stop:0.52 #4F6F94, stop:1 #6080A5); border: 1px solid #C4D7F0;"
        else:
            estilo_fundo = f"background-color: {cor['cor_fundo_janela']};"
            estilo_card = f"background-color: {cor['cor_card']}; border: 1px solid {cor['cor_borda_card']}; border-radius: 14px;"
            estilo_tab = f"background-color: {cor['cor_card']}; color: {cor['cor_texto_secundario']}; border: 1px solid {cor['cor_borda_card']}; border-radius: 9px;"
            estilo_tab_hover = f"background-color: {cor['cor_do_hover_dropdown']}; color: {cor['cor_do_texto']};"
            estilo_tab_selected = f"background-color: {cor['cor_botao_video']}; color: {cor['cor_fonte_botoes']}; border: 1px solid {cor['cor_da_borda_botao_video']}; border-radius: 9px;"
            estilo_combo = f"background-color: {cor['cor_botao_audio']}; color: {cor['cor_fonte_botoes']}; border: 1px solid {cor['cor_da_borda_botao_audio']}; border-radius: 8px; padding: 4px 30px 4px 14px;"
            estilo_combo_hover = f"background-color: {cor['cor_botao_audio_hover']};"
            estilo_btn_sec = f"background-color: {cor['cor_botao_audio']}; color: {cor['cor_fonte_botoes']}; border: 1px solid {cor['cor_da_borda_botao_audio']}; border-radius: 10px; padding: 8px 18px;"
            estilo_btn_sec_hover = f"background-color: {cor['cor_botao_audio_hover']};"
            estilo_btn_prim = f"background-color: {cor['cor_botao_video']}; color: {cor['cor_fonte_botoes']}; border: 1px solid {cor['cor_da_borda_botao_video']}; border-radius: 10px; padding: 8px 22px;"
            estilo_btn_prim_hover = f"background-color: {cor['cor_botao_video_hover']};"

        self.setStyleSheet(f"""
            QDialog {{
                {estilo_fundo}
            }}
            QTabWidget, QTabWidget::pane, QTabBar, QWidget#abaSistema, QWidget#abaSobre {{
                background: transparent;
                border: none;
            }}
            QLabel {{
                background: transparent;
            }}
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                {estilo_tab}
                padding: 8px 28px;
                margin: 0px 4px;
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                {estilo_tab_selected}
            }}
            QTabBar::tab:hover:!selected {{
                {estilo_tab_hover}
            }}
            QFrame#cardInterno {{
                {estilo_card}
            }}
            QLabel#labelSecao {{
                color: {cor["cor_do_texto"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: 600;
            }}
            QLabel#labelVersao {{
                color: {cor["cor_do_texto"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 15px;
                font-weight: bold;
            }}
            QLabel#labelDisclaimer {{
                color: {cor["cor_texto_secundario"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 12px;
            }}
            QLabel#labelCreditos {{
                color: {cor["cor_do_texto"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 12px;
                font-style: italic;
            }}
            QLabel#marcaDagua {{
                color: {cor["cor_do_texto_magua"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 11px;
                font-style: italic;
            }}
            QComboBox {{
                {estilo_combo}
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QComboBox:hover {{
                {estilo_combo_hover}
            }}
            QComboBox::drop-down {{
                border: none;
                width: 26px;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            {estilo_lista_dropdown(cor)}
            QPushButton#botaoSecundario {{
                {estilo_btn_sec}
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#botaoSecundario:hover {{
                {estilo_btn_sec_hover}
            }}
            QPushButton#botaoPrimario {{
                {estilo_btn_prim}
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#botaoPrimario:hover {{
                {estilo_btn_prim_hover}
            }}
            QPushButton#botaoLinkRepo {{
                background-color: transparent;
                color: {cor["cor_do_texto"]};
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                text-align: left;
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton#botaoLinkRepo:hover {{
                background-color: {cor["cor_do_hover_dropdown"]};
            }}
        """)

# --------------------------------------------------------------------------------------------------------------------
# --- Superfície de Fundo Dinâmica & Efeito Frutiger Aero ---
# --------------------------------------------------------------------------------------------------------------------

class WidgetFundoCrimson(QWidget):
    """
    Widget central com suporte a renderização dinâmica
    - 'Frutiger Aero': desenha gradiente celeste límpido, feixe solar e bolhas vítreas flutuantes
    - 'Platinum Disc': desenha uma superfície metálica de platina escovada com disco de sulcos concêntricos
      e reflexo anisotrópico em rotação contínua (estética vinil/CD de platina e cromo polido)
    - Outros temas: preenchimento estático suave poupando 100% de CPU
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bolhas = []
        self.angulo_platina = 0.0
        self.brilho_platina = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._atualizar_animacao)
        self._inicializar_bolhas()

    def _inicializar_bolhas(self):
        self.bolhas = []
        for _ in range(12):
            self.bolhas.append({
                "x": random.uniform(0.04, 0.96),
                "y": random.uniform(0.0, 1.0),
                "raio": random.uniform(10, 26),
                "velocidade": random.uniform(0.0016, 0.0038),
                "opacidade": random.uniform(0.35, 0.75),
                "fase": random.uniform(0.0, 6.28),
                "frequencia": random.uniform(0.03, 0.06)
            })

    def sincronizar_tema(self):
        janela = self.window()
        minimizada = bool(janela and janela.isMinimized())
        if tema_atual in ("Frutiger Aero", "Platinum Disc") and not desativar_animacoes and not minimizada:
            if not self.timer.isActive():
                self.timer.start(40)  # ~25 FPS para fluidez impecável com consumo mínimo de CPU
        else:
            if self.timer.isActive():
                self.timer.stop()
        self.update()

    def _atualizar_animacao(self):
        janela = self.window()
        if tema_atual not in ("Frutiger Aero", "Platinum Disc") or desativar_animacoes or (janela and janela.isMinimized()):
            self.timer.stop()
            return

        if tema_atual == "Frutiger Aero":
            for b in self.bolhas:
                b["y"] -= b["velocidade"]
                b["fase"] += b["frequencia"]
                if b["y"] < -0.1:
                    b["y"] = 1.08
                    b["x"] = random.uniform(0.04, 0.96)
        elif tema_atual == "Platinum Disc":
            self.angulo_platina = (self.angulo_platina + 0.5) % 360.0
            self.brilho_platina += 0.04

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if tema_atual == "Frutiger Aero":
            # Gradiente Celeste Frutiger Aero (Azul Céu -> Ciano Aquático -> Verde Fresco)
            grad = QLinearGradient(0, 0, 0, self.height())
            grad.setColorAt(0.0, QColor("#1C8BF4"))   # Azul celeste
            grad.setColorAt(0.45, QColor("#56C8FF"))  # Ciano radiante
            grad.setColorAt(0.82, QColor("#B3F5CE"))  # Verde água límpido
            grad.setColorAt(1.0, QColor("#5DD64B"))   # Verde campestre vibrante
            painter.fillRect(self.rect(), grad)

            # Feixe de luz superior suave (efeito solar Frutiger Aero)
            luz = QRadialGradient(self.width() * 0.5, -self.height() * 0.2, self.width() * 0.75)
            luz.setColorAt(0.0, QColor(255, 255, 255, 95))
            luz.setColorAt(0.5, QColor(255, 255, 255, 25))
            luz.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillRect(self.rect(), luz)

            # Bolhas vítreas flutuantes com gradiente radial e reflexo especular
            w = self.width()
            h = self.height()
            for b in self.bolhas:
                bx = (b["x"] + math.sin(b["fase"]) * 0.018) * w
                by = b["y"] * h
                r = b["raio"]
                op = b["opacidade"]

                grad_bolha = QRadialGradient(bx - r * 0.3, by - r * 0.3, r * 1.3)
                grad_bolha.setColorAt(0.0, QColor(255, 255, 255, int(220 * op)))
                grad_bolha.setColorAt(0.35, QColor(255, 255, 255, int(50 * op)))
                grad_bolha.setColorAt(0.75, QColor(0, 210, 255, int(65 * op)))
                grad_bolha.setColorAt(1.0, QColor(255, 255, 255, int(140 * op)))

                painter.setPen(QPen(QColor(255, 255, 255, int(170 * op)), 1.2))
                painter.setBrush(QBrush(grad_bolha))
                painter.drawEllipse(QPointF(bx, by), r, r)

                # Ponto de reflexo superior vítreo
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, int(230 * op)))
                painter.drawEllipse(QPointF(bx - r * 0.35, by - r * 0.35), r * 0.22, r * 0.15)

        elif tema_atual == "Platinum Disc":
            w = self.width()
            h = self.height()
            cx = w * 0.5
            cy = h * 0.52
            raio_disco = max(w, h) * 0.72

            # Base metálica: platina escura escovada profunda
            grad_base = QRadialGradient(cx, cy, raio_disco)
            grad_base.setColorAt(0.0, QColor("#2A313E"))
            grad_base.setColorAt(0.48, QColor("#1D222B"))
            grad_base.setColorAt(1.0, QColor("#13161C"))
            painter.fillRect(self.rect(), grad_base)

            # Reflexo anisotrópico rotativo (feixe de luz metálico em cruz/ampulheta)
            grad_conico = QConicalGradient(cx, cy, self.angulo_platina)
            c_luz1 = QColor(220, 235, 255, 42)
            c_luz2 = QColor(255, 255, 255, 65)
            c_sombra = QColor(10, 13, 18, 48)
            c_neutro = QColor(180, 200, 225, 14)

            grad_conico.setColorAt(0.0, c_neutro)
            grad_conico.setColorAt(0.12, c_luz1)
            grad_conico.setColorAt(0.18, c_luz2)
            grad_conico.setColorAt(0.24, c_luz1)
            grad_conico.setColorAt(0.35, c_sombra)
            grad_conico.setColorAt(0.50, c_neutro)
            grad_conico.setColorAt(0.62, c_luz1)
            grad_conico.setColorAt(0.68, c_luz2)
            grad_conico.setColorAt(0.74, c_luz1)
            grad_conico.setColorAt(0.85, c_sombra)
            grad_conico.setColorAt(1.0, c_neutro)
            painter.fillRect(self.rect(), grad_conico)

            # Sulcos circulares concêntricos do disco de platina (estilo vinil / mídia óptica)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            passos_anel = 9
            for i in range(1, passos_anel + 1):
                r = (raio_disco / passos_anel) * i
                op_linha = 18 if i % 2 == 0 else 34
                painter.setPen(QPen(QColor(215, 230, 252, op_linha), 1.0))
                painter.drawEllipse(QPointF(cx, cy), r, r)

            # Brilho especular sutil pulsante central (miolo do disco)
            pulso = (math.sin(self.brilho_platina) + 1.0) * 0.5
            r_centro = 50 + pulso * 6
            grad_centro = QRadialGradient(cx, cy, r_centro)
            grad_centro.setColorAt(0.0, QColor(255, 255, 255, int(50 + pulso * 25)))
            grad_centro.setColorAt(0.5, QColor(190, 215, 245, int(22 + pulso * 15)))
            grad_centro.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(grad_centro))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(cx, cy), r_centro, r_centro)

        else:
            # Em outros temas, preenche com a cor sólida definida para a janela
            painter.fillRect(self.rect(), QColor(TEMAS[tema_atual]["cor_fundo_janela"]))

        painter.end()
        super().paintEvent(event)

# --------------------------------------------------------------------------------------------------------------------
# --- Janela Principal do Aplicativo ---
# --------------------------------------------------------------------------------------------------------------------

class JanelaCrimson(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crimson - Video Downloader")
        self.setMinimumSize(640, 370)
        self.resize(670, 385)

        # Controle de instâncias para evitar múltiplas janelas abertas simultaneamente
        self.dialogo_plataformas = None
        self.dialogo_config = None

        # Conecta os sinais para comunicação segura entre as threads e a interface
        self.sinais = SinaisDownload()
        self.sinais.progresso.connect(self.set_progresso_ui)
        self.sinais.etapa_conversao.connect(self.bloquear_pausa_na_conversao)
        self.sinais.sucesso.connect(self.finalizar_com_sucesso)
        self.sinais.erro.connect(self.finalizar_com_erro)
        self.sinais.loading_concluido.connect(self.finalizar_loading)

        # Controle de sincronismo de threads de download 
        self._thread_download = None
        self._evento_cancelar_atual = None

        # Controle de taxa de atualização gráfica (throttling para poupar CPU em downloads velozes)
        self._ultimo_update_progresso = 0.0

        self.configurar_icone_janela()
        self.construir_ui()
        self.aplicar_tema()
        self.centralizar_na_tela()
        self.iniciar_loading_atualizacao()

    def configurar_icone_janela(self):
        arquivos_icone = glob.glob(os.path.join(caminho_icons, "*Crimson*.png"))
        if arquivos_icone:
            self.setWindowIcon(QIcon(arquivos_icone[0]))

    def centralizar_na_tela(self):
        
        # O QGuiApplication.primaryScreen() já identifica o monitor principal de forma nativa no Windows e Linux (X11/Wayland)
        tela = QApplication.primaryScreen()
        if tela:
            geometria_disponivel = tela.availableGeometry()
            pos_x = geometria_disponivel.x() + (geometria_disponivel.width() - self.width()) // 2
            pos_y = geometria_disponivel.y() + (geometria_disponivel.height() - self.height()) // 2
            self.move(pos_x, pos_y)

    def construir_ui(self):
        self.widget_central = WidgetFundoCrimson(self)
        self.setCentralWidget(self.widget_central)

        layout_raiz = QVBoxLayout(self.widget_central)
        layout_raiz.setContentsMargins(26, 20, 26, 20)
        layout_raiz.setSpacing(14)

        # ------------------------------------------------------------------
        # --- Tela de Carregamento Inicial (Centralizada no Meio da Janela) ---
        self.container_loading = QWidget()
        layout_loading = QVBoxLayout(self.container_loading)
        layout_loading.setContentsMargins(0, 0, 0, 0)
        layout_loading.setSpacing(16)
        layout_loading.addStretch(1)

        self.label_loading = QLabel(DICIONARIO_IDIOMAS["instrucao_init"][idioma_atual])
        self.label_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_loading.setObjectName("labelLoading")
        layout_loading.addWidget(self.label_loading)

        self.barra_loading = BarraProgressoModerna()
        self.barra_loading.setObjectName("barraProgresso")
        self.barra_loading.setRange(0, 0)  # Modo indeterminado (animação contínua)
        self.barra_loading.setFixedHeight(18)
        self.barra_loading.setFixedWidth(380)
        self.barra_loading.setTextVisible(False)
        layout_loading.addWidget(self.barra_loading, alignment=Qt.AlignmentFlag.AlignCenter)
        layout_loading.addStretch(1)

        layout_raiz.addWidget(self.container_loading)

        # ------------------------------------------------------------------
        # --- Conteúdo Principal da Interface ---
        self.container_principal = QWidget()
        layout_principal = QVBoxLayout(self.container_principal)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(14)

        # Barra Superior (Configurações | Instrução | Plataformas)
        layout_topo = QHBoxLayout()
        layout_topo.setContentsMargins(0, 0, 0, 0)

        self.botao_config = QPushButton()
        self.botao_config.setObjectName("botaoIconeTopo")
        self.botao_config.setFixedSize(40, 40)
        self.botao_config.setIconSize(QSize(26, 26))
        self.botao_config.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_config.clicked.connect(self.abrir_configuracoes)
        layout_topo.addWidget(self.botao_config)

        self.label_instrucao = QLabel(DICIONARIO_IDIOMAS["instrucao_ready"][idioma_atual])
        self.label_instrucao.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_instrucao.setObjectName("labelInstrucao")
        layout_topo.addWidget(self.label_instrucao, stretch=1)

        self.botao_plataformas = QPushButton()
        self.botao_plataformas.setObjectName("botaoIconeTopo")
        self.botao_plataformas.setFixedSize(40, 40)
        self.botao_plataformas.setIconSize(QSize(26, 26))
        self.botao_plataformas.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_plataformas.clicked.connect(self.abrir_plataformas)
        layout_topo.addWidget(self.botao_plataformas)

        layout_principal.addLayout(layout_topo)

        # Campo de Entrada da URL
        self.entrada_url = QLineEdit()
        self.entrada_url.setObjectName("entradaUrl")
        self.entrada_url.setFixedHeight(44)
        self.entrada_url.setPlaceholderText(DICIONARIO_IDIOMAS["placeholder_url"][idioma_atual])
        self.entrada_url.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.entrada_url.customContextMenuRequested.connect(self.exibir_menu_contexto)
        layout_principal.addWidget(self.entrada_url)

        # Seção de Cards (Áudio e Vídeo lado a lado)
        self.container_acoes = QWidget()
        layout_cards = QHBoxLayout(self.container_acoes)
        layout_cards.setContentsMargins(0, 2, 0, 2)
        layout_cards.setSpacing(18)

        # Card de Áudio
        self.card_audio = QFrame()
        self.card_audio.setObjectName("cardAcao")
        layout_card_audio = QVBoxLayout(self.card_audio)
        layout_card_audio.setContentsMargins(16, 14, 16, 16)
        layout_card_audio.setSpacing(10)

        self.lbl_card_audio = QLabel(DICIONARIO_IDIOMAS["titulo_card_audio"][idioma_atual])
        self.lbl_card_audio.setObjectName("tituloCard")
        layout_card_audio.addWidget(self.lbl_card_audio)

        linha_audio = QHBoxLayout()
        linha_audio.setSpacing(10)

        self.dropdown_audio = ComboBoxModerno()
        self.dropdown_audio.setObjectName("dropdownAudio")
        self.dropdown_audio.addItems(["mp3", "m4a", "wav", "flac"])
        self.dropdown_audio.setFixedHeight(38)
        self.dropdown_audio.setFixedWidth(106)
        self.dropdown_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        linha_audio.addWidget(self.dropdown_audio)

        self.botao_baixar_audio = QPushButton(DICIONARIO_IDIOMAS["cor_botao_audio"][idioma_atual])
        self.botao_baixar_audio.setObjectName("botaoAudio")
        self.botao_baixar_audio.setFixedHeight(38)
        self.botao_baixar_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_baixar_audio.clicked.connect(lambda: self.iniciar_download('audio'))
        linha_audio.addWidget(self.botao_baixar_audio, stretch=1)

        layout_card_audio.addLayout(linha_audio)
        layout_cards.addWidget(self.card_audio, stretch=1)

        # Card de Vídeo
        self.card_video = QFrame()
        self.card_video.setObjectName("cardAcao")
        layout_card_video = QVBoxLayout(self.card_video)
        layout_card_video.setContentsMargins(16, 14, 16, 16)
        layout_card_video.setSpacing(10)

        self.lbl_card_video = QLabel(DICIONARIO_IDIOMAS["titulo_card_video"][idioma_atual])
        self.lbl_card_video.setObjectName("tituloCard")
        layout_card_video.addWidget(self.lbl_card_video)

        linha_video = QHBoxLayout()
        linha_video.setSpacing(10)

        self.dropdown_video = ComboBoxModerno()
        self.dropdown_video.setObjectName("dropdownVideo")
        self.dropdown_video.addItems(["mp4", "mkv", "webm"])
        self.dropdown_video.setFixedHeight(38)
        self.dropdown_video.setFixedWidth(106)
        self.dropdown_video.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        linha_video.addWidget(self.dropdown_video)

        self.botao_baixar_video = QPushButton(DICIONARIO_IDIOMAS["cor_botao_video"][idioma_atual])
        self.botao_baixar_video.setObjectName("botaoVideo")
        self.botao_baixar_video.setFixedHeight(38)
        self.botao_baixar_video.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_baixar_video.clicked.connect(lambda: self.iniciar_download('video'))
        linha_video.addWidget(self.botao_baixar_video, stretch=1)

        layout_card_video.addLayout(linha_video)
        layout_cards.addWidget(self.card_video, stretch=1)

        layout_principal.addWidget(self.container_acoes)

        # Barra de Progresso e Status do Download
        self.container_progresso = QWidget()
        layout_progresso = QVBoxLayout(self.container_progresso)
        layout_progresso.setContentsMargins(0, 2, 0, 0)
        layout_progresso.setSpacing(6)

        self.barra_progresso = BarraProgressoModerna()
        self.barra_progresso.setObjectName("barraProgresso")
        self.barra_progresso.setRange(0, 100)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setFixedHeight(18)
        self.barra_progresso.setTextVisible(False)
        layout_progresso.addWidget(self.barra_progresso)

        self.label_progresso = QLabel("")
        self.label_progresso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_progresso.setObjectName("labelProgresso")
        layout_progresso.addWidget(self.label_progresso)

        self.container_progresso.hide()
        layout_principal.addWidget(self.container_progresso)

        layout_principal.addStretch(1)

        # Controles de Execução (Pausar, Continuar, Excluir)
        self.frame_controles = QFrame()
        self.frame_controles.setObjectName("cardControles")
        layout_controles = QHBoxLayout(self.frame_controles)
        layout_controles.setContentsMargins(18, 6, 18, 6)
        layout_controles.setSpacing(24)

        self.botao_pausar = QPushButton()
        self.botao_pausar.setObjectName("botaoControle")
        self.botao_pausar.setFixedSize(44, 44)
        self.botao_pausar.setIconSize(QSize(28, 28))
        self.botao_pausar.setEnabled(False)
        self.botao_pausar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_pausar.clicked.connect(self.acionar_pausa)
        layout_controles.addWidget(self.botao_pausar)

        self.botao_continuar = QPushButton()
        self.botao_continuar.setObjectName("botaoControle")
        self.botao_continuar.setFixedSize(44, 44)
        self.botao_continuar.setIconSize(QSize(28, 28))
        self.botao_continuar.setEnabled(False)
        self.botao_continuar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_continuar.clicked.connect(self.acionar_retomar)
        layout_controles.addWidget(self.botao_continuar)

        self.botao_excluir = QPushButton()
        self.botao_excluir.setObjectName("botaoControle")
        self.botao_excluir.setFixedSize(44, 44)
        self.botao_excluir.setIconSize(QSize(28, 28))
        self.botao_excluir.setEnabled(False)
        self.botao_excluir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_excluir.clicked.connect(self.acionar_excluir)
        layout_controles.addWidget(self.botao_excluir)

        layout_principal.addWidget(self.frame_controles, alignment=Qt.AlignmentFlag.AlignCenter)

        layout_raiz.addWidget(self.container_principal)

    # ------------------------------------------------------------------
    # --- Menu de Contexto (Botão Direito na Barra de URL) ---
    def exibir_menu_contexto(self, posicao):
        if self.entrada_url.isReadOnly():
            return

        menu = QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        acao_colar = QAction(DICIONARIO_IDIOMAS["menu_colar"][idioma_atual], self)
        acao_colar.triggered.connect(self.entrada_url.paste)
        menu.addAction(acao_colar)

        acao_apagar = QAction(DICIONARIO_IDIOMAS["menu_apagar"][idioma_atual], self)
        acao_apagar.triggered.connect(self.apagar_texto_url)
        menu.addAction(acao_apagar)

        menu.exec(self.entrada_url.mapToGlobal(posicao))

    def apagar_texto_url(self):
        if self.entrada_url.hasSelectedText():
            self.entrada_url.del_()
        else:
            self.entrada_url.clear()

    # ------------------------------------------------------------------
    # --- Atualização de Ícones de Controle (Ativo / Inativo) ---
    def atualizar_icones_controles(self):
        cor_icone = TEMAS[tema_atual]["cor_do_texto"]

        op_pausa = 1.0 if self.botao_pausar.isEnabled() else 0.28
        op_cont = 1.0 if self.botao_continuar.isEnabled() else 0.28
        op_excl = 1.0 if self.botao_excluir.isEnabled() else 0.28

        self.botao_pausar.setIcon(carregar_icone_tematico("pausa.png", cor_hex=cor_icone, opacidade=op_pausa))
        self.botao_continuar.setIcon(carregar_icone_tematico("continuar.png", cor_hex=cor_icone, opacidade=op_cont))
        self.botao_excluir.setIcon(carregar_icone_tematico("excluir.png", cor_hex=cor_icone, opacidade=op_excl))

        self.botao_config.setIcon(carregar_icone_tematico("configuracoes.png", cor_hex=cor_icone, opacidade=0.95))
        self.botao_plataformas.setIcon(carregar_icone_tematico("duvidas.png", cor_hex=cor_icone, opacidade=0.95))

    # ------------------------------------------------------------------
    # --- Internacionalização e Temas ---
    def atualizar_idioma_ui(self):
        self.label_loading.setText(DICIONARIO_IDIOMAS["instrucao_init"][idioma_atual])
        self.label_instrucao.setText(DICIONARIO_IDIOMAS["instrucao_ready"][idioma_atual])
        self.entrada_url.setPlaceholderText(DICIONARIO_IDIOMAS["placeholder_url"][idioma_atual])
        self.lbl_card_audio.setText(DICIONARIO_IDIOMAS["titulo_card_audio"][idioma_atual])
        self.lbl_card_video.setText(DICIONARIO_IDIOMAS["titulo_card_video"][idioma_atual])

        if estado_download == "parado":
            self.botao_baixar_audio.setText(DICIONARIO_IDIOMAS["cor_botao_audio"][idioma_atual])
            self.botao_baixar_video.setText(DICIONARIO_IDIOMAS["cor_botao_video"][idioma_atual])

        if self.dialogo_plataformas and self.dialogo_plataformas.isVisible():
            self.dialogo_plataformas.atualizar_textos_e_tema()

    def aplicar_tema(self):
        cor = TEMAS[tema_atual]
        aplicar_paleta_global(cor)  # Garante que pop-ups e diálogos sigam o tema (e não o tema do sistema)
        self.widget_central.sincronizar_tema()
        self.barra_loading.sincronizar_animacao()
        self.atualizar_icones_controles()
        self.dropdown_audio.update()
        self.dropdown_video.update()
        self.barra_loading.update()
        self.barra_progresso.update()

        if tema_atual == "Frutiger Aero":
            # Cards translúcidos em vidro suave Frutiger Aero com borda celeste uniforme (sem borda branca que muda de cor)
            estilo_card = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(235, 248, 255, 0.76), stop:0.5 rgba(210, 240, 255, 0.56), stop:1 rgba(190, 232, 255, 0.70));
                border: 1.5px solid rgba(135, 200, 245, 0.80);
                border-radius: 14px;
            """
            estilo_card_ctrl = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(235, 248, 255, 0.80), stop:0.5 rgba(210, 240, 255, 0.62), stop:1 rgba(190, 232, 255, 0.72));
                border: 1.5px solid rgba(135, 200, 245, 0.80);
                border-radius: 14px;
            """
            estilo_btn_topo = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(238, 249, 255, 0.94), stop:0.48 rgba(220, 242, 255, 0.90), stop:0.52 rgba(205, 235, 255, 0.86), stop:1 rgba(192, 228, 255, 0.92));
                border: 1px solid rgba(110, 182, 235, 0.85);
                border-radius: 12px;
            """
            estilo_btn_topo_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(248, 253, 255, 0.98), stop:0.48 rgba(232, 247, 255, 0.95), stop:0.52 rgba(218, 241, 255, 0.92), stop:1 rgba(205, 235, 255, 0.96));
                border: 1px solid rgba(110, 182, 235, 0.85);
            """
            estilo_url = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(225, 244, 255, 0.90), stop:0.5 rgba(235, 248, 255, 0.92), stop:1 rgba(242, 251, 255, 0.94));
                color: #072F50;
                border: 1.5px solid rgba(115, 195, 250, 0.85);
                border-radius: 11px;
                padding: 0px 16px;
                font-size: 14px;
                font-weight: 500;
                selection-background-color: #0088FF;
                selection-color: #FFFFFF;
            """
            estilo_url_focus = "border: 1.5px solid rgba(115, 195, 250, 0.85);"
            estilo_dropdown_audio = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #48BAFF, stop:0.48 #22A2FF, stop:0.52 #0E8CF2, stop:1 #097CE0);
                color: #FFFFFF;
                border: 1px solid rgba(32, 140, 230, 0.90);
                border-radius: 9px;
                padding: 4px 24px 4px 10px;
                font-size: 12px;
                font-weight: bold;
            """
            estilo_dropdown_audio_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60C5FF, stop:0.48 #36ADFF, stop:0.52 #1C98FA, stop:1 #1288EB);
                border: 1px solid rgba(32, 140, 230, 0.90);
            """
            estilo_dropdown_video = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #46DC70, stop:0.48 #2BC455, stop:0.52 #20B046, stop:1 #1A9E3D);
                color: #FFFFFF;
                border: 1px solid rgba(30, 168, 64, 0.90);
                border-radius: 9px;
                padding: 4px 24px 4px 10px;
                font-size: 12px;
                font-weight: bold;
            """
            estilo_dropdown_video_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5CE482, stop:0.48 #3AD063, stop:0.52 #2BBE52, stop:1 #22AC47);
                border: 1px solid rgba(30, 168, 64, 0.90);
            """
            estilo_btn_video = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #46DC70, stop:0.48 #2BC455, stop:0.52 #20B046, stop:1 #1A9E3D);
                color: #FFFFFF;
                border: 1px solid rgba(30, 168, 64, 0.90);
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            """
            estilo_btn_video_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5CE482, stop:0.48 #3AD063, stop:0.52 #2BBE52, stop:1 #22AC47);
                border: 1px solid rgba(30, 168, 64, 0.90);
            """
            estilo_btn_audio = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #48BAFF, stop:0.48 #22A2FF, stop:0.52 #0E8CF2, stop:1 #097CE0);
                color: #FFFFFF;
                border: 1px solid rgba(32, 140, 230, 0.90);
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            """
            estilo_btn_audio_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60C5FF, stop:0.48 #36ADFF, stop:0.52 #1C98FA, stop:1 #1288EB);
                border: 1px solid rgba(32, 140, 230, 0.90);
            """
            estilo_barra = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(200, 235, 255, 0.75), stop:0.5 rgba(235, 248, 255, 0.90), stop:1 rgba(190, 230, 255, 0.80));
                border: 1.5px solid rgba(115, 195, 250, 0.90);
                border-radius: 9px;
            """
            estilo_barra_chunk = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #AFF4FF, stop:0.12 #52C5FF, stop:0.48 #1AA5FF, stop:0.52 #0087F0, stop:1 #006DCF);
                border-radius: 7px;
            """
            estilo_menu = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(240, 250, 255, 0.96), stop:0.5 rgba(220, 244, 255, 0.92), stop:1 rgba(200, 238, 255, 0.96));
                border: 1.5px solid rgba(135, 200, 245, 0.90);
                border-radius: 10px;
                padding: 5px;
            """
            estilo_menu_item = """
                color: #0C2D48;
                padding: 7px 22px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            """
            estilo_menu_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #48BAFF, stop:0.48 #22A2FF, stop:0.52 #0E8CF2, stop:1 #097CE0);
                color: #FFFFFF;
            """
        elif tema_atual == "Platinum Disc":
            # Estilo metálico em platina escovada, bordas em cromo e reflexos de alto contraste
            estilo_card = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(46, 54, 68, 0.90), stop:0.5 rgba(34, 40, 52, 0.84), stop:1 rgba(24, 28, 38, 0.92));
                border: 1px solid rgba(162, 185, 215, 0.85);
                border-radius: 14px;
            """
            estilo_card_ctrl = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(46, 54, 68, 0.90), stop:0.5 rgba(34, 40, 52, 0.84), stop:1 rgba(24, 28, 38, 0.92));
                border: 1px solid rgba(162, 185, 215, 0.85);
                border-radius: 14px;
            """
            estilo_btn_topo = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #424B5A, stop:0.48 #2E3542, stop:0.52 #222832, stop:1 #2D3442);
                border: 1px solid #7D8FAD;
                border-radius: 12px;
            """
            estilo_btn_topo_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #566377, stop:0.48 #3D4759, stop:0.52 #303947, stop:1 #3F4B5E);
                border: 1px solid #A3B8D6;
            """
            estilo_url = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(22, 26, 33, 0.92), stop:0.5 rgba(28, 33, 42, 0.90), stop:1 rgba(34, 40, 52, 0.94));
                color: #F8FAFC;
                border: 1.5px solid #64748B;
                border-radius: 11px;
                padding: 0px 16px;
                font-size: 14px;
                font-weight: 500;
                selection-background-color: #6382A8;
                selection-color: #FFFFFF;
            """
            estilo_url_focus = "border: 1.5px solid #94A3B8;"
            estilo_dropdown_audio = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #647796, stop:0.48 #485975, stop:0.52 #37465F, stop:1 #435470);
                color: #FFFFFF;
                border: 1px solid #8FA3BF;
                border-radius: 9px;
                padding: 4px 24px 4px 10px;
                font-size: 12px;
                font-weight: bold;
            """
            estilo_dropdown_audio_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #788EAF, stop:0.48 #586C8C, stop:0.52 #455776, stop:1 #536886);
                border: 1px solid #B0C4DE;
            """
            estilo_dropdown_video = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7592B8, stop:0.48 #547298, stop:0.52 #405C80, stop:1 #4D6B90);
                color: #FFFFFF;
                border: 1px solid #A2B9D7;
                border-radius: 9px;
                padding: 4px 24px 4px 10px;
                font-size: 12px;
                font-weight: bold;
            """
            estilo_dropdown_video_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8BA7CE, stop:0.48 #6584AB, stop:0.52 #4F6F94, stop:1 #6080A5);
                border: 1px solid #C4D7F0;
            """
            estilo_btn_video = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7592B8, stop:0.48 #547298, stop:0.52 #405C80, stop:1 #4D6B90);
                color: #FFFFFF;
                border: 1px solid #A2B9D7;
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            """
            estilo_btn_video_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8BA7CE, stop:0.48 #6584AB, stop:0.52 #4F6F94, stop:1 #6080A5);
                border: 1px solid #C4D7F0;
            """
            estilo_btn_audio = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #647796, stop:0.48 #485975, stop:0.52 #37465F, stop:1 #435470);
                color: #FFFFFF;
                border: 1px solid #8FA3BF;
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            """
            estilo_btn_audio_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #788EAF, stop:0.48 #586C8C, stop:0.52 #455776, stop:1 #536886);
                border: 1px solid #B0C4DE;
            """
            estilo_barra = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1A1E26, stop:0.5 #282E3A, stop:1 #1A1E26);
                border: 1.5px solid #64748B;
                border-radius: 9px;
            """
            estilo_barra_chunk = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #E2E8F0, stop:0.2 #94A3B8, stop:0.5 #64748B, stop:0.52 #475569, stop:1 #708CAE);
                border-radius: 7px;
            """
            estilo_menu = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(46, 54, 68, 0.96), stop:0.5 rgba(34, 40, 52, 0.92), stop:1 rgba(24, 28, 38, 0.96));
                border: 1.5px solid rgba(162, 185, 215, 0.85);
                border-radius: 10px;
                padding: 5px;
            """
            estilo_menu_item = """
                color: #F0F4F8;
                padding: 7px 22px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            """
            estilo_menu_hover = """
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #566377, stop:0.48 #3D4759, stop:0.52 #303947, stop:1 #3F4B5E);
                color: #FFFFFF;
                border: 1px solid rgba(162, 185, 215, 0.70);
            """
        else:
            hover_bg_menu = cor["cor_botao_audio"] if tema_atual in ("Dark", "Matcha") else cor["cor_botao_video"]
            estilo_menu = f"background-color: {cor['cor_card']}; border: 1.5px solid {cor['cor_borda_card']}; border-radius: 10px; padding: 5px;"
            estilo_menu_item = f"color: {cor['cor_do_texto']}; padding: 7px 22px; border-radius: 6px; font-size: 13px; font-weight: 500;"
            estilo_menu_hover = f"background-color: {hover_bg_menu}; color: {cor['cor_fonte_botoes']};"
            estilo_card = f"background-color: {cor['cor_card']}; border: 1px solid {cor['cor_borda_card']}; border-radius: 14px;"
            estilo_card_ctrl = f"background-color: {cor['cor_card']}; border: 1px solid {cor['cor_borda_card']}; border-radius: 14px;"
            estilo_btn_topo = f"background-color: {cor['cor_card']}; border: 1px solid {cor['cor_borda_card']}; border-radius: 10px;"
            estilo_btn_topo_hover = f"background-color: {cor['cor_do_hover_dropdown']};"
            estilo_url = f"background-color: {cor['cor_barra_de_pesquisa']}; color: {cor['cor_texto_caixa_de_pesquisa']}; border: 1.5px solid {cor['cor_borda_card']}; border-radius: 11px; padding: 0px 16px; font-size: 14px; selection-background-color: {cor['cor_botao_video']}; selection-color: {cor['cor_fonte_botoes']};"
            estilo_url_focus = f"border: 1.5px solid {cor['cor_botao_video']};"
            estilo_dropdown_audio = f"background-color: {cor['cor_botao_audio']}; color: {cor['cor_fonte_botoes']}; border: 1px solid {cor['cor_da_borda_botao_audio']}; border-radius: 9px; padding: 4px 24px 4px 10px; font-size: 12px; font-weight: bold;"
            estilo_dropdown_audio_hover = f"background-color: {cor['cor_botao_audio_hover']};"
            estilo_dropdown_video = f"background-color: {cor['cor_botao_video']}; color: {cor['cor_fonte_botoes']}; border: 1px solid {cor['cor_da_borda_botao_video']}; border-radius: 9px; padding: 4px 24px 4px 10px; font-size: 12px; font-weight: bold;"
            estilo_dropdown_video_hover = f"background-color: {cor['cor_botao_video_hover']};"
            estilo_btn_video = f"""
                background-color: {cor['cor_botao_video']};
                color: {cor['cor_fonte_botoes']};
                border: 1px solid {cor['cor_da_borda_botao_video']};
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            """
            estilo_btn_video_hover = f"background-color: {cor['cor_botao_video_hover']};"
            estilo_btn_audio = f"""
                background-color: {cor['cor_botao_audio']};
                color: {cor['cor_fonte_botoes']};
                border: 1px solid {cor['cor_da_borda_botao_audio']};
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            """
            estilo_btn_audio_hover = f"background-color: {cor['cor_botao_audio_hover']};"
            estilo_barra = f"background-color: {cor['cor_progresso_fundo']}; border: 1px solid {cor['cor_borda_card']}; border-radius: 9px;"
            estilo_barra_chunk = f"background-color: {cor['cor_progresso_barra']}; border-radius: 7px;"

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {cor["cor_fundo_janela"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
            }}
            WidgetFundoCrimson {{
                background: transparent;
            }}
            QLabel {{
                background: transparent;
            }}
            QLabel#labelInstrucao {{
                color: {cor["cor_do_texto"]};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton#botaoIconeTopo {{
                {estilo_btn_topo}
            }}
            QPushButton#botaoIconeTopo:hover {{
                {estilo_btn_topo_hover}
            }}
            QLineEdit#entradaUrl {{
                {estilo_url}
            }}
            QLineEdit#entradaUrl:focus {{
                {estilo_url_focus}
            }}
            QFrame#cardAcao {{
                {estilo_card}
            }}
            QLabel#tituloCard {{
                color: {cor["cor_texto_secundario"]};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QComboBox#dropdownAudio {{
                {estilo_dropdown_audio}
            }}
            QComboBox#dropdownAudio:hover {{
                {estilo_dropdown_audio_hover}
            }}
            QComboBox#dropdownVideo {{
                {estilo_dropdown_video}
            }}
            QComboBox#dropdownVideo:hover {{
                {estilo_dropdown_video_hover}
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            {estilo_lista_dropdown(cor)}
            QPushButton#botaoAudio {{
                {estilo_btn_audio}
            }}
            QPushButton#botaoAudio:hover:enabled {{
                {estilo_btn_audio_hover}
            }}
            QPushButton#botaoVideo {{
                {estilo_btn_video}
            }}
            QPushButton#botaoVideo:hover:enabled {{
                {estilo_btn_video_hover}
            }}
            QProgressBar#barraProgresso {{
                background: transparent;
                border: none;
            }}
            QProgressBar#barraProgresso::chunk {{
                background: transparent;
                border: none;
            }}
            QLabel#labelLoading {{
                color: {cor["cor_do_texto"]};
                font-size: 16px;
                font-weight: bold;
            }}
            QLabel#labelProgresso {{
                color: {cor["cor_do_texto"]};
                font-size: 12px;
                font-weight: 500;
            }}
            QFrame#cardControles {{
                {estilo_card_ctrl}
            }}
            QPushButton#botaoControle {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
            }}
            QPushButton#botaoControle:hover:enabled {{
                background-color: {cor["cor_do_hover_dropdown"]};
            }}
            QMenu {{
                {estilo_menu}
            }}
            QMenu::item {{
                {estilo_menu_item}
            }}
            QMenu::item:selected {{
                {estilo_menu_hover}
            }}
        """)

        if self.dialogo_plataformas and self.dialogo_plataformas.isVisible():
            self.dialogo_plataformas.atualizar_textos_e_tema()
        if self.dialogo_config and self.dialogo_config.isVisible():
            self.dialogo_config.atualizar_textos_e_tema()

    # ------------------------------------------------------------------
    # --- Abertura das Janelas Modais ---
    def abrir_plataformas(self):
        if self.dialogo_plataformas and self.dialogo_plataformas.isVisible():
            self.dialogo_plataformas.raise_()
            self.dialogo_plataformas.activateWindow()
            return

        self.dialogo_plataformas = DialogoPlataformas(self)
        self.dialogo_plataformas.show()

    def abrir_configuracoes(self):
        if self.dialogo_config and self.dialogo_config.isVisible():
            self.dialogo_config.raise_()
            self.dialogo_config.activateWindow()
            return

        self.dialogo_config = DialogoConfiguracoes(self)
        self.dialogo_config.show()

    def changeEvent(self, event):
        super().changeEvent(event)
        # Pausa ou retoma animações automaticamente ao minimizar/restaurar a janela para poupar CPU
        if event.type() == QEvent.Type.WindowStateChange:
            if hasattr(self, "widget_central"):
                self.widget_central.sincronizar_tema()
            if hasattr(self, "barra_loading"):
                self.barra_loading.sincronizar_animacao()

    def closeEvent(self, event):
        global estado_download
        # Proteção ao fechar a janela durante um download ativo para evitar processos órfãos
        if estado_download in ("rodando", "pausado"):
            resposta = QMessageBox.question(
                self,
                DICIONARIO_IDIOMAS["msg_excluir_titulo"][idioma_atual],
                DICIONARIO_IDIOMAS["msg_excluir_texto"][idioma_atual],
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resposta != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            estado_download = "cancelado"
            if self._evento_cancelar_atual:
                self._evento_cancelar_atual.set()
            encerrar_processos_filhos()
            self._remover_arquivos_residuais()
        else:
            encerrar_processos_filhos()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # --- Lógica da Tela de Carregamento (Update Inicial) ---
    def iniciar_loading_atualizacao(self):
        self.container_principal.hide()
        self.label_loading.setText(DICIONARIO_IDIOMAS["instrucao_init"][idioma_atual])
        self.container_loading.show()

        threading.Thread(target=self.thread_atualizacao_inicial, daemon=True).start()

    def thread_atualizacao_inicial(self):
        caminho_zip = os.path.join(lib_dir, f"yt-dlp-update-{os.getpid()}.zip")
        pasta_staging = os.path.join(lib_dir, f"yt-dlp-staging-{os.getpid()}")
        try:
            print("[*] Verificando atualizações de segurança (Motor yt-dlp)")
            url_master = "https://github.com/yt-dlp/yt-dlp/archive/refs/heads/master.zip"

            # Mantém compatibilidade com servidores/proxies identificando a versão do Crimson
            req = urllib.request.Request(
                url_master,
                headers={'User-Agent': f'Mozilla/5.0 (compatible; Crimson-Downloader/{VERSAO_APP})'}
            )
            limite_bytes = 50 * 1024 * 1024  # Limite de segurança de 50 MB
            total_lido = 0
            with urllib.request.urlopen(req, timeout=5) as response, open(caminho_zip, 'wb') as out_file:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    total_lido += len(chunk)
                    if total_lido > limite_bytes:
                        raise ValueError("Arquivo de atualização excedeu o limite máximo de segurança.")
                    out_file.write(chunk)

            # Validação de integridade e proteção contra Path Traversal antes de substituir o motor
            shutil.rmtree(pasta_staging, ignore_errors=True)
            os.makedirs(pasta_staging, exist_ok=True)
            staging_abs = os.path.abspath(pasta_staging)

            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                for membro in zip_ref.namelist():
                    destino_membro = os.path.abspath(os.path.join(pasta_staging, membro))
                    if not destino_membro.startswith(staging_abs + os.sep) and destino_membro != staging_abs:
                        raise ValueError(f"Caminho inseguro detectado no arquivo ZIP: {membro}")
                arquivo_corrompido = zip_ref.testzip()
                if arquivo_corrompido is not None:
                    raise zipfile.BadZipFile(f"Arquivo corrompido dentro do ZIP: {arquivo_corrompido}")
                zip_ref.extractall(pasta_staging)

            novo_motor = os.path.join(pasta_staging, "yt-dlp-master")
            init_ytdlp = os.path.join(novo_motor, "yt_dlp", "__init__.py")
            if not os.path.isfile(init_ytdlp):
                raise FileNotFoundError("Estrutura do motor yt-dlp inválida após extração.")

            path_extraido = os.path.join(lib_dir, "yt-dlp-master")
            shutil.rmtree(path_extraido, ignore_errors=True)
            shutil.move(novo_motor, path_extraido)

            if path_extraido not in sys.path:
                sys.path.insert(0, path_extraido)
            try:
                importlib.reload(yt_dlp)
            except Exception:
                pass

            print("[*] Motor atualizado e injetado - Interface pronta")
        except Exception as e:
            registrar_erro("thread_atualizacao_inicial", e)
            print(f"[*] Não foi possível atualizar o motor online: {e}")
        finally:
            # Limpeza garantida de arquivos temporários mesmo em caso de falha de rede
            if os.path.exists(caminho_zip):
                try:
                    os.remove(caminho_zip)
                except Exception:
                    pass
            if os.path.exists(pasta_staging):
                shutil.rmtree(pasta_staging, ignore_errors=True)
            self.sinais.loading_concluido.emit()

    def finalizar_loading(self):
        self.container_loading.hide()
        self.label_instrucao.setText(DICIONARIO_IDIOMAS["instrucao_ready"][idioma_atual])
        self.container_principal.show()

    # ------------------------------------------------------------------
    # --- Lógica de Download, Progresso e Controles ---
    def atualizar_progresso(self, d, evento_cancelar=None):
        global estado_download

        if estado_download in ("pausado", "cancelado") or (evento_cancelar and evento_cancelar.is_set()):
            raise DownloadPausado("Download interrompido pelo usuário.")

        if d['status'] == 'downloading':
            agora = time.time()
            percentual_str = d.get('_percent_str', '0%').strip()

            # Throttling de alta performance: limita atualizações da interface para ~16 FPS (60ms),
            # aliviando drasticamente a thread gráfica em conexões rápidas e PCs lentos
            if agora - self._ultimo_update_progresso < 0.06 and percentual_str != '100%':
                return
            self._ultimo_update_progresso = agora

            try:
                # Cálculo numérico direto por bytes com fallback para string percentual
                baixados = d.get('downloaded_bytes')
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                if isinstance(baixados, (int, float)) and isinstance(total, (int, float)) and total > 0:
                    percentual_float = min(100.0, max(0.0, (baixados / total) * 100.0))
                else:
                    percentual_limpo = RE_ANSI_ESCAPE.sub('', percentual_str).replace('%', '').strip()
                    percentual_float = float(percentual_limpo)

                eta = RE_ANSI_ESCAPE.sub('', d.get('_eta_str', 'N/A')).strip()
                velocidade = RE_ANSI_ESCAPE.sub('', d.get('_speed_str', 'N/A')).strip()
                velocidade = RE_ESPACO_VELOCIDADE.sub(' ', velocidade)

                texto = (
                    f"{DICIONARIO_IDIOMAS['progresso_baixando'][idioma_atual]}: {percentual_float:.1f}%   |   "
                    f"{DICIONARIO_IDIOMAS['progresso_vel'][idioma_atual]}: {velocidade}   |   "
                    f"{DICIONARIO_IDIOMAS['progresso_tempo'][idioma_atual]}: {eta}"
                )
                self.sinais.progresso.emit(percentual_float, texto)
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.sinais.etapa_conversao.emit()
            self.sinais.progresso.emit(100.0, DICIONARIO_IDIOMAS["progresso_convertendo"][idioma_atual])

    def bloquear_pausa_na_conversao(self):
        # Desativa o botão de pausa durante a mesclagem final do FFmpeg para evitar travamento de estado
        self.botao_pausar.setEnabled(False)
        self.atualizar_icones_controles()

    def set_progresso_ui(self, valor, texto):
        self.barra_progresso.setValue(int(valor))
        self.label_progresso.setText(texto)

    def iniciar_download(self, tipo):
        global url_atual, tipo_atual, formato_atual, caminho_salvamento_atual, estado_download

        url = self.entrada_url.text().strip()
        if not url or not url.startswith(("http://", "https://")):
            QMessageBox.warning(
                self,
                DICIONARIO_IDIOMAS["msg_aviso_titulo"][idioma_atual],
                DICIONARIO_IDIOMAS["msg_aviso_url"][idioma_atual]
            )
            return

        if tipo == 'audio':
            formato = self.dropdown_audio.currentText()
            botao_ativo = self.botao_baixar_audio
            nome_sugerido = f"audio.{formato}"
        else:
            formato = self.dropdown_video.currentText()
            botao_ativo = self.botao_baixar_video
            nome_sugerido = f"video.{formato}"

        # Filtro neutro para todos os idiomas e localização nativa da pasta Downloads
        filtro_arquivo = f"{formato.upper()} (*.{formato})"
        pasta_downloads = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        if not pasta_downloads or not os.path.exists(pasta_downloads):
            pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(pasta_downloads):
            pasta_downloads = os.path.expanduser('~')

        caminho_completo, _ = QFileDialog.getSaveFileName(
            self,
            DICIONARIO_IDIOMAS["msg_salvar_como"][idioma_atual],
            os.path.join(pasta_downloads, nome_sugerido),
            filtro_arquivo
        )

        if not caminho_completo:
            return

        if not caminho_completo.lower().endswith(f".{formato}"):
            caminho_completo += f".{formato}"

        # Se o usuário confirmou a substituição de um arquivo existente no diálogo, remove o antigo
        if os.path.exists(caminho_completo):
            try:
                os.remove(caminho_completo)
            except Exception as erro_rem:
                registrar_erro("remover_arquivo_existente", erro_rem)

        url_atual = url
        tipo_atual = tipo
        formato_atual = formato
        caminho_salvamento_atual = caminho_completo
        estado_download = "rodando"

        self.botao_baixar_audio.setEnabled(False)
        self.botao_baixar_video.setEnabled(False)
        botao_ativo.setText(DICIONARIO_IDIOMAS["btn_baixar_inativo"][idioma_atual])

        self.entrada_url.setReadOnly(True)
        self.container_progresso.show()

        self.botao_pausar.setEnabled(True)
        self.botao_continuar.setEnabled(False)
        self.botao_excluir.setEnabled(False)
        self.atualizar_icones_controles()

        self.set_progresso_ui(0, DICIONARIO_IDIOMAS["progresso_init"][idioma_atual])

        evento_cancelar = threading.Event()
        self._evento_cancelar_atual = evento_cancelar
        thread_antiga = self._thread_download
        nova_thread = threading.Thread(
            target=self.thread_download,
            args=(evento_cancelar, thread_antiga),
            daemon=True
        )
        self._thread_download = nova_thread
        nova_thread.start()

    def thread_download(self, evento_cancelar=None, thread_anterior=None):
        try:
            # Aguarda o encerramento completo da thread anterior antes de acessar o mesmo arquivo '.part'
            if thread_anterior is not None and thread_anterior.is_alive():
                thread_anterior.join(timeout=2.0)

            if evento_cancelar and evento_cancelar.is_set():
                return

            baixar_midia(
                url_atual,
                tipo_atual,
                formato_atual,
                hook_progresso=lambda d: self.atualizar_progresso(d, evento_cancelar),
                caminho_completo=caminho_salvamento_atual
            )
            if not (evento_cancelar and evento_cancelar.is_set()) and estado_download != "cancelado":
                self.sinais.sucesso.emit(tipo_atual, formato_atual)
        except DownloadPausado:
            pass
        except Exception as e:
            registrar_erro("thread_download", e)
            if not (evento_cancelar and evento_cancelar.is_set()) and estado_download != "cancelado":
                self.sinais.erro.emit(str(e))

    def finalizar_com_sucesso(self, tipo, formato):
        QMessageBox.information(
            self,
            DICIONARIO_IDIOMAS["msg_sucesso_titulo"][idioma_atual],
            DICIONARIO_IDIOMAS["msg_sucesso_texto"][idioma_atual]
        )
        self.restaurar_botoes()
        self.entrada_url.clear()

    def finalizar_com_erro(self, mensagem_erro):
        # Higieniza códigos ANSI, limita tamanho e força texto puro no diálogo de erro
        registrar_erro("finalizar_com_erro_ui", mensagem_erro)
        erro_limpo = RE_ANSI_ESCAPE.sub('', str(mensagem_erro)).strip()
        if len(erro_limpo) > 500:
            erro_limpo = erro_limpo[:500] + "..."

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(DICIONARIO_IDIOMAS["msg_erro_titulo"][idioma_atual])
        msg_box.setTextFormat(Qt.TextFormat.PlainText)
        msg_box.setText(f"{DICIONARIO_IDIOMAS['msg_erro_generico'][idioma_atual]}{erro_limpo}")
        msg_box.exec()
        self.restaurar_botoes()

    def restaurar_botoes(self):
        global estado_download
        estado_download = "parado"

        self.botao_baixar_audio.setEnabled(True)
        self.botao_baixar_video.setEnabled(True)
        self.botao_baixar_audio.setText(DICIONARIO_IDIOMAS["cor_botao_audio"][idioma_atual])
        self.botao_baixar_video.setText(DICIONARIO_IDIOMAS["cor_botao_video"][idioma_atual])

        self.container_progresso.hide()
        self.entrada_url.setReadOnly(False)

        self.botao_pausar.setEnabled(False)
        self.botao_continuar.setEnabled(False)
        self.botao_excluir.setEnabled(False)
        self.atualizar_icones_controles()

        # Coleta de lixo ativa para devolver memória RAM ao sistema imediatamente
        gc.collect()

    def acionar_pausa(self):
        global estado_download
        estado_download = "pausado"
        if self._evento_cancelar_atual:
            self._evento_cancelar_atual.set()

        self.botao_pausar.setEnabled(False)
        self.botao_continuar.setEnabled(True)
        self.botao_excluir.setEnabled(True)
        self.atualizar_icones_controles()

    def acionar_retomar(self):
        global estado_download
        estado_download = "rodando"

        self.botao_pausar.setEnabled(True)
        self.botao_continuar.setEnabled(False)
        self.botao_excluir.setEnabled(False)
        self.atualizar_icones_controles()

        evento_cancelar = threading.Event()
        self._evento_cancelar_atual = evento_cancelar
        thread_antiga = self._thread_download
        nova_thread = threading.Thread(
            target=self.thread_download,
            args=(evento_cancelar, thread_antiga),
            daemon=True
        )
        self._thread_download = nova_thread
        nova_thread.start()

    def _remover_arquivos_residuais(self):
        try:
            if not caminho_salvamento_atual:
                return
            base_nome = os.path.splitext(caminho_salvamento_atual)[0]
            arquivos_residuais = glob.glob(glob.escape(base_nome) + ".*")
            for arq in arquivos_residuais:
                if arq.endswith(".part") or arq.endswith(".ytdl") or arq.endswith(".temp"):
                    try:
                        os.remove(arq)
                    except Exception:
                        pass
        except Exception as erro_res:
            registrar_erro("remover_arquivos_residuais", erro_res)

    def acionar_excluir(self):
        global estado_download

        resposta = QMessageBox.question(
            self,
            DICIONARIO_IDIOMAS["msg_excluir_titulo"][idioma_atual],
            DICIONARIO_IDIOMAS["msg_excluir_texto"][idioma_atual],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            estado_download = "cancelado"
            if self._evento_cancelar_atual:
                self._evento_cancelar_atual.set()
            encerrar_processos_filhos()
            if self._thread_download and self._thread_download.is_alive():
                self._thread_download.join(timeout=1.0)
            self._remover_arquivos_residuais()
            self.restaurar_botoes()
            self.entrada_url.clear()


# -------------------------------
# --- Inicialização da Aplicação ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # O estilo 'Fusion' é desenhado pelo próprio Qt, então fica idêntico no Windows e no Linux
    # (sem ele, o Qt usa o estilo do sistema, como Breeze no KDE, Windows 11 no Windows, etc.)
    app.setStyle("Fusion")

    janela = JanelaCrimson()
    janela.show()
    sys.exit(app.exec())