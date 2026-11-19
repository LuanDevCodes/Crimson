# Projeto Crimson - Inicialização da aplicação
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

from PySide6.QtWidgets import QApplication

from crimson.janela import JanelaCrimson
from crimson.temas import EstiloCrimson


# Função que cria a aplicação Qt, abre a janela principal e mantém o programa rodando
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Crimson")
    app.setDesktopFileName("io.github.luandevcodes.Crimson")

    # O estilo 'Fusion' é desenhado pelo próprio Qt, então fica idêntico no Windows e no Linux
    # (sem ele, o Qt usa o estilo do sistema, como Breeze no KDE, Windows 11 no Windows, etc.)
    # O 'EstiloCrimson' é o próprio Fusion, só recolorindo os ícones dos botões dos pop-ups conforme o tema
    app.setStyle(EstiloCrimson("Fusion"))

    janela = JanelaCrimson()
    janela.show()

    # Devolve o código de saída do Qt para o sistema operacional
    return app.exec()