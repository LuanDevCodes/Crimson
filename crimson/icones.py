# Projeto Crimson - Carregamento e recoloração de ícones (Pillow + Qt) com cache em memória
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import os               # Biblioteca para interagir com o sistema operacional (verificar se um arquivo existe, montar caminhos)
import sys              # Necessário para identificar se está rodando como .exe
from PIL import Image   # Biblioteca 'Pillow', ajuda na manipulação de canais RGBA e recoloração dinâmica dos ícones

from PySide6.QtGui import QIcon, QPixmap, QImage

# Pasta dos ícones da interface: dentro do .exe do PyInstaller fica em 'Icons' (via --add-data),
# e no código-fonte fica na pasta 'Icons' ao lado deste arquivo (crimson/Icons)
if hasattr(sys, '_MEIPASS'):
    caminho_icons = os.path.join(sys._MEIPASS, "Icons")
else:
    caminho_icons = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Icons")

# --------------------------------------------------------------------------------------------------------------------
# --- Utilitários Visuais (Manipulação de Ícones com Pillow + Qt e Cache de CPU) ---
# --------------------------------------------------------------------------------------------------------------------

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