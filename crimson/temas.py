# Projeto Crimson - Temas visuais (cores) e estilos compartilhados entre as janelas
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPalette

from crimson.estado import estado

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

def estilo_lista_dropdown(cor):

    """
    Estilo da lista aberta dos dropdowns, compartilhado pela janela principal e pela de Configurações
    """

    # Se o tema for Frutiger Aero ou Platinum Disc, personaliza a barra de rolagem com gradiente temático
    if estado.tema_atual == "Frutiger Aero":
        bg_handle = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6ECBFF, stop:0.5 #0088FF, stop:1 #005FB8)"
        bg_handle_hover = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8CE0FF, stop:0.5 #1FA3FF, stop:1 #0077E6)"
    elif estado.tema_atual == "Platinum Disc":
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