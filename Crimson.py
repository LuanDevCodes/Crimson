# Projeto Crimson - Uma interface capaz de baixar vídeos de diversas plataformas de forma simples
# Criei esse projeto pela necessidade de uma ferramenta útil e confiável para tal, nascendo assim ele :D

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
import platform  # Detecta o sistema operacional para adaptar os caminhos
from PIL import Image  # Biblioteca 'Pillow', ajuda na manipulação de canais RGBA e recoloração dinâmica dos ícones

# Bibliotecas do PySide6 (Qt6) para uma interface gráfica moderna, com anti-aliasing nativo no Windows e Linux
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QProgressBar, QDialog, QTabWidget, QFrame, QMessageBox,
    QFileDialog, QMenu, QStyledItemDelegate
)
from PySide6.QtCore import Qt, QSize, Signal, QObject, QPointF
from PySide6.QtGui import (
    QIcon, QPixmap, QImage, QColor, QCursor, QAction,
    QPainter, QPen, QPainterPath, QPalette
)

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

# Cria as pastas caso elas não existam no computador desse usuário
os.makedirs(lib_dir, exist_ok=True)
os.makedirs(config_dir, exist_ok=True)

# --- Injeção de Dependência Modular ---
# Procura se o motor do yt-dlp já foi baixado na pasta Lib
# Se existir, forço o Python a ler as bibliotecas dessa pasta, ignorando bibliotecas nativas congeladas (PyInstaller)
path_yt_dlp = os.path.join(lib_dir, 'yt-dlp-master')

if os.path.exists(path_yt_dlp):
    sys.path.insert(0, path_yt_dlp)  # O insert 0 diz basicamente fala "olhe aqui antes de qualquer outro lugar"

import yt_dlp  # Agora sim ela é importada (Se a injeção existia, ele pegou a atualizada, senão, pegou a local como fallback)

# -------------------------------
# *******************************
# -------------------------------

# --- Funções de Leitura e Escrita do JSON ---
def carregar_configuracoes():
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass  # Se o arquivo estiver corrompido, só ignora e retorna o padrão
    return {"idioma": "Portuguese", "tema": "Dark"}

def salvar_configuracoes(idioma, tema):
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({"idioma": idioma, "tema": tema}, f, indent=4)
        return True
    except Exception:
        return False

# Dicionário global de configurações ativas
config_atual = carregar_configuracoes()
idioma_atual = config_atual.get("idioma", "Portuguese")
tema_atual = config_atual.get("tema", "Dark")

# Definindo cores em tons pastéis e superfícies modernas para manter a harmonia visual
TEMAS = {
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
        "cor_fundo_janela":             "#1C1E22",  # fundo grafite metálico / titânio
        "cor_card":                     "#272A30",  # placa metálica de platina
        "cor_borda_card":               "#3E444F",  # borda cromo escovado
        "cor_do_texto":                 "#F1F4F8",  # texto prata de alto contraste
        "cor_texto_secundario":         "#98A2B3",  # texto secundário estanho
        "cor_botao_audio":              "#475467",  # botão áudio aço escovado
        "cor_botao_audio_hover":        "#56657A",  # hover áudio
        "cor_botao_video":              "#536B88",  # botão vídeo platina metálica
        "cor_botao_video_hover":        "#637F9F",  # hover vídeo
        "cor_fonte_botoes":             "#FFFFFF",  # texto branco
        "cor_barra_de_pesquisa":        "#15171A",  # barra ferro escuro
        "cor_texto_caixa_de_pesquisa":  "#F1F4F8",  # texto barra
        "cor_de_fundo_dropdown":        "#2E333B",  # fundo dropdown
        "cor_do_hover_dropdown":        "#404652",  # hover dropdown
        "cor_da_borda_botao_video":     "#6B89AD",  # borda vídeo
        "cor_da_borda_botao_audio":     "#5D6D82",  # borda áudio
        "cor_do_texto_magua":           "#717D91",  # marca d'água
        "cor_progresso_fundo":          "#15171A",  # trilho
        "cor_progresso_barra":          "#7E99B8"   # preenchimento platina lustrosa
    }
}

IDIOMAS_SUPORTADOS = [
    "Portuguese",
    "English",
    "Spanish",
    "Chinese",
    "Japanese",
    "Korean",
    "Russian",
    "Ukrainian",
    "Indonesian",
    "Filipino",
    "Vietnamese",
    "Norwegian",
    "Hausa",
    "Bambara",
    "Latin"
]

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
        "Latin": "Securitatis renovatio quaeritur..."
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
        "Latin": "Inscriptionem (URL) cinematographi insere:"
    },
    "placeholder_url": {
        "Portuguese": "Cole aqui o link do vídeo ou música",
        "English": "Paste the video or music link here",
        "Spanish": "Pega aquí el enlace del vídeo o música",
        "Chinese": "在此粘贴视频或音乐链接",
        "Japanese": "動画または音楽のリンクをここに貼り付け",
        "Korean": "동영상 또는 음악 링크를 여기에 붙여넣으세요",
        "Russian": "Вставьте ссылку на видео или музыку",
        "Ukrainian": "Вставте посилання на відео або музику",
        "Indonesian": "Tempel tautan video atau musik di sini",
        "Filipino": "I-paste dito ang link ng video o musika",
        "Vietnamese": "Dán liên kết video hoặc âm nhạc vào đây",
        "Norwegian": "Lim inn lenken til video eller musikk her",
        "Hausa": "Manna mahadar bidiyo ko kiɗa a nan",
        "Bambara": "Wideyo walima dɔnkili sirilen bila yan",
        "Latin": "Hic nexum cinematographi vel soni insere"
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
        "Latin": "SONUS"
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
        "Latin": "VISIO"
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
        "Latin": "Sonum Depromere"
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
        "Latin": "Visionem Depromere"
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
        "Latin": "Systema"
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
        "Latin": "De Hoc"
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
        "Latin": "Applicatio Lingua:"
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
        "Latin": "Forma Argumenti:"
    },
    "lbl_versao": {
        "Portuguese": "Versão atual: V.2.3.0",
        "English": "Current version: V.2.3.0",
        "Spanish": "Versión actual: V.2.3.0",
        "Chinese": "当前版本：V.2.3.0",
        "Japanese": "現在のバージョン: V.2.3.0",
        "Korean": "현재 버전: V.2.3.0",
        "Russian": "Текущая версия: V.2.3.0",
        "Ukrainian": "Поточна версія: V.2.3.0",
        "Indonesian": "Versi saat ini: V.2.3.0",
        "Filipino": "Kasalukuyang bersyon: V.2.3.0",
        "Vietnamese": "Phiên bản hiện tại: V.2.3.0",
        "Norwegian": "Gjeldende versjon: V.2.3.0",
        "Hausa": "Fasalin yanzu: V.2.3.0",
        "Bambara": "Sisan kɔnɔko: V.2.3.0",
        "Latin": "Editio currens: V.2.3.0"
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
        "Latin": "Sine quaestu mercatorio creatum\nOmnis distributio gratuita ac libera\nomnibus esse debet"
    },
    "lbl_creditos": {
        "Portuguese": "Créditos e agradecimentos à comunidade Open Source",
        "English": "Credits and thanks to the Open Source community",
        "Spanish": "Créditos y agradecimientos a la comunidad Open Source",
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
        "Latin": "Gratiae et laus communitati Open Source"
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
        "Latin": "  Repositorium Crimson"
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
        "Latin": "  Repositorium yt-dlp"
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
        "Latin": "  Repositorium FFmpeg"
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
        "Latin": "Suggesta Fulta"
    },
    "plataformas_texto": {
        "Portuguese": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "English": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Spanish": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Chinese": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Japanese": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Korean": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Russian": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Ukrainian": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Indonesian": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Filipino": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Vietnamese": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Norwegian": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Hausa": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Bambara": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili",
        "Latin": "• YouTube\n • Vimeo\n • Dailymotion\n • Facebook\n • Instagram\n • Twitter / X\n • TikTok\n • Twitch\n • SoundCloud\n • Reddit\n • LinkedIn\n • Pinterest\n • VK\n • Bilibili"
    },
    "plataformas_aviso": {
        "Portuguese": "Aviso: O motor que Crimson utiliza possui suporte nativo para esses sites.\nNo entanto, a disponibilidade e estabilidade podem variar segundo as regras de cada plataforma.",
        "English": "Warning: The Crimson engine supports these sites natively.\nHowever, availability and stability may vary according to each platform's rules.",
        "Spanish": "Aviso: El motor utilizado por Crimson tiene compatibilidad nativa con estos sitios.\nSin embargo, la disponibilidad y estabilidad pueden variar según las normas de cada plataforma.",
        "Chinese": "提示：Crimson 使用的引擎原生支持这些网站。\n但可用性和稳定性可能因各平台规则而有所不同。",
        "Japanese": "注意: Crimson エンジンはこれらのサイトをネイティブにサポートしています。\nただし、各プラットフォームの規約により可用性や安定性が異なる場合があります。",
        "Korean": "알림: Crimson 엔진은 이러한 사이트를 기본적으로 지원합니다.\n단, 가용성과 안정성은 각 플랫폼의 정책에 따라 달라질 수 있습니다.",
        "Russian": "Примечание: Движок Crimson нативно поддерживает эти сайты.\nОднако стабильность может зависеть от правил каждой платформы.",
        "Ukrainian": "Примітка: Двигун Crimson має нативну підтримку цих сайтів.\nПроте доступність і стабільність можуть залежати від правил кожної платформи.",
        "Indonesian": "Pemberitahuan: Mesin Crimson mendukung situs-situs ini secara bawaan.\nNamun, ketersediaan dan stabilitas dapat berbeda tergantung aturan platform.",
        "Filipino": "Paunawa: Katutubong sinusuportahan ng Crimson engine ang mga site na ito.\nGayunpaman, maaaring mag-iba ang availability at katatagan ayon sa mga patakaran ng bawat platform.",
        "Vietnamese": "Lưu ý: Công cụ Crimson hỗ trợ các trang web này nguyên bản.\nTuy nhiên, tính khả dụng và độ ổn định có thể thay đổi theo quy định của từng nền tảng.",
        "Norwegian": "Merk: Crimson-motoren støtter disse nettstedene.\nTilgjengelighet og stabilitet kan imidlertid variere etter plattformenes regler.",
        "Hausa": "Sanarwa: Injin Crimson yana tallafawa waɗannan shafuka kai tsaye.\nDuk da haka, samuwa da karko na iya bambanta bisa ƙa'idodin kowane dandali.",
        "Bambara": "Kɔlɔsili: Crimson masini bɛ dɛmɛ di nin sitiw la cogo bɛɛ la.\nNka a sɔrɔli bɛ se ka caman yɛlɛma kɛɲɛ ni sitiw ka sariyaw ye.",
        "Latin": "Monitum: Instrumentum Crimson haec loca indigenice sustinet.\nAttamen stabilitas secundum cuiusque loci regulas mutari potest."
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
        "Latin": "A LuanDevCodes elaboratum"
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
        "Latin": "Feliciter"
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
        "Latin": "Deportatio atque conversio feliciter perfecta est"
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
        "Latin": "Error"
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
        "Latin": "Error quidam in deponendo accidit:\n"
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
        "Latin": "Monitum"
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
        "Latin": "Quaesumus, validam inscriptionem (URL) insere"
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
        "Latin": "Depromens"
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
        "Latin": "Velocitas"
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
        "Latin": "Tempus residuum"
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
        "Latin": "Deportatio incipitur..."
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
        "Latin": "Depromptum - Conversio exspectatur (FFmpeg)..."
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
        "Latin": "Parans..."
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
        "Latin": "Deportationem Delere"
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
        "Latin": "Certusne es te velle hanc deportationem abrumpere ac delere?"
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
        "Latin": "Servare sub nomine..."
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
        "Latin": "Glutinare"
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
        "Latin": "Delere"
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
        "Latin": "Processus umbraticos delere"
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
        "Latin": "Processuum Purgatio"
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
        "Latin": "Certusne es te velle processus posticos applicationis finire?"
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
        "Latin": "Feliciter"
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
        "Latin": "Processus posteriores finiti sunt"
    },
    "btn_salvar_config": {
        "Portuguese": "Salvar e Aplicar",
        "English": "Save & Apply",
        "Spanish": "Guardar y Aplicar",
        "Chinese": "保存并应用",
        "Japanese": "保存して適用",
        "Korean": "저장 및 적용",
        "Russian": "Сохранить и применить",
        "Ukrainian": "Зберегти та застосувати",
        "Indonesian": "Simpan & Terapkan",
        "Filipino": "I-save at Ilapat",
        "Vietnamese": "Lưu và Áp dụng",
        "Norwegian": "Lagre og bruk",
        "Hausa": "Ajiye kuma Aiwatar",
        "Bambara": "A mara k'a labaara",
        "Latin": "Servare et Adhibere"
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
        "Latin": "Confirmare"
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
        "Latin": "Certusne es te optata hodierna servare velle?"
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
        "Latin": "Optata feliciter servata sunt"
    }
}

# -------------------------------
# *******************************
# -------------------------------

caminho_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
caminho_icons = os.path.join(caminho_base, "Icons")

# No Windows, uso o ffmpeg local que fica na pasta 'ffmpeg/' do projeto
# No Linux, o ffmpeg já fica instalado no sistema (/usr/bin/ffmpeg), então não precisamos de pasta local
if SISTEMA == 'Windows':
    caminho_ffmpeg_dir = os.path.join(caminho_base, 'ffmpeg')
    os.environ["PATH"] = os.environ["PATH"] + os.pathsep + caminho_ffmpeg_dir
else:
    # No Linux o ffmpeg fica em /usr/bin — o yt-dlp vai achá-lo automaticamente pelo PATH do sistema
    caminho_ffmpeg_dir = '/usr/bin'

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

def baixar_midia_youtube(url, tipo, formato, hook_progresso, caminho_completo):
    # Configurações base de Download (ydl_opts)
    ydl_opts = {
        # Define o caminho exato de saída já com nome e extensão que o usuário escolheu
        'outtmpl': caminho_completo,

        # Conecta a função da nossa barra de progresso no sistema do yt-dlp
        'progress_hooks': [hook_progresso],

        # Indica para o yt-dlp onde encontrar o executável do ffmpeg
        'ffmpeg_location': caminho_ffmpeg_dir,

        # Mostra o progresso no console
        'quiet': False,
        'no_warnings': True,

        # Desativa códigos de cores (ANSI) para que o texto da barra de progresso fique limpo
        'color': 'no_color',

        # Bypasses para evitar limitador de velocidade do YouTube (Throttling) e compensar o uso do módulo puro
        'concurrent_fragment_downloads': 5,  # Usa 5 conexões simultâneas para baixar os pedaços
        'http_chunk_size': 10485760,         # Divide em blocos de 10MB para download rápido
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

    print(f"[*] Preparando para baixar ({tipo} - {formato}): {url}")

    # Inicializa o yt-dlp com as configurações preparadas e dispara o download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print(f"[*] Download concluído - Verifique a pasta '{caminho_salvamento_atual}'")


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

        # O delegate padrão do QComboBox ignora as regras '::item' do stylesheet (hover, altura, cantos)
        # Com o QStyledItemDelegate, a lista passa a obedecer o visual definido em estilo_lista_dropdown()
        self.setItemDelegate(QStyledItemDelegate(self))

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

def estilo_lista_dropdown(cor):
    
    """
    Estilo da lista aberta dos dropdowns, compartilhado pela janela principal e pela de Configurações
    """
    
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
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                color: {cor["cor_do_texto"]};
                min-height: 26px;
                padding: 0px 8px;
                border-radius: 6px;
            }}
            QComboBox QAbstractItemView::item:hover,
            QComboBox QAbstractItemView::item:selected {{
                background-color: {cor["cor_do_hover_dropdown"]};
                color: {cor["cor_do_texto"]};
            }}
    """

# --------------------------------------------------------------------------------------------------------------------
# --- Ponte de Sinais Assíncronos (Thread-Safe UI Updates) ---
# --------------------------------------------------------------------------------------------------------------------

class SinaisDownload(QObject):

    """
    No Qt (PySide6), threads em segundo plano não devem alterar widgets diretamente
    Esses sinais enviam os eventos com segurança para a thread principal da interface
    """

    progresso = Signal(float, str)
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

        # Card que agrupa as plataformas em formato de tags/badges modernos
        self.card_plataformas = QFrame()
        self.card_plataformas.setObjectName("cardInterno")
        grid_plat = QGridLayout(self.card_plataformas)
        grid_plat.setContentsMargins(16, 16, 16, 16)
        grid_plat.setSpacing(10)

        plataformas = [
            "YouTube", "Vimeo", "Dailymotion", "Facebook",
            "Instagram", "Twitter / X", "TikTok", "Twitch",
            "SoundCloud", "Reddit", "LinkedIn", "Pinterest",
            "VK", "Bilibili"
        ]

        self.badges_plataformas = []
        for idx, nome in enumerate(plataformas):
            badge = QLabel(f"• {nome}")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setObjectName("badgePlataforma")
            badge.setMinimumHeight(32)
            grid_plat.addWidget(badge, idx // 3, idx % 3)
            self.badges_plataformas.append(badge)

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
        self.lbl_aviso.setText(DICIONARIO_IDIOMAS["plataformas_aviso"][idioma_atual])

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {cor["cor_fundo_janela"]};
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
                background-color: {cor["cor_card"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 14px;
            }}
            QLabel#badgePlataforma {{
                background-color: {cor["cor_fundo_janela"]};
                color: {cor["cor_do_texto"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 8px;
                padding: 4px 10px;
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: 600;
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
        self.dropdown_tema.addItems(list(TEMAS.keys()))
        self.dropdown_tema.setCurrentText(tema_atual)
        self.dropdown_tema.setFixedWidth(190)
        self.dropdown_tema.setFixedHeight(38)
        self.dropdown_tema.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout_prefs.addWidget(self.dropdown_tema, alignment=Qt.AlignmentFlag.AlignCenter)

        layout_sistema.addWidget(self.card_prefs)
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
                if SISTEMA == 'Windows':
                    subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["pkill", "-f", "ffmpeg"], capture_output=True)

                gc.collect()

                QMessageBox.information(
                    self,
                    DICIONARIO_IDIOMAS["msg_sucesso_limpeza_titulo"][idioma_atual],
                    DICIONARIO_IDIOMAS["msg_sucesso_limpeza_texto"][idioma_atual]
                )
            except Exception:
                pass

    def confirmar_e_salvar(self):
        global idioma_atual, tema_atual

        novo_idioma = self.dropdown_idioma.currentText()
        novo_tema = self.dropdown_tema.currentText()

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

            salvar_configuracoes(idioma_atual, tema_atual)

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

        self.setStyleSheet(f"""
            QDialog, QWidget {{
                background-color: {cor["cor_fundo_janela"]};
            }}
            QLabel {{
                background: transparent;
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {cor["cor_fundo_janela"]};
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background-color: {cor["cor_card"]};
                color: {cor["cor_texto_secundario"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 9px;
                padding: 8px 28px;
                margin: 0px 4px;
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {cor["cor_botao_video"]};
                color: {cor["cor_fonte_botoes"]};
                border: 1px solid {cor["cor_da_borda_botao_video"]};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {cor["cor_do_hover_dropdown"]};
                color: {cor["cor_do_texto"]};
            }}
            QFrame#cardInterno {{
                background-color: {cor["cor_card"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 14px;
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
                background-color: {cor["cor_botao_audio"]};
                color: {cor["cor_fonte_botoes"]};
                border: 1px solid {cor["cor_da_borda_botao_audio"]};
                border-radius: 8px;
                padding: 4px 30px 4px 14px;
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QComboBox:hover {{
                background-color: {cor["cor_botao_audio_hover"]};
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
                background-color: {cor["cor_botao_audio"]};
                color: {cor["cor_fonte_botoes"]};
                border: 1px solid {cor["cor_da_borda_botao_audio"]};
                border-radius: 10px;
                padding: 8px 18px;
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#botaoSecundario:hover {{
                background-color: {cor["cor_botao_audio_hover"]};
            }}
            QPushButton#botaoPrimario {{
                background-color: {cor["cor_botao_video"]};
                color: {cor["cor_fonte_botoes"]};
                border: 1px solid {cor["cor_da_borda_botao_video"]};
                border-radius: 10px;
                padding: 8px 22px;
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#botaoPrimario:hover {{
                background-color: {cor["cor_botao_video_hover"]};
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
# --- Janela Principal do Aplicativo (Crimson) ---
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
        self.sinais.sucesso.connect(self.finalizar_com_sucesso)
        self.sinais.erro.connect(self.finalizar_com_erro)
        self.sinais.loading_concluido.connect(self.finalizar_loading)

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
        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_raiz = QVBoxLayout(widget_central)
        layout_raiz.setContentsMargins(26, 20, 26, 20)
        layout_raiz.setSpacing(14)

        # ------------------------------------------------------------------
        # --- Barra Superior (Configurações | Instrução | Plataformas) ---
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

        layout_raiz.addLayout(layout_topo)

        # ------------------------------------------------------------------
        # --- Barra de Carregamento Inicial (Auto-Update yt-dlp) ---
        self.barra_loading = QProgressBar()
        self.barra_loading.setObjectName("barraProgresso")
        self.barra_loading.setRange(0, 0)  # Modo indeterminado (animação contínua)
        self.barra_loading.setFixedHeight(10)
        self.barra_loading.setFixedWidth(360)
        self.barra_loading.setTextVisible(False)
        layout_raiz.addWidget(self.barra_loading, alignment=Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------------------------------
        # --- Campo de Entrada da URL ---
        self.entrada_url = QLineEdit()
        self.entrada_url.setObjectName("entradaUrl")
        self.entrada_url.setFixedHeight(44)
        self.entrada_url.setPlaceholderText(DICIONARIO_IDIOMAS["placeholder_url"][idioma_atual])
        self.entrada_url.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.entrada_url.customContextMenuRequested.connect(self.exibir_menu_contexto)
        layout_raiz.addWidget(self.entrada_url)

        # ------------------------------------------------------------------
        # --- Seção de Cards (Áudio e Vídeo lado a lado) ---
        self.container_acoes = QWidget()
        layout_cards = QHBoxLayout(self.container_acoes)
        layout_cards.setContentsMargins(0, 2, 0, 2)
        layout_cards.setSpacing(18)

        # --- Card de Áudio ---
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

        # --- Card de Vídeo ---
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

        layout_raiz.addWidget(self.container_acoes)

        # ------------------------------------------------------------------
        # --- Barra de Progresso e Status do Download ---
        self.container_progresso = QWidget()
        layout_progresso = QVBoxLayout(self.container_progresso)
        layout_progresso.setContentsMargins(0, 2, 0, 0)
        layout_progresso.setSpacing(6)

        self.barra_progresso = QProgressBar()
        self.barra_progresso.setObjectName("barraProgresso")
        self.barra_progresso.setRange(0, 100)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setFixedHeight(10)
        self.barra_progresso.setTextVisible(False)
        layout_progresso.addWidget(self.barra_progresso)

        self.label_progresso = QLabel("")
        self.label_progresso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_progresso.setObjectName("labelProgresso")
        layout_progresso.addWidget(self.label_progresso)

        self.container_progresso.hide()
        layout_raiz.addWidget(self.container_progresso)

        layout_raiz.addStretch(1)

        # ------------------------------------------------------------------
        # --- Controles de Execução (Pausar, Continuar, Excluir) ---
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

        layout_raiz.addWidget(self.frame_controles, alignment=Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------
    # --- Menu de Contexto (Botão Direito na Barra de URL) ---
    def exibir_menu_contexto(self, posicao):
        if self.entrada_url.isReadOnly():
            return

        menu = QMenu(self)
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
        if self.barra_loading.isVisible():
            self.label_instrucao.setText(DICIONARIO_IDIOMAS["instrucao_init"][idioma_atual])
        else:
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
        self.atualizar_icones_controles()
        self.dropdown_audio.update()
        self.dropdown_video.update()

        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {cor["cor_fundo_janela"]};
                font-family: 'Segoe UI', 'Ubuntu', 'Arial', sans-serif;
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
                background-color: {cor["cor_card"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 10px;
            }}
            QPushButton#botaoIconeTopo:hover {{
                background-color: {cor["cor_do_hover_dropdown"]};
            }}
            QLineEdit#entradaUrl {{
                background-color: {cor["cor_barra_de_pesquisa"]};
                color: {cor["cor_texto_caixa_de_pesquisa"]};
                border: 1.5px solid {cor["cor_borda_card"]};
                border-radius: 11px;
                padding: 0px 16px;
                font-size: 14px;
                selection-background-color: {cor["cor_botao_video"]};
                selection-color: {cor["cor_fonte_botoes"]};
            }}
            QLineEdit#entradaUrl:focus {{
                border: 1.5px solid {cor["cor_botao_video"]};
            }}
            QFrame#cardAcao {{
                background-color: {cor["cor_card"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 14px;
            }}
            QLabel#tituloCard {{
                color: {cor["cor_texto_secundario"]};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QComboBox#dropdownAudio {{
                background-color: {cor["cor_botao_audio"]};
                color: {cor["cor_fonte_botoes"]};
                border: 1px solid {cor["cor_da_borda_botao_audio"]};
                border-radius: 9px;
                padding: 4px 24px 4px 10px;
                font-size: 12px;
                font-weight: bold;
            }}
            QComboBox#dropdownAudio:hover {{
                background-color: {cor["cor_botao_audio_hover"]};
            }}
            QComboBox#dropdownVideo {{
                background-color: {cor["cor_botao_video"]};
                color: {cor["cor_fonte_botoes"]};
                border: 1px solid {cor["cor_da_borda_botao_video"]};
                border-radius: 9px;
                padding: 4px 24px 4px 10px;
                font-size: 12px;
                font-weight: bold;
            }}
            QComboBox#dropdownVideo:hover {{
                background-color: {cor["cor_botao_video_hover"]};
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
                background-color: {cor["cor_botao_audio"]};
                color: {cor["cor_fonte_botoes"]};
                border: 1px solid {cor["cor_da_borda_botao_audio"]};
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#botaoAudio:hover:enabled {{
                background-color: {cor["cor_botao_audio_hover"]};
            }}
            QPushButton#botaoVideo {{
                background-color: {cor["cor_botao_video"]};
                color: {cor["cor_fonte_botoes"]};
                border: 1px solid {cor["cor_da_borda_botao_video"]};
                border-radius: 9px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton#botaoVideo:hover:enabled {{
                background-color: {cor["cor_botao_video_hover"]};
            }}
            QProgressBar#barraProgresso {{
                background-color: {cor["cor_progresso_fundo"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 5px;
            }}
            QProgressBar#barraProgresso::chunk {{
                background-color: {cor["cor_progresso_barra"]};
                border-radius: 4px;
            }}
            QLabel#labelProgresso {{
                color: {cor["cor_do_texto"]};
                font-size: 12px;
                font-weight: 500;
            }}
            QFrame#cardControles {{
                background-color: {cor["cor_card"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 14px;
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
                background-color: {cor["cor_card"]};
                color: {cor["cor_do_texto"]};
                border: 1px solid {cor["cor_borda_card"]};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 22px;
                border-radius: 5px;
            }}
            QMenu::item:selected {{
                background-color: {cor["cor_botao_video"]};
                color: {cor["cor_fonte_botoes"]};
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

    # ------------------------------------------------------------------
    # --- Lógica da Tela de Carregamento (Update Inicial) ---
    def iniciar_loading_atualizacao(self):
        self.botao_config.hide()
        self.botao_plataformas.hide()
        self.entrada_url.hide()
        self.container_acoes.hide()
        self.frame_controles.hide()
        self.label_instrucao.setText(DICIONARIO_IDIOMAS["instrucao_init"][idioma_atual])
        self.barra_loading.show()

        threading.Thread(target=self.thread_atualizacao_inicial, daemon=True).start()

    def thread_atualizacao_inicial(self):
        try:
            print("[*] Verificando atualizações de segurança (Motor yt-dlp)")
            url_master = "https://github.com/yt-dlp/yt-dlp/archive/refs/heads/master.zip"
            caminho_zip = os.path.join(lib_dir, "yt-dlp-master.zip")

            req = urllib.request.Request(url_master, headers={'User-Agent': 'Mozilla/5.0 (Crimson-Downloader)'})
            with urllib.request.urlopen(req, timeout=5) as response, open(caminho_zip, 'wb') as out_file:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    out_file.write(chunk)

            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(lib_dir)

            os.remove(caminho_zip)

            path_extraido = os.path.join(lib_dir, "yt-dlp-master")
            if path_extraido not in sys.path:
                sys.path.insert(0, path_extraido)

            print("[*] Motor atualizado e injetado - Interface pronta")
        except Exception as e:
            print(f"[*] Não foi possível atualizar o motor online: {e}")
        finally:
            self.sinais.loading_concluido.emit()

    def finalizar_loading(self):
        self.barra_loading.hide()
        self.label_instrucao.setText(DICIONARIO_IDIOMAS["instrucao_ready"][idioma_atual])
        self.botao_config.show()
        self.botao_plataformas.show()
        self.entrada_url.show()
        self.container_acoes.show()
        self.frame_controles.show()

    # ------------------------------------------------------------------
    # --- Lógica de Download, Progresso e Controles ---
    def atualizar_progresso(self, d):
        global estado_download

        if estado_download == "pausado":
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
                percentual_limpo = RE_ANSI_ESCAPE.sub('', percentual_str).replace('%', '')
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
            self.sinais.progresso.emit(100.0, DICIONARIO_IDIOMAS["progresso_convertendo"][idioma_atual])

    def set_progresso_ui(self, valor, texto):
        self.barra_progresso.setValue(int(valor))
        self.label_progresso.setText(texto)

    def iniciar_download(self, tipo):
        global url_atual, tipo_atual, formato_atual, caminho_salvamento_atual, estado_download

        url = self.entrada_url.text().strip()
        if not url:
            QMessageBox.warning(
                self,
                DICIONARIO_IDIOMAS["msg_aviso_titulo"][idioma_atual],
                DICIONARIO_IDIOMAS["msg_aviso_url"][idioma_atual]
            )
            return

        if tipo == 'audio':
            formato = self.dropdown_audio.currentText()
            botao_ativo = self.botao_baixar_audio
        else:
            formato = self.dropdown_video.currentText()
            botao_ativo = self.botao_baixar_video

        filtro_arquivo = f"Arquivo {formato.upper()} (*.{formato})"
        pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')

        caminho_completo, _ = QFileDialog.getSaveFileName(
            self,
            DICIONARIO_IDIOMAS["msg_salvar_como"][idioma_atual],
            os.path.join(pasta_downloads, f"video.{formato}"),
            filtro_arquivo
        )

        if not caminho_completo:
            return

        if not caminho_completo.lower().endswith(f".{formato}"):
            caminho_completo += f".{formato}"

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

        threading.Thread(target=self.thread_download, daemon=True).start()

    def thread_download(self):
        try:
            baixar_midia_youtube(
                url_atual,
                tipo_atual,
                formato_atual,
                hook_progresso=self.atualizar_progresso,
                caminho_completo=caminho_salvamento_atual
            )
            if estado_download == "rodando":
                self.sinais.sucesso.emit(tipo_atual, formato_atual)
        except DownloadPausado:
            pass
        except Exception as e:
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
        QMessageBox.critical(
            self,
            DICIONARIO_IDIOMAS["msg_erro_titulo"][idioma_atual],
            f"{DICIONARIO_IDIOMAS['msg_erro_generico'][idioma_atual]}{mensagem_erro}"
        )
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

        threading.Thread(target=self.thread_download, daemon=True).start()

    def acionar_excluir(self):
        global estado_download, caminho_salvamento_atual

        resposta = QMessageBox.question(
            self,
            DICIONARIO_IDIOMAS["msg_excluir_titulo"][idioma_atual],
            DICIONARIO_IDIOMAS["msg_excluir_texto"][idioma_atual],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            estado_download = "parado"
            self.restaurar_botoes()
            self.entrada_url.clear()

            try:
                base_nome = os.path.splitext(caminho_salvamento_atual)[0]
                arquivos_residuais = glob.glob(base_nome + ".*")
                for arq in arquivos_residuais:
                    if arq.endswith(".part") or arq.endswith(".ytdl"):
                        try:
                            os.remove(arq)
                        except Exception:
                            pass
            except Exception:
                pass


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