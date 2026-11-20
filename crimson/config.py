# Projeto Crimson - Caminhos do aplicativo, registro de erros e configurações salvas
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import os                           # Biblioteca para interagir com o sistema operacional (pastas, arquivos e variáveis de ambiente)
import json                         # Biblioteca nativa para salvar e ler dados configurados usando esse formato de arquivo
import re                           # Biblioteca do Regex
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

        # Rodízio, quando o log passa de 1 MB, ele vira 'errors_crimson.log.old' (substituindo o antigo)
        # e um log novo começa, assim o arquivo nunca cresce sem limite
        if os.path.exists(errors_file) and os.path.getsize(errors_file) > 1024 * 1024:
            os.replace(errors_file, errors_file + ".old")

        # Troca os links por '<link>': eles podem ter dados pessoais ou tokens de acesso
        texto_erro = re.sub(r'https?://\S+', '<link>', repr(erro))

        carimbo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(errors_file, 'a', encoding='utf-8') as f:
            f.write(f"[{carimbo}] [{contexto}] {texto_erro}\n")
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

# Os parâmetros novos (playlist, qualidades e pasta padrão) têm valores padrão,
# então quem só passa idioma, tema e animações continua funcionando
# Qualidade "livre" significa que o usuário escolhe na tela inicial a cada download
def salvar_configuracoes(idioma, tema, desativar_anim=False, baixar_playlist=False,
                         qualidade_audio="livre", qualidade_video="livre", pasta_padrao=""):
    # Gravação segura, escreve primeiro num arquivo temporário e só depois troca pelo verdadeiro (os.replace)
    # Se o PC desligar no meio da gravação, o config.json antigo continua inteiro, em vez de ficar pela metade
    arquivo_temporario = config_file + ".tmp"
    try:
        os.makedirs(config_dir, exist_ok=True)
        with open(arquivo_temporario, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    "idioma": idioma,
                    "tema": tema,
                    "desativar_animacoes": bool(desativar_anim),
                    "baixar_playlist": bool(baixar_playlist),
                    "qualidade_audio": qualidade_audio,
                    "qualidade_video": qualidade_video,
                    "pasta_padrao": pasta_padrao
                },
                f,
                indent=4
            )
        os.replace(arquivo_temporario, config_file)
        return True
    except Exception as erro_salvar:
        registrar_erro("salvar_configuracoes", erro_salvar)
        return False