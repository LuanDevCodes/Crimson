# Projeto Crimson - Pacote principal da aplicação
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

# Este arquivo transforma a pasta 'crimson' em um "pacote" Python:
# é por causa dele que podemos escrever 'from crimson.config import ...' e rodar 'python -m crimson'

# Constante única de versão para manter sincronia em toda a aplicação
# Ao lançar uma nova versão, atualize também: pyproject.toml, meson.build e a lista <releases> do metainfo.xml
VERSAO_APP = "V.4.0.0"