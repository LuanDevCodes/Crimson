# Projeto Crimson - Janela principal do aplicativo e ponte de sinais entre threads e interface
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import os               # Biblioteca para interagir com o sistema operacional (navegar entre pastas, verificar se um arquivo existe, criar pastas e ler variáveis)
import sys              # Necessário para ajustar o caminho de importação ao carregar o motor yt-dlp atualizado
import glob             # Para manipulação dos caminhos dos arquivos, além de ajudar na exclusão dos arquivos residuais
import threading        # Biblioteca para criar rotinas em segundo plano (evita que a tela trave)
import time             # Controle de intervalos e throttling para manter a UI leve
import gc               # Coleta de lixo forçada para liberar memória imediatamente em máquinas modestas
import re               # Usado para limpar textos gerados pelo yt-dlp
import urllib.request   # Biblioteca nativa para baixar arquivos da internet
import zipfile          # Biblioteca nativa para extrair arquivos compactados
import shutil           # Usado para limpeza segura de pastas temporárias e localização de binários no sistema
import importlib        # Permite recarregar o motor yt-dlp em memória após atualização sem reiniciar o app

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QFrame, QMessageBox,
    QFileDialog, QMenu
)
from PySide6.QtCore import Qt, QSize, Signal, QObject, QEvent, QStandardPaths
from PySide6.QtGui import QIcon, QCursor, QAction

from crimson import VERSAO_APP
from crimson.config import EM_FLATPAK, lib_dir, temp_dir, registrar_erro
from crimson.estado import estado
from crimson.temas import TEMAS, aplicar_paleta_global, estilo_lista_dropdown
from crimson.idiomas import DICIONARIO_IDIOMAS
from crimson.icones import caminho_icons, carregar_icone_tematico
from crimson.motor import yt_dlp, DownloadPausado, baixar_midia, encerrar_processos_filhos
from crimson.widgets import ComboBoxModerno, BarraProgressoModerna, WidgetFundoCrimson
from crimson.dialogos import DialogoPlataformas, DialogoConfiguracoes

# Expressões regulares pré-compiladas para evitar overhead de compilação em loops de alta frequência
RE_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[mK]')
RE_ESPACO_VELOCIDADE = re.compile(r'(?<=\d)(?=[a-zA-Z])')

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

        # Últimos valores válidos de velocidade e tempo restante (o yt-dlp às vezes informa 'Unknown' no meio do download)
        self._ultima_velocidade = "--"
        self._ultimo_eta = "--"

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

        self.label_loading = QLabel(DICIONARIO_IDIOMAS["instrucao_init"][estado.idioma_atual])
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

        self.label_instrucao = QLabel(DICIONARIO_IDIOMAS["instrucao_ready"][estado.idioma_atual])
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
        self.entrada_url.setPlaceholderText(DICIONARIO_IDIOMAS["placeholder_url"][estado.idioma_atual])
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

        self.lbl_card_audio = QLabel(DICIONARIO_IDIOMAS["titulo_card_audio"][estado.idioma_atual])
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

        self.botao_baixar_audio = QPushButton(DICIONARIO_IDIOMAS["cor_botao_audio"][estado.idioma_atual])
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

        self.lbl_card_video = QLabel(DICIONARIO_IDIOMAS["titulo_card_video"][estado.idioma_atual])
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

        self.botao_baixar_video = QPushButton(DICIONARIO_IDIOMAS["cor_botao_video"][estado.idioma_atual])
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
        acao_colar = QAction(DICIONARIO_IDIOMAS["menu_colar"][estado.idioma_atual], self)
        acao_colar.triggered.connect(self.entrada_url.paste)
        menu.addAction(acao_colar)

        acao_apagar = QAction(DICIONARIO_IDIOMAS["menu_apagar"][estado.idioma_atual], self)
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
        cor_icone = TEMAS[estado.tema_atual]["cor_do_texto"]

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
        self.label_loading.setText(DICIONARIO_IDIOMAS["instrucao_init"][estado.idioma_atual])
        self.label_instrucao.setText(DICIONARIO_IDIOMAS["instrucao_ready"][estado.idioma_atual])
        self.entrada_url.setPlaceholderText(DICIONARIO_IDIOMAS["placeholder_url"][estado.idioma_atual])
        self.lbl_card_audio.setText(DICIONARIO_IDIOMAS["titulo_card_audio"][estado.idioma_atual])
        self.lbl_card_video.setText(DICIONARIO_IDIOMAS["titulo_card_video"][estado.idioma_atual])

        if estado.estado_download == "parado":
            self.botao_baixar_audio.setText(DICIONARIO_IDIOMAS["cor_botao_audio"][estado.idioma_atual])
            self.botao_baixar_video.setText(DICIONARIO_IDIOMAS["cor_botao_video"][estado.idioma_atual])

        if self.dialogo_plataformas and self.dialogo_plataformas.isVisible():
            self.dialogo_plataformas.atualizar_textos_e_tema()

    def aplicar_tema(self):
        cor = TEMAS[estado.tema_atual]
        aplicar_paleta_global(cor)  # Garante que pop-ups e diálogos sigam o tema (e não o tema do sistema)
        self.widget_central.sincronizar_tema()
        self.barra_loading.sincronizar_animacao()
        self.atualizar_icones_controles()
        self.dropdown_audio.update()
        self.dropdown_video.update()
        self.barra_loading.update()
        self.barra_progresso.update()

        if estado.tema_atual == "Frutiger Aero":
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
        elif estado.tema_atual == "Platinum Disc":
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
            hover_bg_menu = cor["cor_botao_audio"] if estado.tema_atual in ("Dark", "Matcha") else cor["cor_botao_video"]
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
        # Proteção ao fechar a janela durante um download ativo para evitar processos órfãos
        if estado.estado_download in ("rodando", "pausado"):
            resposta = QMessageBox.question(
                self,
                DICIONARIO_IDIOMAS["msg_excluir_titulo"][estado.idioma_atual],
                DICIONARIO_IDIOMAS["msg_excluir_texto"][estado.idioma_atual],
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resposta != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            estado.estado_download = "cancelado"
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

        # No Flatpak, as atualizações são gerenciadas pela própria loja (Flathub), abrindo a interface instantaneamente
        if EM_FLATPAK:
            self.finalizar_loading()
            return

        self.container_principal.hide()
        self.label_loading.setText(DICIONARIO_IDIOMAS["instrucao_init"][estado.idioma_atual])
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
        self.label_instrucao.setText(DICIONARIO_IDIOMAS["instrucao_ready"][estado.idioma_atual])
        self.container_principal.show()

    # ------------------------------------------------------------------
    # --- Lógica de Download, Progresso e Controles ---
    def atualizar_progresso(self, d, evento_cancelar=None):

        if estado.estado_download in ("pausado", "cancelado") or (evento_cancelar and evento_cancelar.is_set()):
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

                # O yt-dlp escreve 'Unknown' enquanto ainda não consegue calcular velocidade/tempo (comum ao iniciar,
                # ao retomar e em vídeos baixados em fragmentos), nesses momentos mantém o último valor válido na tela
                if 'Unknown' in velocidade or velocidade in ('N/A', ''):
                    velocidade = self._ultima_velocidade
                else:
                    self._ultima_velocidade = velocidade
                if 'Unknown' in eta or eta in ('N/A', ''):
                    eta = self._ultimo_eta
                else:
                    self._ultimo_eta = eta

                texto = (
                    f"{DICIONARIO_IDIOMAS['progresso_baixando'][estado.idioma_atual]}: {percentual_float:.1f}%   |   "
                    f"{DICIONARIO_IDIOMAS['progresso_vel'][estado.idioma_atual]}: {velocidade}   |   "
                    f"{DICIONARIO_IDIOMAS['progresso_tempo'][estado.idioma_atual]}: {eta}"
                )
                self.sinais.progresso.emit(percentual_float, texto)
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.sinais.etapa_conversao.emit()
            self.sinais.progresso.emit(100.0, DICIONARIO_IDIOMAS["progresso_convertendo"][estado.idioma_atual])

    def bloquear_pausa_na_conversao(self):
        # Desativa o botão de pausa durante a mesclagem final do FFmpeg para evitar travamento de estado
        self.botao_pausar.setEnabled(False)
        self.atualizar_icones_controles()

    def set_progresso_ui(self, valor, texto):
        self.barra_progresso.setValue(int(valor))
        self.label_progresso.setText(texto)

    def iniciar_download(self, tipo):
        url = self.entrada_url.text().strip()
        if not url or not url.startswith(("http://", "https://")):
            QMessageBox.warning(
                self,
                DICIONARIO_IDIOMAS["msg_aviso_titulo"][estado.idioma_atual],
                DICIONARIO_IDIOMAS["msg_aviso_url"][estado.idioma_atual]
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
            DICIONARIO_IDIOMAS["msg_salvar_como"][estado.idioma_atual],
            os.path.join(pasta_downloads, nome_sugerido),
            filtro_arquivo
        )

        if not caminho_completo:
            return

        if not caminho_completo.lower().endswith(f".{formato}"):
            caminho_completo += f".{formato}"

        # Se o arquivo já existia, o próprio diálogo já pediu a confirmação de substituição ao usuário,
        # e o arquivo antigo será substituído quando o download terminar (ver mover_para_destino)

        estado.url_atual = url
        estado.tipo_atual = tipo
        estado.formato_atual = formato
        estado.caminho_salvamento_atual = caminho_completo
        estado.nome_temporario_atual = f"crimson_{os.getpid()}_{int(time.time())}"  # Nome único deste download na pasta temporária
        estado.estado_download = "rodando"
        self._ultima_velocidade = "--"
        self._ultimo_eta = "--"

        self.botao_baixar_audio.setEnabled(False)
        self.botao_baixar_video.setEnabled(False)

        # Trava também a escolha de formato: enquanto houver um download em andamento (ou pausado), o usuário
        # não pode trocar o formato, senão a tela deixaria de refletir o que está realmente sendo baixado
        self.dropdown_audio.setEnabled(False)
        self.dropdown_video.setEnabled(False)

        botao_ativo.setText(DICIONARIO_IDIOMAS["btn_baixar_inativo"][estado.idioma_atual])

        self.entrada_url.setReadOnly(True)
        self.container_progresso.show()

        self.botao_pausar.setEnabled(True)
        self.botao_continuar.setEnabled(False)
        self.botao_excluir.setEnabled(False)
        self.atualizar_icones_controles()

        self.set_progresso_ui(0, DICIONARIO_IDIOMAS["progresso_init"][estado.idioma_atual])

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

            arquivo_final = baixar_midia(
                estado.url_atual,
                estado.tipo_atual,
                estado.formato_atual,
                hook_progresso=lambda d: self.atualizar_progresso(d, evento_cancelar),
                nome_temporario=estado.nome_temporario_atual
            )
            if not (evento_cancelar and evento_cancelar.is_set()) and estado.estado_download != "cancelado":
                self.mover_para_destino(arquivo_final)
                self._remover_arquivos_residuais()
                self.sinais.sucesso.emit(estado.tipo_atual, estado.formato_atual)
        except DownloadPausado:
            pass
        except Exception as e:
            registrar_erro("thread_download", e)
            if not (evento_cancelar and evento_cancelar.is_set()) and estado.estado_download != "cancelado":
                self.sinais.erro.emit(str(e))

    def mover_para_destino(self, arquivo_final):

        # Leva o arquivo pronto da pasta temporária para o local que o usuário escolheu na janela "Salvar como"
        destino = estado.caminho_salvamento_atual
        try:
            # Troca instantânea quando os dois locais estão no mesmo disco (e substitui o arquivo, se ele já existir)
            os.replace(arquivo_final, destino)
        except OSError:
            # Discos diferentes ou pasta do sandbox: copia o conteúdo e só depois apaga o temporário
            shutil.copyfile(arquivo_final, destino)
            os.remove(arquivo_final)

    def finalizar_com_sucesso(self, tipo, formato):
        QMessageBox.information(
            self,
            DICIONARIO_IDIOMAS["msg_sucesso_titulo"][estado.idioma_atual],
            DICIONARIO_IDIOMAS["msg_sucesso_texto"][estado.idioma_atual]
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
        msg_box.setWindowTitle(DICIONARIO_IDIOMAS["msg_erro_titulo"][estado.idioma_atual])
        msg_box.setTextFormat(Qt.TextFormat.PlainText)
        msg_box.setText(f"{DICIONARIO_IDIOMAS['msg_erro_generico'][estado.idioma_atual]}{erro_limpo}")
        msg_box.exec()
        self.restaurar_botoes()

    def restaurar_botoes(self):
        estado.estado_download = "parado"

        self.botao_baixar_audio.setEnabled(True)
        self.botao_baixar_video.setEnabled(True)

        # Libera de novo a escolha de formato, pois o contexto está livre para um novo download
        self.dropdown_audio.setEnabled(True)
        self.dropdown_video.setEnabled(True)

        self.botao_baixar_audio.setText(DICIONARIO_IDIOMAS["cor_botao_audio"][estado.idioma_atual])
        self.botao_baixar_video.setText(DICIONARIO_IDIOMAS["cor_botao_video"][estado.idioma_atual])

        self.container_progresso.hide()
        self.entrada_url.setReadOnly(False)

        self.botao_pausar.setEnabled(False)
        self.botao_continuar.setEnabled(False)
        self.botao_excluir.setEnabled(False)
        self.atualizar_icones_controles()

        # Coleta de lixo ativa para devolver memória RAM ao sistema imediatamente
        gc.collect()

    def acionar_pausa(self):
        estado.estado_download = "pausado"
        if self._evento_cancelar_atual:
            self._evento_cancelar_atual.set()

        self.botao_pausar.setEnabled(False)
        self.botao_continuar.setEnabled(True)
        self.botao_excluir.setEnabled(True)
        self.atualizar_icones_controles()

    def acionar_retomar(self):
        estado.estado_download = "rodando"

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
            if not estado.nome_temporario_atual:
                return
            # Apaga da pasta temporária tudo que pertence a este download (.part, .ytdl, faixas separadas...)
            base_nome = os.path.join(temp_dir, estado.nome_temporario_atual)
            arquivos_residuais = glob.glob(glob.escape(base_nome) + ".*")
            for arq in arquivos_residuais:
                try:
                    os.remove(arq)
                except Exception:
                    pass
        except Exception as erro_res:
            registrar_erro("remover_arquivos_residuais", erro_res)

    def acionar_excluir(self):

        resposta = QMessageBox.question(
            self,
            DICIONARIO_IDIOMAS["msg_excluir_titulo"][estado.idioma_atual],
            DICIONARIO_IDIOMAS["msg_excluir_texto"][estado.idioma_atual],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            estado.estado_download = "cancelado"
            if self._evento_cancelar_atual:
                self._evento_cancelar_atual.set()
            encerrar_processos_filhos()
            if self._thread_download and self._thread_download.is_alive():
                self._thread_download.join(timeout=1.0)
            self._remover_arquivos_residuais()
            self.restaurar_botoes()
            self.entrada_url.clear()