# Projeto Crimson - Janelas modais: Plataformas Suportadas e Configurações/Sobre
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import gc               # Coleta de lixo forçada para liberar memória imediatamente em máquinas modestas
import webbrowser       # Usado para abrir links na internet (como no caso dos links dos repositórios usados)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QTabWidget, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

from crimson.config import registrar_erro, salvar_configuracoes
from crimson.estado import estado
from crimson.temas import TEMAS, estilo_lista_dropdown
from crimson.idiomas import IDIOMAS_SUPORTADOS, DICIONARIO_IDIOMAS
from crimson.icones import carregar_pixmap_icone, carregar_icone_tematico
from crimson.motor import encerrar_processos_filhos
from crimson.widgets import ComboBoxModerno, BotaoSwitchTema

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
        cor = TEMAS[estado.tema_atual]
        self.setWindowTitle(DICIONARIO_IDIOMAS["plataformas_titulo"][estado.idioma_atual])
        self.lbl_titulo.setText(DICIONARIO_IDIOMAS["plataformas_titulo"][estado.idioma_atual])
        self.botao_lista_oficial.setText(DICIONARIO_IDIOMAS["plataformas_texto"][estado.idioma_atual])
        self.botao_lista_oficial.setIcon(carregar_icone_tematico("github.png", cor_hex=None))
        self.lbl_aviso.setText(DICIONARIO_IDIOMAS["plataformas_aviso"][estado.idioma_atual])

        if estado.tema_atual == "Frutiger Aero":
            estilo_fundo = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #BEE5FF, stop:0.5 #DEF3FF, stop:1 #C2F2D7);"
            estilo_card = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(235, 248, 255, 0.78), stop:0.5 rgba(210, 240, 255, 0.58), stop:1 rgba(190, 232, 255, 0.72)); border: 1.5px solid rgba(135, 200, 245, 0.80); border-radius: 14px;"
            estilo_btn = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(238, 249, 255, 0.94), stop:0.5 rgba(215, 240, 255, 0.88), stop:1 rgba(195, 230, 255, 0.92)); color: #0C2D48; border: 1px solid rgba(110, 182, 235, 0.85); border-radius: 10px; padding: 8px 16px; font-weight: bold;"
            estilo_btn_hover = "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(248, 253, 255, 0.98), stop:0.5 rgba(228, 246, 255, 0.95), stop:1 rgba(208, 238, 255, 0.96)); border: 1px solid rgba(80, 165, 230, 0.95);"
        elif estado.tema_atual == "Platinum Disc":
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
        self.dropdown_idioma.setCurrentText(estado.idioma_atual)
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
        self.dropdown_tema.setCurrentText(estado.tema_atual)
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
        self.switch_animacoes.setChecked(estado.desativar_animacoes)
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
            DICIONARIO_IDIOMAS["msg_confirm_limpeza_titulo"][estado.idioma_atual],
            DICIONARIO_IDIOMAS["msg_confirm_limpeza_texto"][estado.idioma_atual],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                encerrar_processos_filhos()
                gc.collect()

                QMessageBox.information(
                    self,
                    DICIONARIO_IDIOMAS["msg_sucesso_limpeza_titulo"][estado.idioma_atual],
                    DICIONARIO_IDIOMAS["msg_sucesso_limpeza_texto"][estado.idioma_atual]
                )
            except Exception as erro_limpeza:
                registrar_erro("limpar_processos", erro_limpeza)

    def confirmar_e_salvar(self):
        novo_idioma = self.dropdown_idioma.currentText()
        novo_tema = self.dropdown_tema.currentText()
        novo_desativar_anim = self.switch_animacoes.isChecked()

        titulo_msg = DICIONARIO_IDIOMAS["msg_confirm_salvar_titulo"].get(estado.idioma_atual, "Confirm")
        texto_msg = DICIONARIO_IDIOMAS["msg_confirm_salvar_texto"].get(estado.idioma_atual, "Are you sure you want to save?")

        resposta = QMessageBox.question(
            self,
            titulo_msg,
            texto_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            estado.idioma_atual = novo_idioma
            estado.tema_atual = novo_tema
            estado.desativar_animacoes = novo_desativar_anim

            salvar_configuracoes(estado.idioma_atual, estado.tema_atual, estado.desativar_animacoes)

            # Atualiza a janela principal e a janela de configurações em tempo real
            self.janela_mae.atualizar_idioma_ui()
            self.janela_mae.aplicar_tema()
            self.atualizar_textos_e_tema()

            texto_sucesso = DICIONARIO_IDIOMAS["msg_sucesso_salvar_texto"].get(estado.idioma_atual, "Settings saved successfully")

            QMessageBox.information(self, titulo_msg, texto_sucesso)

    def atualizar_textos_e_tema(self):
        cor = TEMAS[estado.tema_atual]

        self.setWindowTitle(f"{DICIONARIO_IDIOMAS['aba_sistema'][estado.idioma_atual]} / {DICIONARIO_IDIOMAS['aba_sobre'][estado.idioma_atual]}")
        self.abas.setTabText(0, DICIONARIO_IDIOMAS["aba_sistema"][estado.idioma_atual])
        self.abas.setTabText(1, DICIONARIO_IDIOMAS["aba_sobre"][estado.idioma_atual])

        self.label_idioma.setText(DICIONARIO_IDIOMAS["lbl_idioma"][estado.idioma_atual])
        self.label_tema.setText(DICIONARIO_IDIOMAS["lbl_tema"][estado.idioma_atual])
        self.label_animacoes.setText(DICIONARIO_IDIOMAS["lbl_desativar_animacoes"][estado.idioma_atual])
        self.switch_animacoes.update()
        self.botao_limpar.setText("  " + DICIONARIO_IDIOMAS["btn_limpar_processos"][estado.idioma_atual])
        self.botao_salvar.setText(DICIONARIO_IDIOMAS["btn_salvar_config"][estado.idioma_atual])

        self.label_versao.setText(DICIONARIO_IDIOMAS["lbl_versao"][estado.idioma_atual])
        self.label_disclaimer.setText(DICIONARIO_IDIOMAS["txt_disclaimer"][estado.idioma_atual])
        self.label_creditos.setText(DICIONARIO_IDIOMAS["lbl_creditos"][estado.idioma_atual])
        self.link_crimson.setText(DICIONARIO_IDIOMAS["link_crimson"][estado.idioma_atual])
        self.link_ytdlp.setText(DICIONARIO_IDIOMAS["link_ytdlp"][estado.idioma_atual])
        self.link_ffmpeg.setText(DICIONARIO_IDIOMAS["link_ffmpeg"][estado.idioma_atual])
        self.marca_dagua.setText(DICIONARIO_IDIOMAS["marca_dagua"][estado.idioma_atual])

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

        if estado.tema_atual == "Frutiger Aero":
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
        elif estado.tema_atual == "Platinum Disc":
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