# Projeto Crimson - Caminhos do aplicativo, registro de erros e configurações salvas
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import os                           # Biblioteca para interagir com o sistema operacional (pastas, arquivos e variáveis de ambiente)
import json                         # Biblioteca nativa para salvar e ler dados configurados usando esse formato de arquivo
import platform                     # Detecta o sistema operacional para adaptar os caminhos
from datetime import datetime       # Usado para carimbar data e hora nos registros de erro

# -------------------------------
# --- Setup de Diretórios do Aplicativo (AppData) e Persistência ---

SISTEMA = platform.system()  # Retorna 'Windows', 'Linux' ou 'Darwin' (macOS)
EM_FLATPAK = os.path.exists('/.flatpak-info')  # Identifica se está rodando dentro do sandbox oficial do Flatpak

# No Windows: usa a pasta oficial LocalAppData (ex: C:\Users\Luan\AppData\Local\Crimson)
# No Linux:   respeita o XDG_DATA_HOME (essencial para o sandbox do Flatpak) com fallback para ~/.local/share/Crimson
if SISTEMA == 'Windows':
    appdata_local = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
else:
    appdata_local = os.environ.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')

crimson_dir = os.path.join(appdata_local, 'Crimson')
lib_dir = os.path.join(crimson_dir, 'Lib')
config_dir = os.path.join(crimson_dir, 'Config')
config_file = os.path.join(config_dir, 'config.json')
errors_file = os.path.join(config_dir, 'errors_crimson.log')

# Pasta temporária dos downloads em andamento (arquivos '.part', faixas separadas e o arquivo final antes de ser movido)
# No Windows fica dentro da pasta do Crimson; no Linux usa o XDG_CACHE_HOME (no Flatpak aponta para o cache do próprio app)
if SISTEMA == 'Windows':
    temp_dir = os.path.join(crimson_dir, 'Temp')
else:
    cache_local = os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache')
    temp_dir = os.path.join(cache_local, 'Crimson', 'Temp')

# Cria as pastas caso elas não existam no computador desse usuário
os.makedirs(lib_dir, exist_ok=True)
os.makedirs(config_dir, exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)

# --- Função de Registro de Erros ---
def registrar_erro(contexto, erro):

    # Salva falhas técnicas em arquivo dedicado na pasta Config para diagnóstico sem expor dados sensíveis
    try:
        os.makedirs(config_dir, exist_ok=True)
        carimbo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(errors_file, 'a', encoding='utf-8') as f:
            f.write(f"[{carimbo}] [{contexto}] {repr(erro)}\n")
    except Exception:
        pass

# --- Funções de Leitura e Escrita do JSON ---
def carregar_configuracoes():

    padrao = {"idioma": "English", "tema": "Frutiger Aero", "desativar_animacoes": False}

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                return dados
        except Exception as erro_json:
            registrar_erro("carregar_configuracoes", erro_json)
    return padrao

def salvar_configuracoes(idioma, tema, desativar_anim=False):
    try:
        os.makedirs(config_dir, exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    "idioma": idioma,
                    "tema": tema,
                    "desativar_animacoes": bool(desativar_anim)
                },
                f,
                indent=4
            )
        return True
    except Exception as erro_salvar:
        registrar_erro("salvar_configuracoes", erro_salvar)
        return False