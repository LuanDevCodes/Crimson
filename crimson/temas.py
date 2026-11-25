# Projeto Crimson - Temas visuais (cores) e estilos compartilhados entre as janelas
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle
from PySide6.QtGui import QColor, QPalette, QIcon, QPainter

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
    },

    "Star Hunter": {
        "cor_fundo_janela":             "#0A0E24",  # azul-noite do espaço profundo
        "cor_card":                     "#151C3D",  # vidro escuro (onde a transparência não é possível)
        "cor_borda_card":               "#4A5C9E",  # contorno azulado do vidro
        "cor_do_texto":                 "#EEF2FF",  # branco estelar levemente azulado
        "cor_texto_secundario":         "#AAB6E6",  # azul-lavanda suave
        "cor_botao_audio":              "#3A4F96",  # azul cósmico
        "cor_botao_audio_hover":        "#4A62B2",  # hover áudio
        "cor_botao_video":              "#4E4BA8",  # índigo nebular
        "cor_botao_video_hover":        "#625FC4",  # hover vídeo
        "cor_fonte_botoes":             "#FFFFFF",  # texto branco puro
        "cor_barra_de_pesquisa":        "#0E1432",  # painel escuro da barra
        "cor_texto_caixa_de_pesquisa":  "#EEF2FF",  # texto da barra
        "cor_de_fundo_dropdown":        "#121836",  # fundo da lista aberta
        "cor_do_hover_dropdown":        "#26306A",  # hover da lista
        "cor_da_borda_botao_video":     "#8C8AF0",  # borda vídeo
        "cor_da_borda_botao_audio":     "#7F9BF0",  # borda áudio
        "cor_do_texto_magua":           "#7F89BD",  # marca d'água
        "cor_progresso_fundo":          "#0E1432",  # trilho
        "cor_progresso_barra":          "#7FB8FF"   # barra de progresso
    },

    "Komoki": {
        "cor_fundo_janela":             "#15302A",  # verde profundo da floresta
        "cor_card":                     "#1E3D33",  # vidro de folhagem (onde a transparência não é possível)
        "cor_borda_card":               "#5E8F6E",  # contorno de musgo
        "cor_do_texto":                 "#F1F6E9",  # creme claro, como a luz filtrada pelas folhas
        "cor_texto_secundario":         "#BFD8B4",  # verde-claro suave
        "cor_botao_audio":              "#3F7A5A",  # musgo
        "cor_botao_audio_hover":        "#4C8E69",  # hover áudio
        "cor_botao_video":              "#2F7470",  # água esverdeada
        "cor_botao_video_hover":        "#3A8A85",  # hover vídeo
        "cor_fonte_botoes":             "#FFFFFF",  # texto branco puro
        "cor_barra_de_pesquisa":        "#10261F",  # painel escuro da barra
        "cor_texto_caixa_de_pesquisa":  "#F1F6E9",  # texto da barra
        "cor_de_fundo_dropdown":        "#183A30",  # fundo da lista aberta
        "cor_do_hover_dropdown":        "#2A5546",  # hover da lista
        "cor_da_borda_botao_video":     "#6FC2B4",  # borda vídeo
        "cor_da_borda_botao_audio":     "#8FCB86",  # borda áudio
        "cor_do_texto_magua":           "#8FB28A",  # marca d'água
        "cor_progresso_fundo":          "#10261F",  # trilho
        "cor_progresso_barra":          "#9FD67A"   # barra de progresso
    },

    "Time Moves Slow": {
        "cor_fundo_janela":             "#1E1226",  # roxo do céu logo depois do pôr do sol
        "cor_card":                     "#2C1830",  # vidro vinho (onde a transparência não é possível)
        "cor_borda_card":               "#8A5A6E",  # contorno rosado
        "cor_do_texto":                 "#FFF1E6",  # creme quente
        "cor_texto_secundario":         "#E5C3B5",  # pêssego suave
        "cor_botao_audio":              "#A8553A",  # âmbar do entardecer
        "cor_botao_audio_hover":        "#C0664A",  # hover áudio
        "cor_botao_video":              "#7A3A6A",  # rosa-violeta do crepúsculo
        "cor_botao_video_hover":        "#904A80",  # hover vídeo
        "cor_fonte_botoes":             "#FFFFFF",  # texto branco puro
        "cor_barra_de_pesquisa":        "#170D1C",  # painel escuro da barra
        "cor_texto_caixa_de_pesquisa":  "#FFF1E6",  # texto da barra
        "cor_de_fundo_dropdown":        "#24142A",  # fundo da lista aberta
        "cor_do_hover_dropdown":        "#3E2440",  # hover da lista
        "cor_da_borda_botao_video":     "#C98AB8",  # borda vídeo
        "cor_da_borda_botao_audio":     "#F0A27A",  # borda áudio
        "cor_do_texto_magua":           "#B08A90",  # marca d'água
        "cor_progresso_fundo":          "#170D1C",  # trilho
        "cor_progresso_barra":          "#F0903F"   # barra de progresso
    }
}

# --- Temas de Vidro (Star Hunter, Komoki e Time Moves Slow) ---
# Nesses temas, cards, botões e painéis são de vidro translúcido, e a cena animada aparece por trás
# Cada tema guarda aqui as cores do seu vidro, a janela principal e os diálogos montam os estilos a partir delas
# ("bolha_1" = botões de áudio e secundários | "bolha_2" = botões de vídeo e principais)
VIDRO_TEMAS = {
    "Star Hunter": {
        # Vidro de escotilha de nave, azul-noite, bolhas azul e violeta, destaque em ciano
        "painel":           "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(45, 60, 130, 0.30), stop:1 rgba(25, 35, 90, 0.40)); border: 1px solid rgba(165, 200, 255, 0.45);",
        "botao_topo":       "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(60, 80, 160, 0.34), stop:1 rgba(40, 55, 130, 0.40)); border: 1px solid rgba(165, 200, 255, 0.50);",
        "botao_topo_hover": "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(80, 105, 190, 0.44), stop:1 rgba(55, 75, 160, 0.50));",
        "campo":            "rgba(8, 12, 34, 0.55)",
        "campo_borda":      "rgba(150, 190, 255, 0.45)",
        "destaque":         "rgba(130, 225, 255, 0.95)",
        "selecao":          "#5B7BE0",
        "bolha_1":          "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(200, 220, 255, 0.34), stop:0.48 rgba(110, 145, 240, 0.24), stop:0.52 rgba(75, 105, 215, 0.22), stop:1 rgba(90, 125, 235, 0.32));",
        "bolha_1_hover":    "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(215, 232, 255, 0.46), stop:0.48 rgba(125, 160, 250, 0.36), stop:0.52 rgba(90, 120, 230, 0.34), stop:1 rgba(105, 140, 245, 0.44));",
        "bolha_2":          "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(220, 205, 255, 0.34), stop:0.48 rgba(145, 115, 240, 0.24), stop:0.52 rgba(115, 85, 215, 0.22), stop:1 rgba(130, 100, 235, 0.32));",
        "bolha_2_hover":    "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(232, 220, 255, 0.46), stop:0.48 rgba(160, 130, 250, 0.36), stop:0.52 rgba(130, 100, 230, 0.34), stop:1 rgba(145, 115, 245, 0.44));",
        "borda_bolha":      "rgba(180, 208, 255, 0.55)",
        "aba":              "rgba(40, 55, 120, 0.35)",
        "aba_hover":        "rgba(70, 95, 180, 0.42)",
        "aba_borda":        "rgba(165, 200, 255, 0.38)",
        "plasma":           ("#6FD3FF", "#7B8CFF", "#B07BFF"),     # barra de progresso, switch e rolagem
        "plasma_claro":     ("#B5E9FF", "#8DA0FF", "#A68AF5"),     # rolagem com o mouse por cima
        "trilho":           ((10, 16, 42, 190), (32, 44, 100, 160), (160, 195, 255, 150)),  # topo, base e borda (RGBA)
        "menu":             "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(30, 40, 90, 0.97), stop:1 rgba(14, 20, 48, 0.97)); border: 1.5px solid rgba(150, 190, 255, 0.55);",
        "menu_hover":       "rgba(110, 150, 255, 0.32)",
        "desativado":       ("#2E5A6EB4", "#73C8D4F5", "#38A5C8FF")  # "vidro apagado": fundo, texto e borda (#AARRGGBB)
    },

    "Komoki": {
        # Vidro de folhagem, verde translúcido, bolhas de musgo e de água, destaque dourado como a luz do sol
        "painel":           "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(24, 52, 38, 0.48), stop:1 rgba(12, 32, 26, 0.56)); border: 1px solid rgba(190, 230, 180, 0.42);",
        "botao_topo":       "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(45, 85, 62, 0.40), stop:1 rgba(28, 58, 44, 0.48)); border: 1px solid rgba(190, 230, 180, 0.50);",
        "botao_topo_hover": "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(65, 110, 80, 0.50), stop:1 rgba(40, 78, 58, 0.56));",
        "campo":            "rgba(8, 24, 18, 0.55)",
        "campo_borda":      "rgba(180, 225, 170, 0.45)",
        "destaque":         "rgba(240, 228, 150, 0.95)",
        "selecao":          "#5E9A6A",
        "bolha_1":          "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(205, 235, 190, 0.32), stop:0.48 rgba(115, 170, 105, 0.24), stop:0.52 rgba(85, 145, 80, 0.22), stop:1 rgba(100, 160, 95, 0.30));",
        "bolha_1_hover":    "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(220, 245, 205, 0.44), stop:0.48 rgba(130, 185, 120, 0.36), stop:0.52 rgba(100, 160, 95, 0.34), stop:1 rgba(115, 175, 110, 0.42));",
        "bolha_2":          "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(195, 238, 230, 0.32), stop:0.48 rgba(95, 170, 160, 0.24), stop:0.52 rgba(65, 140, 135, 0.22), stop:1 rgba(80, 155, 150, 0.30));",
        "bolha_2_hover":    "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(210, 246, 240, 0.44), stop:0.48 rgba(110, 185, 175, 0.36), stop:0.52 rgba(80, 155, 150, 0.34), stop:1 rgba(95, 170, 165, 0.42));",
        "borda_bolha":      "rgba(195, 232, 185, 0.55)",
        "aba":              "rgba(30, 62, 46, 0.38)",
        "aba_hover":        "rgba(55, 100, 72, 0.46)",
        "aba_borda":        "rgba(190, 230, 180, 0.40)",
        "plasma":           ("#D6EE8E", "#86CD78", "#4FB3A6"),     # da folha iluminada à água
        "plasma_claro":     ("#E6F6B0", "#A2DC93", "#6CC6BA"),
        "trilho":           ((8, 26, 20, 190), (28, 62, 46, 160), (185, 225, 175, 150)),
        "menu":             "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(32, 64, 48, 0.97), stop:1 rgba(16, 38, 30, 0.97)); border: 1.5px solid rgba(185, 225, 175, 0.55);",
        "menu_hover":       "rgba(150, 210, 130, 0.30)",
        "desativado":       ("#2E6E8C6E", "#73D7E8CD", "#38B4DCAA")
    },

    "Time Moves Slow": {
        # Vidro de crepúsculo, vinho translúcido, bolhas âmbar e rosa-violeta, destaque amarelo como a luz do poste
        "painel":           "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(70, 30, 55, 0.42), stop:1 rgba(35, 14, 35, 0.54)); border: 1px solid rgba(255, 195, 160, 0.42);",
        "botao_topo":       "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(90, 40, 65, 0.44), stop:1 rgba(50, 22, 45, 0.52)); border: 1px solid rgba(255, 195, 160, 0.50);",
        "botao_topo_hover": "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(120, 55, 80, 0.54), stop:1 rgba(70, 30, 58, 0.60));",
        "campo":            "rgba(20, 8, 20, 0.55)",
        "campo_borda":      "rgba(255, 190, 150, 0.45)",
        "destaque":         "rgba(255, 214, 120, 0.95)",
        "selecao":          "#B5506A",
        "bolha_1":          "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 215, 170, 0.32), stop:0.48 rgba(225, 130, 80, 0.24), stop:0.52 rgba(195, 100, 60, 0.22), stop:1 rgba(210, 115, 70, 0.30));",
        "bolha_1_hover":    "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 228, 190, 0.44), stop:0.48 rgba(240, 145, 95, 0.36), stop:0.52 rgba(210, 115, 75, 0.34), stop:1 rgba(225, 130, 85, 0.42));",
        "bolha_2":          "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(245, 200, 230, 0.32), stop:0.48 rgba(185, 95, 150, 0.24), stop:0.52 rgba(150, 65, 125, 0.22), stop:1 rgba(165, 80, 140, 0.30));",
        "bolha_2_hover":    "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(252, 215, 240, 0.44), stop:0.48 rgba(200, 110, 165, 0.36), stop:0.52 rgba(165, 80, 140, 0.34), stop:1 rgba(180, 95, 155, 0.42));",
        "borda_bolha":      "rgba(255, 205, 175, 0.55)",
        "aba":              "rgba(70, 30, 55, 0.40)",
        "aba_hover":        "rgba(110, 50, 80, 0.48)",
        "aba_borda":        "rgba(255, 195, 160, 0.40)",
        "plasma":           ("#FFD27A", "#F0703F", "#B23A6E"),     # as cores do pôr do sol
        "plasma_claro":     ("#FFE3A8", "#F58F66", "#C9578A"),
        "trilho":           ((22, 8, 22, 190), (60, 25, 50, 160), (255, 190, 150, 150)),
        "menu":             "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(60, 26, 50, 0.97), stop:1 rgba(30, 12, 30, 0.97)); border: 1.5px solid rgba(255, 190, 150, 0.55);",
        "menu_hover":       "rgba(255, 170, 120, 0.28)",
        "desativado":       ("#2E966E6E", "#73F0D7CD", "#38FFBE96"),
        "veu_dialogo":      120   # Véu mais escuro nos diálogos, as casas iluminadas atrapalhavam a leitura (os outros temas usam 60)
    }
}

def gradiente_plasma(cores):
    
    # Monta o gradiente horizontal de 3 cores em formato de stylesheet (usado na rolagem das listas)
    return f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cores[0]}, stop:0.5 {cores[1]}, stop:1 {cores[2]})"

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

# Ícones padrão dos botões dos pop-ups (OK, Sim, Não, Cancelar, Salvar, etc.)
ICONES_BOTOES_DIALOGO = (
    QStyle.StandardPixmap.SP_DialogOkButton,
    QStyle.StandardPixmap.SP_DialogCancelButton,
    QStyle.StandardPixmap.SP_DialogYesButton,
    QStyle.StandardPixmap.SP_DialogNoButton,
    QStyle.StandardPixmap.SP_DialogOpenButton,
    QStyle.StandardPixmap.SP_DialogSaveButton,
    QStyle.StandardPixmap.SP_DialogCloseButton,
    QStyle.StandardPixmap.SP_DialogApplyButton,
    QStyle.StandardPixmap.SP_DialogResetButton,
    QStyle.StandardPixmap.SP_DialogDiscardButton,
    QStyle.StandardPixmap.SP_DialogHelpButton,
)

class EstiloCrimson(QProxyStyle):

    """
    Estilo 'Fusion' com um único ajuste, os ícones dos botões dos pop-ups são pintados com a cor do texto do tema
    Sem isso, o ícone vem do tema de ícones do sistema (ex: branco no KDE Breeze Dark) e some nos temas claros do Crimson
    """

    def standardIcon(self, tipo_icone, opcao=None, widget=None):
        icone = super().standardIcon(tipo_icone, opcao, widget)

        # Os demais ícones (como o 'i' azul de informação) continuam com as cores originais
        if tipo_icone not in ICONES_BOTOES_DIALOGO:
            return icone

        pixmap = icone.pixmap(64, 64)
        if pixmap.isNull():
            return icone

        # 'SourceIn' troca a cor de cada pixel pela cor do tema, mantendo o formato (transparência) do desenho
        cor_icone = QApplication.palette().color(QPalette.ColorRole.ButtonText)
        pintor = QPainter(pixmap)
        pintor.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        pintor.fillRect(pixmap.rect(), cor_icone)
        pintor.end()

        return QIcon(pixmap)

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
    elif estado.tema_atual in VIDRO_TEMAS:
        # Temas de vidro, barra de rolagem com o mesmo gradiente da barra de progresso
        bg_handle = gradiente_plasma(VIDRO_TEMAS[estado.tema_atual]["plasma"])
        bg_handle_hover = gradiente_plasma(VIDRO_TEMAS[estado.tema_atual]["plasma_claro"])
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

# --- Visual dos Itens Desativados (botões e dropdowns que não podem ser clicados) ---
def cores_desativado(cor):

    """
    Devolve (fundo, texto, borda) em tons de cinza para os itens desativados
    Em temas claros o cinza é claro; em temas escuros, um cinza escuro, para combinar com o fundo
    O tema é considerado escuro quando o brilho da cor de fundo da janela é baixo (abaixo de 128, numa escala de 0 a 255)
    """

    # Temas de vidro, "vidro apagado", o mesmo vidro dos botões, só que quase transparente e com texto esmaecido
    # (formato #AARRGGBB: os dois primeiros dígitos são a transparência, de 00 = invisível a FF = opaco)
    if estado.tema_atual in VIDRO_TEMAS:
        return VIDRO_TEMAS[estado.tema_atual]["desativado"]

    brilho = QColor(cor["cor_fundo_janela"]).lightness()
    if brilho < 128:
        return "#3E434B", "#8D939C", "#555B64"
    return "#D3D7DD", "#8A919B", "#BFC4CC"

def icone_github(cor):

    # Logo oficial do GitHub: versão preta nos temas claros e branca nos escuros (como o próprio GitHub recomenda)
    return "github_branco.png" if QColor(cor["cor_fundo_janela"]).lightness() < 128 else "github.png"

def estilo_desativado(cor):

    # Mesmas cores acima em formato de stylesheet ('background' sobrescreve também os gradientes dos temas)
    fundo, texto, borda = cores_desativado(cor)
    return f"background: {fundo}; color: {texto}; border: 1px solid {borda};"