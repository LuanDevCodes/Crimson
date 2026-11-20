# Projeto Crimson - Janela principal do aplicativo e ponte de sinais entre threads e interface
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import os               # Biblioteca para interagir com o sistema operacional (navegar entre pastas, verificar se um arquivo existe, criar pastas e ler variáveis)
import json             # Usado para ler a resposta do GitHub com a versão mais recente do yt-dlp
import glob             # Para manipulação dos caminhos dos arquivos, além de ajudar na exclusão dos arquivos residuais
import threading        # Biblioteca para criar rotinas em segundo plano (evita que a tela trave)
import time             # Controle de intervalos e throttling para manter a UI leve
import gc               # Coleta de lixo forçada para liberar memória imediatamente em máquinas modestas
import re               # Usado para limpar textos gerados pelo yt-dlp
import urllib.request   # Biblioteca nativa para baixar arquivos da internet
import zipfile          # Biblioteca nativa para extrair arquivos compactados
import shutil           # Usado para limpeza segura de pastas temporárias e localização de binários no sistema

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QFrame, QMessageBox,
    QFileDialog, QMenu
)
from PySide6.QtCore import Qt, QSize, Signal, QObject, QEvent, QStandardPaths
from PySide6.QtGui import QIcon, QCursor, QAction

from crimson import VERSAO_APP, TITULO_JANELA
from crimson.config import EM_FLATPAK, lib_dir, temp_dir, registrar_erro
from crimson.estado import estado
from crimson.temas import TEMAS, aplicar_paleta_global, estilo_lista_dropdown, estilo_desativado
from crimson.idiomas import DICIONARIO_IDIOMAS
from crimson.icones import caminho_icons, carregar_icone_tematico
from crimson.motor import (
    yt_dlp, DownloadPausado, baixar_midia, encerrar_processos_filhos, erro_disco_cheio, espaco_livre,
    limpar_temp_antigo, QUALIDADES_AUDIO, QUALIDADES_VIDEO
)
from crimson.widgets import ComboBoxModerno, BarraProgressoModerna, WidgetFundoCrimson
from crimson.dialogos import (
    DialogoPlataformas, DialogoConfiguracoes, DialogoSequencial, caixa_mensagem, preencher_combo_qualidade
)

# Expressões regulares pré-compiladas para evitar overhead de compilação em loops de alta frequência
RE_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[mK]')
RE_ESPACO_VELOCIDADE = re.compile(r'(?<=\d)(?=[a-zA-Z])')

def versao_em_numeros(versao):
    # Transforma "2026.07.23" em (2026, 7, 23) para comparar versões número por número
    # (as partes que não são números, como "dev0", são ignoradas)
    return tuple(int(parte) for parte in versao.split('.') if parte.isdigit())

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
    etapa_download = Signal()
    disco_cheio = Signal()
    sucesso = Signal(str, str)
    erro = Signal(str)
    loading_concluido = Signal()

# --------------------------------------------------------------------------------------------------------------------
# --- Janela Principal do Aplicativo ---
# --------------------------------------------------------------------------------------------------------------------

class JanelaCrimson(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITULO_JANELA)

        # Só a altura mínima é fixa, a largura mínima fica por conta do layout, que a calcula pelos textos do idioma atual
        # (um 'setMinimumSize' com largura fixa vence o layout e corta o texto dos botões em idiomas de escrita longa)
        # A altura mínima (430) já reserva o espaço da linha de qualidade e da barra de progresso durante o download
        self.setMinimumHeight(430)
        self.resize(670, 440)

        # Último tamanho definido pelo próprio app, se a janela estiver diferente disso, foi o usuário quem redimensionou
        self._tamanho_automatico = self.size()

        # Controle de instâncias para evitar múltiplas janelas abertas simultaneamente
        self.dialogo_plataformas = None
        self.dialogo_config = None

        # Conecta os sinais para comunicação segura entre as threads e a interface
        self.sinais = SinaisDownload()
        self.sinais.progresso.connect(self.set_progresso_ui)
        self.sinais.etapa_conversao.connect(self.bloquear_pausa_na_conversao)
        self.sinais.etapa_download.connect(self.liberar_pausa_no_download)
        self.sinais.disco_cheio.connect(self.avisar_disco_cheio)
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

        # Indica que o arquivo atual terminou de baixar e está sendo convertido (usado nas playlists)
        self._em_conversao = False

        # Arquivos já baixados que ainda precisam ser movidos para o destino (usado ao retomar após disco cheio)
        self._arquivos_pendentes = []

        # Arquivamento Sequencial: posição do link atual na fila e links que falharam
        self._indice_fila = 0
        self._falhas_fila = []

        # Playlist: erros dos vídeos que não puderam ser baixados e o total de vídeos (para o resumo final)
        self._falhas_playlist = []
        self._total_playlist = 0

        # Downloads cancelados enquanto a thread ainda terminava: a própria thread apaga os temporários ao sair
        self._limpar_ao_sair = set()

        # Apaga restos de downloads antigos (ex: de uma queda de energia) que ficaram na pasta temporária
        limpar_temp_antigo()

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
        layout_topo.setSpacing(10)  # Distância fixa entre os itens da barra (deixa os dois botões da direita próximos)

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

        # Espaço do mesmo tamanho do botão de fila mais o vão até o "?" (40 + 10), para o título continuar
        # centralizado com 2 botões à direita (o Qt não coloca o espaçamento da barra ao redor deste espaço vazio)
        layout_topo.addSpacing(50)
        layout_topo.addWidget(self.label_instrucao, stretch=1)

        # Botão do Arquivamento Sequencial (fila de links), ao lado do botão de plataformas
        self.botao_sequencial = QPushButton()
        self.botao_sequencial.setObjectName("botaoIconeTopo")
        self.botao_sequencial.setFixedSize(40, 40)
        self.botao_sequencial.setIconSize(QSize(24, 24))
        self.botao_sequencial.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.botao_sequencial.clicked.connect(self.abrir_sequencial)
        self.botao_sequencial.setToolTip(DICIONARIO_IDIOMAS["seq_titulo"][estado.idioma_atual])
        layout_topo.addWidget(self.botao_sequencial)

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
        self.entrada_url.setMinimumWidth(588)  # Mantém a janela com pelo menos 640 px (588 + 26 de margem em cada lado)
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

        # Linha de qualidade do áudio (reaproveita o visual do dropdown de formato pelo mesmo objectName)
        linha_qual_audio = QHBoxLayout()
        linha_qual_audio.setSpacing(10)
        self.lbl_qualidade_audio = QLabel()
        self.lbl_qualidade_audio.setObjectName("labelQualidade")
        linha_qual_audio.addWidget(self.lbl_qualidade_audio)
        self.dropdown_qualidade_audio = ComboBoxModerno()
        self.dropdown_qualidade_audio.setObjectName("dropdownAudio")
        self.dropdown_qualidade_audio.setFixedHeight(34)
        self.dropdown_qualidade_audio.setMaxVisibleItems(4)  # Lista curta, com barra de rolagem, para não sair da janela
        self.dropdown_qualidade_audio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        linha_qual_audio.addWidget(self.dropdown_qualidade_audio, stretch=1)
        layout_card_audio.addLayout(linha_qual_audio)

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

        # Linha de qualidade do vídeo (altura máxima da imagem)
        linha_qual_video = QHBoxLayout()
        linha_qual_video.setSpacing(10)
        self.lbl_qualidade_video = QLabel()
        self.lbl_qualidade_video.setObjectName("labelQualidade")
        linha_qual_video.addWidget(self.lbl_qualidade_video)
        self.dropdown_qualidade_video = ComboBoxModerno()
        self.dropdown_qualidade_video.setObjectName("dropdownVideo")
        self.dropdown_qualidade_video.setFixedHeight(34)
        self.dropdown_qualidade_video.setMaxVisibleItems(4)  # 7 opções não cabem abaixo do card: mostra 4 e rola o resto
        self.dropdown_qualidade_video.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        linha_qual_video.addWidget(self.dropdown_qualidade_video, stretch=1)
        layout_card_video.addLayout(linha_qual_video)

        layout_cards.addWidget(self.card_video, stretch=1)

        # Preenche os dropdowns de qualidade conforme o que foi definido nas configurações
        self.atualizar_dropdowns_qualidade()

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
        self.botao_sequencial.setIcon(carregar_icone_tematico("text.png", cor_hex=cor_icone, opacidade=0.95))

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

        self.atualizar_dropdowns_qualidade()
        self.botao_sequencial.setToolTip(DICIONARIO_IDIOMAS["seq_titulo"][estado.idioma_atual])
        if estado.fila_urls and estado.estado_download == "parado":
            self.atualizar_modo_sequencial()  # Reescreve o aviso da barra de URL no idioma novo

        if self.dialogo_plataformas and self.dialogo_plataformas.isVisible():
            self.dialogo_plataformas.atualizar_textos_e_tema()

    def atualizar_dropdowns_qualidade(self):

        """
        Preenche os dropdowns de qualidade da tela inicial no idioma atual
        -> Configuração "livre": o usuário escolhe aqui a cada download (mantendo a escolha que já estava feita)
        -> Qualidade fixada nas configurações: o dropdown mostra esse valor, mas fica travado
        """

        self.lbl_qualidade_audio.setText(DICIONARIO_IDIOMAS["lbl_qualidade"][estado.idioma_atual])
        self.lbl_qualidade_video.setText(DICIONARIO_IDIOMAS["lbl_qualidade"][estado.idioma_atual])

        for combo, valores, tipo, valor_config in (
            (self.dropdown_qualidade_audio, QUALIDADES_AUDIO, "audio", estado.qualidade_audio),
            (self.dropdown_qualidade_video, QUALIDADES_VIDEO, "video", estado.qualidade_video),
        ):
            fixada = valor_config != "livre"
            valor = valor_config if fixada else (combo.currentData() or "melhor")
            preencher_combo_qualidade(combo, valores, tipo, valor)

            # Só fica clicável quando a qualidade é livre e não há download em andamento
            combo.setEnabled(not fixada and estado.estado_download == "parado")

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
            QLabel#labelQualidade {{
                color: {cor["cor_texto_secundario"]};
                font-size: 12px;
                font-weight: bold;
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
            QPushButton#botaoAudio:disabled, QPushButton#botaoVideo:disabled,
            QComboBox#dropdownAudio:disabled, QComboBox#dropdownVideo:disabled,
            QPushButton#botaoIconeTopo:disabled {{
                {estilo_desativado(cor)}
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

        self.ajustar_tamanho_janela()

        if self.dialogo_plataformas and self.dialogo_plataformas.isVisible():
            self.dialogo_plataformas.atualizar_textos_e_tema()
        if self.dialogo_config and self.dialogo_config.isVisible():
            self.dialogo_config.atualizar_textos_e_tema()

    # ------------------------------------------------------------------

    def ajustar_tamanho_janela(self):

        """
        Confere, ao trocar idioma ou tema, se a janela tem espaço (largura e altura) para exibir os textos sem cortes
        -> Se o usuário redimensionou a janela e o conteúdo cabe nela, nada é alterado
        -> Se o conteúdo não cabe, ou se a janela ainda está no tamanho que o próprio app definiu,
          ela vai para o tamanho padrão do idioma atual (670 x 440, ou maior se os textos precisarem)
        """

        # Janela maximizada ou em tela cheia já tem todo o espaço disponível
        if self.isMaximized() or self.isFullScreen():
            return

        # Guarda o tamanho de agora, pois o Qt pode alargar a janela sozinho durante o cálculo abaixo
        tamanho_antes = self.size()

        # O Qt só recalcula os layouts mais tarde (um nível por vez), então forço o cálculo agora, de dentro para fora
        for widget in (self.card_audio, self.card_video, self.container_acoes, self.container_principal, self.widget_central):
            widget.layout().activate()
        self.layout().activate()

        # Espaço mínimo que o conteúdo do idioma atual precisa
        largura_necessaria = self.minimumWidth()
        altura_necessaria = max(self.minimumHeight(), self.widget_central.minimumSizeHint().height())

        conteudo_cabe = tamanho_antes.width() >= largura_necessaria and tamanho_antes.height() >= altura_necessaria
        usuario_redimensionou = tamanho_antes != self._tamanho_automatico

        if conteudo_cabe and usuario_redimensionou:
            return

        # Tamanho padrão do idioma, o padrão do app, alargado só o necessário para os botões não ficarem espremidos
        self.resize(max(670, largura_necessaria), max(440, altura_necessaria))
        self._tamanho_automatico = self.size()

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
            resposta = caixa_mensagem(
                self,
                QMessageBox.Icon.Question,
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

        """
        Atualiza o motor yt-dlp em segundo plano:
        1. Pergunta ao GitHub qual é a última versão OFICIAL (release) do yt-dlp
        2. Se a versão em uso já for igual ou mais nova, não baixa nada
        3. Se houver versão nova, libera a janela e baixa em segundo plano para a pasta 'yt-dlp-novo'
        A versão nova só entra em uso na próxima vez que o Crimson abrir (ver o início do motor.py),
        assim nunca misturo arquivos novos com o motor que já está carregado na memória
        """

        caminho_zip = os.path.join(lib_dir, "yt-dlp-update.zip")
        pasta_staging = os.path.join(lib_dir, "yt-dlp-staging")
        cabecalho = {'User-Agent': f'Mozilla/5.0 (compatible; Crimson-Downloader/{VERSAO_APP})'}
        janela_liberada = False
        try:
            print("[*] Verificando atualizações de segurança (Motor yt-dlp)")

            # Última versão oficial publicada no GitHub (ex: "2026.07.23")
            req_versao = urllib.request.Request(
                "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest", headers=cabecalho
            )
            with urllib.request.urlopen(req_versao, timeout=5) as resposta:
                versao_nova = json.loads(resposta.read().decode('utf-8'))["tag_name"]

            #Compara número por número (ex: (2026, 7, 23) com a versão em uso)
            if versao_em_numeros(yt_dlp.version.__version__) >= versao_em_numeros(versao_nova):
                print("[*] Motor yt-dlp já está atualizado")
                return

            # Há versão nova, a janela não precisa esperar o download, pois ela só vale na próxima abertura
            self.sinais.loading_concluido.emit()
            janela_liberada = True

            req = urllib.request.Request(
                f"https://github.com/yt-dlp/yt-dlp/archive/refs/tags/{versao_nova}.zip", headers=cabecalho
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

            # O ZIP de uma versão traz tudo dentro de uma pasta chamada "yt-dlp-<versão>"
            novo_motor = os.path.join(pasta_staging, f"yt-dlp-{versao_nova}")
            init_ytdlp = os.path.join(novo_motor, "yt_dlp", "__init__.py")
            if not os.path.isfile(init_ytdlp):
                raise FileNotFoundError("Estrutura do motor yt-dlp inválida após extração.")

            # Guarda em 'yt-dlp-novo': o motor.py troca pelo atual na próxima abertura do Crimson
            path_novo = os.path.join(lib_dir, "yt-dlp-novo")
            shutil.rmtree(path_novo, ignore_errors=True)
            os.replace(novo_motor, path_novo)

            print(f"[*] Motor yt-dlp {versao_nova} baixado, será usado na próxima abertura do Crimson")
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

            # Libera a janela (se ela ainda não foi liberada antes do download)
            if not janela_liberada:
                self.sinais.loading_concluido.emit()

    def finalizar_loading(self):
        self.container_loading.hide()
        self.label_instrucao.setText(DICIONARIO_IDIOMAS["instrucao_ready"][estado.idioma_atual])
        self.container_principal.show()

        # O conteúdo principal acabou de aparecer, confere se ele cabe na janela no idioma atual
        self.ajustar_tamanho_janela()

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

                # Playlist, o próximo vídeo começou depois da conversão do anterior, então o botão de pausa volta a funcionar
                if self._em_conversao:
                    self._em_conversao = False
                    self.sinais.etapa_download.emit()

                # Playlist, mostra qual vídeo está sendo baixado, ex: "[3/12]"
                info = d.get('info_dict') or {}
                indice = info.get('playlist_index')
                total_itens = info.get('n_entries') or info.get('playlist_count')
                prefixo = f"[{indice}/{total_itens}]   " if estado.playlist_atual and indice and total_itens else ""

                # Fila do Arquivamento Sequencia, mostra a posição do link atual, ex: "[2/5]"
                if estado.fila_urls:
                    prefixo = f"[{self._indice_fila + 1}/{len(estado.fila_urls)}]   "

                texto = (
                    f"{prefixo}{DICIONARIO_IDIOMAS['progresso_baixando'][estado.idioma_atual]}: {percentual_float:.1f}%   |   "
                    f"{DICIONARIO_IDIOMAS['progresso_vel'][estado.idioma_atual]}: {velocidade}   |   "
                    f"{DICIONARIO_IDIOMAS['progresso_tempo'][estado.idioma_atual]}: {eta}"
                )
                self.sinais.progresso.emit(percentual_float, texto)
            except Exception:
                pass
        elif d['status'] == 'finished':
            self._em_conversao = True
            self.sinais.etapa_conversao.emit()
            self.sinais.progresso.emit(100.0, DICIONARIO_IDIOMAS["progresso_convertendo"][estado.idioma_atual])

    def bloquear_pausa_na_conversao(self):
        # Desativa o botão de pausa durante a mesclagem final do FFmpeg para evitar travamento de estado
        self.botao_pausar.setEnabled(False)
        self.atualizar_icones_controles()

    def liberar_pausa_no_download(self):
        # Reativa o botão de pausa quando um novo arquivo começa a baixar (ex: próximo vídeo da playlist)
        if estado.estado_download == "rodando":
            self.botao_pausar.setEnabled(True)
            self.atualizar_icones_controles()

    def set_progresso_ui(self, valor, texto):
        self.barra_progresso.setValue(int(valor))
        self.label_progresso.setText(texto)

    def iniciar_download(self, tipo):

        # Com uma fila do Arquivamento Sequencial salva, começa pelo próximo link dela (já validados ao salvar)
        # Numa fila nova é o primeiro; numa fila cancelada no meio, os links que já terminaram são pulados
        modo_fila = bool(estado.fila_urls)
        if modo_fila and estado.fila_proximo >= len(estado.fila_urls):
            estado.fila_proximo = 0
        url = estado.fila_urls[estado.fila_proximo] if modo_fila else self.entrada_url.text().strip()
        if not url or not url.startswith(("http://", "https://")):
            QMessageBox.warning(
                self,
                DICIONARIO_IDIOMAS["msg_aviso_titulo"][estado.idioma_atual],
                DICIONARIO_IDIOMAS["msg_aviso_url"][estado.idioma_atual]
            )
            return

        # currentData() devolve o valor interno da qualidade (ex: "320" ou "1080"), e não o texto exibido
        if tipo == 'audio':
            formato = self.dropdown_audio.currentText()
            qualidade = self.dropdown_qualidade_audio.currentData()
            botao_ativo = self.botao_baixar_audio
            nome_sugerido = f"audio.{formato}"
        else:
            formato = self.dropdown_video.currentText()
            qualidade = self.dropdown_qualidade_video.currentData()
            botao_ativo = self.botao_baixar_video
            nome_sugerido = f"video.{formato}"

        # Filtro neutro para todos os idiomas e localização nativa da pasta Downloads
        filtro_arquivo = f"{formato.upper()} (*.{formato})"
        pasta_downloads = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        if not pasta_downloads or not os.path.exists(pasta_downloads):
            pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(pasta_downloads):
            pasta_downloads = os.path.expanduser('~')

        # Onde salvar:
        # -> Pasta padrão definida (e ainda existente): vai direto para ela, com o título do vídeo como nome
        # -> Playlist ou fila sem pasta padrão: pede uma pasta (são vários arquivos, então "Salvar como" não serve)
        # -> Nenhum dos dois: janela "Salvar como" de sempre, para um arquivo só
        pasta_destino = ""
        caminho_completo = ""

        # Pasta padrão que sumiu (apagada ou num pendrive desconectado): avisa antes de pedir outro lugar
        if estado.pasta_padrao and not os.path.isdir(estado.pasta_padrao):
            caixa_mensagem(
                self,
                QMessageBox.Icon.Warning,
                DICIONARIO_IDIOMAS["msg_aviso_titulo"][estado.idioma_atual],
                DICIONARIO_IDIOMAS["msg_pasta_padrao_sumiu"][estado.idioma_atual]
            )

        if estado.pasta_padrao and os.path.isdir(estado.pasta_padrao):
            pasta_destino = estado.pasta_padrao
        elif estado.baixar_playlist or modo_fila:
            pasta_destino = QFileDialog.getExistingDirectory(
                self,
                DICIONARIO_IDIOMAS["msg_escolher_pasta"][estado.idioma_atual],
                pasta_downloads
            )
            if not pasta_destino:
                return
        else:
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

        estado.tipo_atual = tipo
        estado.formato_atual = formato
        estado.qualidade_atual = qualidade or "melhor"
        estado.caminho_salvamento_atual = caminho_completo
        estado.pasta_destino_atual = pasta_destino

        # Na fila, cada link baixa só o vídeo individual (para a numeração (01), (02)... não se misturar com playlists)
        estado.playlist_atual = estado.baixar_playlist and not modo_fila
        self._indice_fila = estado.fila_proximo if modo_fila else 0

        # A lista de falhas só recomeça numa fila nova; ao retomar, as falhas anteriores continuam no resumo
        if self._indice_fila == 0:
            self._falhas_fila = []

        self.botao_baixar_audio.setEnabled(False)
        self.botao_baixar_video.setEnabled(False)
        self.botao_sequencial.setEnabled(False)  # A fila não pode ser trocada no meio dos downloads

        # Trava também a escolha de formato: enquanto houver um download em andamento (ou pausado), o usuário
        # não pode trocar o formato, senão a tela deixaria de refletir o que está realmente sendo baixado
        self.dropdown_audio.setEnabled(False)
        self.dropdown_video.setEnabled(False)
        self.dropdown_qualidade_audio.setEnabled(False)
        self.dropdown_qualidade_video.setEnabled(False)

        botao_ativo.setText(DICIONARIO_IDIOMAS["btn_baixar_inativo"][estado.idioma_atual])

        self.entrada_url.setReadOnly(True)
        self.container_progresso.show()

        self.iniciar_item(url)

    def iniciar_item(self, url):

        # Prepara e dispara o download de um link (o único no modo normal, ou o item atual da fila)
        estado.url_atual = url
        estado.nome_temporario_atual = f"crimson_{os.getpid()}_{int(time.time())}_{self._indice_fila}"  # Nome único na pasta temporária
        estado.estado_download = "rodando"
        self._ultima_velocidade = "--"
        self._ultimo_eta = "--"
        self._em_conversao = False
        self._arquivos_pendentes = []

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

        # Nome deste download na pasta temporária, guardado agora porque o estado pode mudar enquanto a thread roda
        nome_temporario = estado.nome_temporario_atual
        try:
            # Aguarda a thread anterior terminar por completo antes de mexer no mesmo arquivo '.part'
            # (sem limite de tempo: esta espera acontece aqui em segundo plano, então a janela não trava,
            # e evita que duas threads baixem o mesmo arquivo ao mesmo tempo)
            if thread_anterior is not None and thread_anterior.is_alive():
                thread_anterior.join()

            if evento_cancelar and evento_cancelar.is_set():
                return

            # Se o download já tinha terminado e só faltou mover os arquivos (ex: disco cheio no destino),
            # ao continuar não baixa de novo: vai direto para a mudança dos arquivos que sobraram
            if not self._arquivos_pendentes:
                falhas = []
                self._arquivos_pendentes = baixar_midia(
                    estado.url_atual,
                    estado.tipo_atual,
                    estado.formato_atual,
                    hook_progresso=lambda d: self.atualizar_progresso(d, evento_cancelar),
                    nome_temporario=nome_temporario,
                    qualidade=estado.qualidade_atual,
                    baixar_playlist=estado.playlist_atual,
                    falhas=falhas
                )
                # Playlist: guarda quantos vídeos falharam e o total, para o resumo no final
                self._falhas_playlist = falhas
                self._total_playlist = len(self._arquivos_pendentes) + len(falhas)
            if not (evento_cancelar and evento_cancelar.is_set()) and estado.estado_download != "cancelado":

                # Move um arquivo por vez e só o tira da lista depois de movido com sucesso
                while self._arquivos_pendentes:
                    arquivo_final, titulo = self._arquivos_pendentes[0]
                    self.mover_para_destino(arquivo_final, self.definir_destino(arquivo_final, titulo))
                    self._arquivos_pendentes.pop(0)
                self._remover_arquivos_residuais()
                self.sinais.sucesso.emit(estado.tipo_atual, estado.formato_atual)
        except DownloadPausado:
            pass
        except Exception as e:

            # Disco cheio: em vez de falhar, pausa o download (mantendo os arquivos parciais) e avisa o usuário
            if erro_disco_cheio(e) and not (evento_cancelar and evento_cancelar.is_set()) and estado.estado_download != "cancelado":
                estado.estado_download = "pausado"
                self.sinais.disco_cheio.emit()
                return
            registrar_erro("thread_download", e)
            if not (evento_cancelar and evento_cancelar.is_set()) and estado.estado_download != "cancelado":
                self.sinais.erro.emit(str(e))
        finally:
            # Download cancelado enquanto esta thread ainda terminava: agora que ela parou, apaga os temporários
            if nome_temporario in self._limpar_ao_sair:
                self._limpar_ao_sair.discard(nome_temporario)
                self._remover_arquivos_residuais(nome_temporario)

    def definir_destino(self, arquivo_final, titulo):

        # Sem pasta de destino, vale o caminho escolhido na janela "Salvar como"
        if not estado.pasta_destino_atual:
            return estado.caminho_salvamento_atual

        # Com pasta de destino, o nome vem do título (sem caracteres proibidos em nomes de arquivo)
        # e a extensão vem do arquivo real que o yt-dlp gerou
        nome_limpo = yt_dlp.utils.sanitize_filename(titulo) or "Crimson"

        # O Linux e o Windows aceitam nomes de no máximo 255 bytes. Corto o título em 150 bytes
        # (letras como 'ã' ou '語' ocupam mais de 1 byte), sobrando espaço para "(01) ", " (2)" e a extensão
        # O 'ignore' descarta um caractere que tenha ficado cortado pela metade
        nome_limpo = nome_limpo.encode('utf-8')[:150].decode('utf-8', 'ignore').strip() or "Crimson"
        extensao = os.path.splitext(arquivo_final)[1]

        # Na fila, o nome ganha a posição do link, ex: "(01) Título", para os arquivos ficarem na ordem colada
        if estado.fila_urls:
            nome_limpo = f"({self._indice_fila + 1:02d}) {nome_limpo}"
        return self.caminho_disponivel(estado.pasta_destino_atual, nome_limpo, extensao)

    def caminho_disponivel(self, pasta, nome, extensao):

        # Se "nome.ext" já existir na pasta, tenta "nome (2).ext", "nome (3).ext"... para não apagar nada do usuário
        destino = os.path.join(pasta, nome + extensao)
        contador = 2
        while os.path.exists(destino):
            destino = os.path.join(pasta, f"{nome} ({contador}){extensao}")
            contador += 1
        return destino

    def mover_para_destino(self, arquivo_final, destino):

        # Leva o arquivo pronto da pasta temporária para o destino final (escolhido pelo usuário ou montado pelo título)
        try:
            # Troca instantânea quando os dois locais estão no mesmo disco (e substitui o arquivo, se ele já existir)
            os.replace(arquivo_final, destino)
        except OSError:
            # Discos diferentes ou pasta do sandbox: copia o conteúdo e só depois apaga o temporário
            try:
                shutil.copyfile(arquivo_final, destino)
            except OSError:
                # Cópia interrompida (ex: disco cheio): apaga o pedaço copiado para não deixar um arquivo quebrado
                # no destino, mantendo o original na pasta temporária para tentar de novo
                if os.path.exists(destino):
                    os.remove(destino)
                raise
            os.remove(arquivo_final)

    def finalizar_com_sucesso(self, tipo, formato):

        # Na fila: passa direto para o próximo link, sem pop-up (o resumo aparece só no final)
        if estado.fila_urls:
            self.proximo_item_fila()
            return

        if self._falhas_playlist:
            # Playlist em que alguns vídeos não puderam ser baixados (indisponíveis, privados...): avisa quantos
            caixa_mensagem(
                self,
                QMessageBox.Icon.Warning,
                DICIONARIO_IDIOMAS["msg_aviso_titulo"][estado.idioma_atual],
                DICIONARIO_IDIOMAS["msg_playlist_falhas"][estado.idioma_atual].format(
                    falhas=len(self._falhas_playlist), total=self._total_playlist
                )
            )
        else:
            QMessageBox.information(
                self,
                DICIONARIO_IDIOMAS["msg_sucesso_titulo"][estado.idioma_atual],
                DICIONARIO_IDIOMAS["msg_sucesso_texto"][estado.idioma_atual]
            )
        self._falhas_playlist = []
        self.restaurar_botoes()
        self.entrada_url.clear()

    # ------------------------------------------------------------------
    # --- Arquivamento Sequencial (Fila de Downloads) ---
    def abrir_sequencial(self):
        dialogo = DialogoSequencial(self)
        dialogo.exec()

    def atualizar_modo_sequencial(self):

        # Com fila salva, a barra de URL fica travada mostrando o aviso do modo sequencial; sem fila, volta ao normal
        if estado.fila_urls:
            self.entrada_url.setReadOnly(True)
            self.entrada_url.setText(DICIONARIO_IDIOMAS["seq_texto_entrada"][estado.idioma_atual])
            self.entrada_url.setToolTip(f"{len(estado.fila_urls)} links")
        elif estado.estado_download == "parado":
            # Sem download rodando, a barra só fica travada no modo sequencial, então o texto dela é o aviso: apaga
            if self.entrada_url.isReadOnly():
                self.entrada_url.clear()
            self.entrada_url.setToolTip("")
            self.entrada_url.setReadOnly(False)

    def proximo_item_fila(self):
        # Avança para o próximo link da fila, ou mostra o resumo se ela acabou
        self._indice_fila += 1
        estado.fila_proximo = self._indice_fila  # Se a fila for cancelada depois daqui, recomeça deste link
        if self._indice_fila < len(estado.fila_urls):
            self.iniciar_item(estado.fila_urls[self._indice_fila])
        else:
            self.concluir_fila()

    def concluir_fila(self):

        # Fim da fila: mostra o resumo (com os links que falharam, se houver) e volta ao modo normal
        total = len(estado.fila_urls)
        titulo = DICIONARIO_IDIOMAS["msg_sucesso_titulo"][estado.idioma_atual]
        texto = DICIONARIO_IDIOMAS["msg_sucesso_texto"][estado.idioma_atual]
        icone = QMessageBox.Icon.Information
        if self._falhas_fila:
            # Com falhas, o título vira "Aviso" (e não "Sucesso", que seria estranho se todos falhassem)
            icone = QMessageBox.Icon.Warning
            titulo = DICIONARIO_IDIOMAS["msg_aviso_titulo"][estado.idioma_atual]
            lista = "\n".join(f"• {link[:80]}" for link in self._falhas_fila[:10])
            texto = DICIONARIO_IDIOMAS["seq_resumo_falhas"][estado.idioma_atual].format(falhas=len(self._falhas_fila), total=total)
            texto += f"\n\n{lista}"

        estado.fila_urls = []
        estado.fila_proximo = 0
        caixa_mensagem(self, icone, titulo, texto)
        self.restaurar_botoes()
        self.entrada_url.clear()

    def finalizar_com_erro(self, mensagem_erro):

        # Na fila: guarda o link que falhou, limpa o que sobrou dele e segue para o próximo
        if estado.fila_urls:
            registrar_erro("fila_sequencial", mensagem_erro)
            self._falhas_fila.append(estado.url_atual)
            self._remover_arquivos_residuais()
            self.proximo_item_fila()
            return

        # Higieniza códigos ANSI, limita tamanho e força texto puro no diálogo de erro
        registrar_erro("finalizar_com_erro_ui", mensagem_erro)
        self._remover_arquivos_residuais()  # Apaga os pedaços do download que falhou
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
        self.atualizar_dropdowns_qualidade()  # Libera a qualidade (se ela não estiver fixada nas configurações)

        self.botao_baixar_audio.setText(DICIONARIO_IDIOMAS["cor_botao_audio"][estado.idioma_atual])
        self.botao_baixar_video.setText(DICIONARIO_IDIOMAS["cor_botao_video"][estado.idioma_atual])

        self.container_progresso.hide()
        self.entrada_url.setReadOnly(False)
        self.botao_sequencial.setEnabled(True)

        # Fila ainda salva (ex: depois de cancelar): a barra de URL volta a mostrar o aviso do modo sequencial
        if estado.fila_urls:
            self.atualizar_modo_sequencial()

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

    def _remover_arquivos_residuais(self, nome_temporario=None):

        # Sem nome informado, limpa o download atual
        nome = nome_temporario or estado.nome_temporario_atual
        try:
            if not nome:
                return
            # Apaga da pasta temporária tudo que pertence a este download (.part, .ytdl, faixas separadas...)
            base_nome = os.path.join(temp_dir, nome)
            arquivos_residuais = glob.glob(glob.escape(base_nome) + ".*")
            for arq in arquivos_residuais:
                try:
                    os.remove(arq)
                except Exception:
                    pass

            # Downloads de playlist usam uma subpasta com o mesmo nome, que é apagada inteira
            if os.path.isdir(base_nome):
                shutil.rmtree(base_nome, ignore_errors=True)
        except Exception as erro_res:
            registrar_erro("remover_arquivos_residuais", erro_res)

    def acionar_excluir(self):

        resposta = caixa_mensagem(
            self,
            QMessageBox.Icon.Question,
            DICIONARIO_IDIOMAS["msg_excluir_titulo"][estado.idioma_atual],
            DICIONARIO_IDIOMAS["msg_excluir_texto"][estado.idioma_atual],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            self.cancelar_download()

    def cancelar_download(self):

        # Interrompe o download, apaga os arquivos temporários e devolve a tela ao estado inicial
        # (usado pelo botão de excluir e pelo "Finalizar" do aviso de disco cheio)
        estado.estado_download = "cancelado"
        if self._evento_cancelar_atual:
            self._evento_cancelar_atual.set()
        encerrar_processos_filhos()

        # Se a thread ainda está terminando, apagar agora seria inútil (ela poderia recriar os arquivos):
        # ela mesma apaga os temporários ao sair. Assim a janela não precisa ficar travada esperando
        if self._thread_download and self._thread_download.is_alive():
            self._limpar_ao_sair.add(estado.nome_temporario_atual)
        else:
            self._remover_arquivos_residuais()
        self.restaurar_botoes()

        # A fila não é apagada ao cancelar, para o usuário poder recomeçar sem colar os links de novo
        if not estado.fila_urls:
            self.entrada_url.clear()

    # ------------------------------------------------------------------
    # --- Aviso de Disco Cheio ---
    def pastas_do_download(self):
        # Pastas onde o download escreve, a temporária e a de destino
        destino = estado.pasta_destino_atual or os.path.dirname(estado.caminho_salvamento_atual)
        return temp_dir, destino

    def avisar_disco_cheio(self):

        """
        Chamado quando o disco enche durante o download (ou ao mover o arquivo pronto)
        O download já está pausado; a tela mostra os botões de pausa e o usuário escolhe:
        -> Continuar: só retoma se algum espaço tiver sido liberado, senão o aviso aparece de novo
        -> Finalizar: cancela o download e apaga os arquivos temporários
        """

        self.botao_pausar.setEnabled(False)
        self.botao_continuar.setEnabled(True)
        self.botao_excluir.setEnabled(True)
        self.atualizar_icones_controles()
        self.set_progresso_ui(self.barra_progresso.value(), DICIONARIO_IDIOMAS["msg_disco_cheio_titulo"][estado.idioma_atual])

        # Espaço livre no momento do erro, para saber depois se o usuário liberou alguma coisa
        livre_no_erro = espaco_livre(*self.pastas_do_download())

        while True:
            caixa = QMessageBox(self)
            caixa.setIcon(QMessageBox.Icon.Warning)
            caixa.setWindowTitle(DICIONARIO_IDIOMAS["msg_disco_cheio_titulo"][estado.idioma_atual])
            caixa.setText(DICIONARIO_IDIOMAS["msg_disco_cheio_texto"][estado.idioma_atual])
            botao_finalizar = caixa.addButton(DICIONARIO_IDIOMAS["btn_finalizar"][estado.idioma_atual], QMessageBox.ButtonRole.RejectRole)
            botao_continuar = caixa.addButton(DICIONARIO_IDIOMAS["btn_continuar"][estado.idioma_atual], QMessageBox.ButtonRole.AcceptRole)
            caixa.setDefaultButton(botao_continuar)
            caixa.exec()
            clicado = caixa.clickedButton()

            if clicado == botao_finalizar:
                self.cancelar_download()
                return
            if clicado != botao_continuar:
                return  # Fechou o aviso pelo 'X': o download fica pausado e os botões da tela continuam valendo

            # Só retoma se algum espaço foi liberado desde o erro (se ainda não for suficiente, o aviso volta sozinho)
            if espaco_livre(*self.pastas_do_download()) > livre_no_erro:
                self.acionar_retomar()
                return