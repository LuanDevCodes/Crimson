# Projeto Crimson - Motor de download (yt-dlp + FFmpeg), pausa e limpeza de processos
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import os           # Biblioteca para interagir com o sistema operacional (caminhos, variáveis de ambiente e PID)
import sys          # Necessário para identificar se está rodando como .exe e para ajustar o caminho de importação
import glob         # Para procurar arquivos na pasta temporária pelo nome
import shutil       # Usado para limpeza segura de pastas temporárias e localização de binários no sistema
import subprocess   # Usado para executar comandos do sistema (como atualizar o yt-dlp ou finalizar processos)

from crimson.config import SISTEMA, lib_dir, temp_dir, registrar_erro

# --- Injeção de Dependência Modular com Autorrecuperação ---
# Procura se o motor do yt-dlp já foi baixado na pasta Lib
# Se existir, força o Python a ler as bibliotecas dessa pasta antes das bibliotecas congeladas (PyInstaller)
path_yt_dlp = os.path.join(lib_dir, 'yt-dlp-master')

if os.path.exists(path_yt_dlp):
    sys.path.insert(0, path_yt_dlp)  # O insert 0 diz basicamente "olhe aqui antes de qualquer outro lugar"

try:
    import yt_dlp  # Tenta importar o motor atualizado (ou local se a pasta externa não existir)
except Exception as erro_import_ytdlp:

    # Se a pasta externa estiver corrompida por queda de energia/rede anterior, limpa e usa o motor nativo
    registrar_erro("import_yt_dlp_externo", erro_import_ytdlp)

    if path_yt_dlp in sys.path:
        sys.path.remove(path_yt_dlp)
    for modulo_nome in list(sys.modules.keys()):
        if modulo_nome == "yt_dlp" or modulo_nome.startswith("yt_dlp."):
            sys.modules.pop(modulo_nome, None)
    shutil.rmtree(path_yt_dlp, ignore_errors=True)
    import yt_dlp

# Pasta raiz do projeto (um nível acima de 'crimson/'); dentro do .exe do PyInstaller é a pasta temporária do executável
caminho_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Localização dinâmica do FFmpeg compatível com diferentes distros Linux, Flatpak, Homebrew e Windows
if SISTEMA == 'Windows':
    caminho_ffmpeg_local = os.path.join(caminho_base, 'ffmpeg')
    os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + caminho_ffmpeg_local
    binario_ffmpeg = shutil.which("ffmpeg")
    caminho_ffmpeg_dir = os.path.dirname(binario_ffmpeg) if binario_ffmpeg else caminho_ffmpeg_local
else:
    binario_ffmpeg = shutil.which("ffmpeg")
    caminho_ffmpeg_dir = os.path.dirname(binario_ffmpeg) if binario_ffmpeg else '/usr/bin'

# --- Limpeza Segura de Processos Filhos ---
def encerrar_processos_filhos():

    # Finaliza apenas processos do FFmpeg criados por esta instância do Crimson (preservando outros apps do usuário)
    meu_pid = os.getpid()

    try:
        if SISTEMA == 'Windows':
            cmd_ps = (
                f"Get-CimInstance Win32_Process -Filter \"ParentProcessId = {meu_pid}\" | "
                "ForEach-Object { "
                "if ($_.Name -ieq 'ffmpeg.exe' -or $_.Name -ieq 'ffprobe.exe') { "
                "Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue "
                "} "
                "Get-CimInstance Win32_Process -Filter \"ParentProcessId = $($_.ProcessId)\" | "
                "Where-Object { $_.Name -ieq 'ffmpeg.exe' -or $_.Name -ieq 'ffprobe.exe' } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } "
                "}"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd_ps],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            subprocess.run(
                ["pkill", "-KILL", "-P", str(meu_pid), "-x", "ffmpeg"],
                capture_output=True
            )
            subprocess.run(
                ["pkill", "-KILL", "-P", str(meu_pid), "-x", "ffprobe"],
                capture_output=True
            )
            res = subprocess.run(["pgrep", "-P", str(meu_pid)], capture_output=True, text=True)
            for linha in res.stdout.splitlines():
                pid_filho = linha.strip()
                if pid_filho.isdigit():
                    subprocess.run(
                        ["pkill", "-KILL", "-P", pid_filho, "-x", "ffmpeg"],
                        capture_output=True
                    )
    except Exception as erro_proc:
        registrar_erro("encerrar_processos_filhos", erro_proc)

# --------------------------------------------------------------------------------------------------------------------
# --- Mecanismo de Pausa Customizado (O Truque da Exceção) ---
# O yt-dlp é excelente, mas não possui uma função nativa de "pausa"
# Para contornar isso, nós criamos nossa própria Classe de Erro (Exception) abaixo. A lógica funciona em 4 passos:
# 1. O yt-dlp aciona o "espião" (a função atualizar_progresso) a cada avanço percentual do download
# 2. Se o usuário tiver clicado no botão Pausa, o espião dispara esse erro abaixo intencionalmente (raise DownloadPausado)
# 3. O disparo do erro corta a linha de execução do yt-dlp na mesma hora, forçando ele a parar e deixar o arquivo '.part' salvo na pasta
# 4. A função 'thread_download' pega esse erro no bloco 'try...except' e simplesmente dá um "pass" (ignora), evitando que o aplicativo quebre ou trave
# Quando o usuário clica em "Continuar", apenas mando ele baixar novamente. O yt-dlp acha o arquivo '.part' na pasta e retoma de onde o corte ocorreu
class DownloadPausado(Exception):
    pass

def localizar_arquivo_final(info, nome_temporario):

    # Depois de todas as conversões, o yt-dlp informa o caminho do arquivo final em 'requested_downloads'
    for item in (info or {}).get('requested_downloads') or []:
        caminho = item.get('filepath')
        if caminho and os.path.exists(caminho):
            return caminho

    # Plano B: procura na pasta temporária pelo nome do download, ignorando arquivos parciais
    candidatos = [
        arq for arq in glob.glob(glob.escape(os.path.join(temp_dir, nome_temporario)) + ".*")
        if not arq.endswith((".part", ".ytdl", ".temp"))
    ]
    if not candidatos:
        raise FileNotFoundError("O arquivo final não foi encontrado na pasta temporária.")
    return max(candidatos, key=os.path.getsize)

def baixar_midia(url, tipo, formato, hook_progresso, nome_temporario):
    # Configurações base de Download (ydl_opts)
    ydl_opts = {
        # O download acontece na pasta temporária do aplicativo, e não direto na pasta que o usuário escolheu
        # (no Flatpak o app só pode escrever no arquivo escolhido pela janela "Salvar como", via portal)
        # O molde termina em '.%(ext)s' para o yt-dlp colocar sozinho a extensão correta, evitando nomes como 'audio.mp3.mp3'
        'outtmpl': os.path.join(temp_dir, nome_temporario + ".%(ext)s"),

        # Conecta a função da nossa barra de progresso no sistema do yt-dlp
        'progress_hooks': [hook_progresso],

        # Indica para o yt-dlp onde encontrar o executável do ffmpeg
        'ffmpeg_location': caminho_ffmpeg_dir,

        # Garante que links contendo listas de reprodução baixem apenas o vídeo individual
        'noplaylist': True,

        # Mostra o progresso no console
        'quiet': False,
        'no_warnings': True,

        # Desativa códigos de cores (ANSI) para que o texto da barra de progresso fique limpo
        'color': 'no_color',

        # Otimização de rede por divisão de blocos e múltiplas conexões
        'concurrent_fragment_downloads': 5,  # Usa 5 conexões simultâneas para baixar os pedaços
        'http_chunk_size': 10485760,         # Divide em blocos de 10MB para download estável
    }

    # Se o usuário escolheu áudio, configuro para extrair o áudio
    if tipo == 'audio':
        ydl_opts['format'] = 'bestaudio/best'  # Pega a melhor qualidade de áudio
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': formato,
            'preferredquality': '192',  # Qualidade do áudio (192kbps é um bom padrão)
        }]

    # Se o usuário escolheu vídeo, configuro para baixar vídeo e áudio juntos
    elif tipo == 'video':
        # Força o download de formatos que sejam naturalmente compatíveis
        # evitando que o FFmpeg precise re-renderizar o vídeo (poupando 100% de CPU)
        if formato == 'mp4':
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

        # O merge_output_format diz ao FFmpeg apenas para juntar o áudio e o vídeo (Muxing)
        ydl_opts['merge_output_format'] = formato

    # Evita exibir a URL bruta no terminal para proteger tokens/links privado
    print(f"[*] Preparando para baixar mídia ({tipo} - {formato})...")

    # Inicializa o yt-dlp com as configurações preparadas e dispara o download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    print("[*] Download concluído com sucesso")

    # Devolve o caminho do arquivo final (já convertido ou mesclado) que ficou na pasta temporária
    return localizar_arquivo_final(info, nome_temporario)