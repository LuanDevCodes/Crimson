# Projeto Crimson - Ponto de entrada para 'python -m crimson'
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

# O Python executa este arquivo quando rodamos 'python -m crimson'
# Ele só chama a função main(), que fica em main.py
import sys

from crimson.main import main

sys.exit(main())