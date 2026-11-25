# Projeto Crimson - Motor de download (yt-dlp + FFmpeg), pausa e limpeza de processos
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import os           # Biblioteca para interagir com o sistema operacional (caminhos, variáveis de ambiente e PID)
import errno        # Códigos de erro do sistema (ex: ENOSPC = disco cheio)
import sys          # Necessário para identificar se está rodando como .exe e para ajustar o caminho de importação
import glob         # Para procurar arquivos na pasta temporária pelo nome
import shutil       # Usado para limpeza segura de pastas temporárias e localização de binários no sistema
import subprocess   # Usado para executar comandos do sistema (como atualizar o yt-dlp ou finalizar processos)
import time         # Usado para saber a idade dos arquivos que sobraram na pasta temporária
import re           # Expressões regulares, são bem úteis para manipular, localizar e filtrar strings

from crimson.config import SISTEMA, lib_dir, temp_dir, registrar_erro

# --- Injeção de Dependência Modular com Autorrecuperação ---
# Procura se o motor do yt-dlp já foi baixado na pasta Lib
# Se existir, força o Python a ler as bibliotecas dessa pasta antes das bibliotecas congeladas (PyInstaller)
path_yt_dlp = os.path.join(lib_dir, 'yt-dlp-master')

# Atualização baixada na execução anterior: ela fica guardada em 'yt-dlp-novo' e só entra no lugar agora,
# antes do import, para nunca apagar arquivos de um motor que está em uso
path_yt_dlp_novo = os.path.join(lib_dir, 'yt-dlp-novo')
if os.path.isfile(os.path.join(path_yt_dlp_novo, 'yt_dlp', '__init__.py')):
    try:
        shutil.rmtree(path_yt_dlp, ignore_errors=True)
        os.replace(path_yt_dlp_novo, path_yt_dlp)
    except OSError as erro_troca:
        registrar_erro("trocar_motor_yt_dlp", erro_troca)

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
# Ela herda de 'DownloadCancelled' (a exceção de cancelamento do próprio yt-dlp) porque, em playlists, o yt-dlp
# pula qualquer outro erro e segue para o próximo vídeo; o cancelamento é o único erro que ele sempre deixa passar
class DownloadPausado(yt_dlp.utils.DownloadCancelled):
    pass

# --- Limpeza de Restos Antigos na Pasta Temporária ---
def limpar_temp_antigo(horas=24):

    # Apaga da pasta temporária o que ficou para trás há mais de 'horas' (ex: depois de uma queda de energia)
    # Itens recentes são preservados, pois podem ser um download pausado de outra janela do Crimson
    limite = time.time() - horas * 3600
    try:
        for nome in os.listdir(temp_dir):
            caminho = os.path.join(temp_dir, nome)
            try:
                if os.path.getmtime(caminho) < limite:
                    if os.path.isdir(caminho):
                        shutil.rmtree(caminho, ignore_errors=True)
                    else:
                        os.remove(caminho)
            except OSError:
                pass
    except OSError as erro_limpeza:
        registrar_erro("limpar_temp_antigo", erro_limpeza)

# --- Detecção de Disco Cheio ---
def erro_disco_cheio(erro):

    """
    Descobre se um erro foi causado por falta de espaço em disco
    O yt-dlp costuma "embrulhar" o erro original do sistema dentro do dele, então procura em toda a cadeia de erros:
    -> Linux/macOS: OSError com errno 28 (ENOSPC, "No space left on device")
    -> Windows: OSError com winerror 112 (ERROR_DISK_FULL)
    """

    vistos = set()
    while erro is not None and id(erro) not in vistos:
        vistos.add(id(erro))
        if isinstance(erro, OSError) and (erro.errno == errno.ENOSPC or getattr(erro, 'winerror', None) == 112):
            return True
        texto = str(erro)
        if "No space left on device" in texto or "not enough space on the disk" in texto:
            return True

        # Próximo elo da cadeia: o erro original guardado pelo yt-dlp (exc_info) ou pelo próprio Python (__cause__/__context__)
        exc_info = getattr(erro, 'exc_info', None)
        if exc_info and len(exc_info) > 1 and exc_info[1] is not erro:
            erro = exc_info[1]
        else:
            erro = erro.__cause__ or erro.__context__
    return False

# --- Tradução de Erros para o Usuário ---
# O yt-dlp devolve mensagens técnicas em inglês (ex: "ERROR: [youtube] abc: Private video. Sign in if...")
# Esta lista liga trechos dessas mensagens a uma chave do dicionário de idiomas, com um texto amigável e traduzido
# A ordem importa e a primeira categoria que bater vence (ex: "Private video. Sign in..." deve virar "indisponível", não "login")
CATEGORIAS_ERRO = [
    ("erro_ao_vivo",       ["live event will begin", "premieres in", "this live event", "is upcoming", "will begin in"]),
    ("erro_drm",           ["drm"]),
    ("erro_regiao",        ["not available in your country", "in your country", "from your location", "geo restrict", "geo-restrict"]),
    ("erro_bloqueio",      ["http error 429", "too many requests", "rate-limit", "rate limit", "http error 403", "forbidden"]),
    ("erro_indisponivel",  ["private video", "this video is private", "has been removed", "http error 404", "http error 410"]),
    ("erro_login",         ["sign in", "log in", "logged-in", "logged in", "login", "confirm your age", "age-restricted", "age restricted",
                            "inappropriate for some users", "members-only", "members only", "join this channel", "cookies", "authentication",
                            "purchase", "payment", "rental", "premium"]),
    ("erro_formato",       ["requested format is not available", "format is not available", "no video formats found", "no formats found"]),
    ("erro_conversao",     ["ffmpeg", "ffprobe", "postprocessing", "conversion failed", "invalid data found"]),  # Antes de "not found", por causa do "ffmpeg not found"
    ("erro_indisponivel",  ["unavailable", "does not exist", "not found", "been deleted", "terminated", "no longer available"]),
    ("erro_conexao",       ["unable to download", "getaddrinfo", "name or service not known", "temporary failure in name resolution",
                            "timed out", "connection", "network is unreachable", "urlopen error", "http error 5", "ssl"]),
    ("erro_link_invalido", ["unsupported url", "is not a valid url", "not a valid url"]),
    ("erro_permissao",     ["permission denied", "errno 13", "read-only file system", "errno 30", "access is denied", "winerror 5"]),
]

def classificar_erro(mensagem):

    # Devolve a chave do dicionário de idiomas com a explicação amigável do erro (ou a genérica, se nenhuma bater)
    texto = str(mensagem).lower()
    
    for chave, trechos in CATEGORIAS_ERRO:
        if any(trecho in texto for trecho in trechos):
            return chave
    return "erro_desconhecido"

def espaco_livre(*pastas):

    # Devolve o menor espaço livre (em bytes) entre as pastas informadas (a pasta temporária e a de destino)
    livres = []
    for pasta in pastas:
        if pasta and os.path.isdir(pasta):
            try:
                livres.append(shutil.disk_usage(pasta).free)
            except OSError:
                pass
    return min(livres) if livres else 0

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

# Qualidades disponíveis (valores internos, salvos no JSON)
# Áudio: taxa de bits em kbps | Vídeo: altura máxima em pixels | "melhor" = a maior que o site oferecer
QUALIDADES_AUDIO = ["melhor", "320", "192", "128"]
QUALIDADES_VIDEO = ["melhor", "2160", "1440", "1080", "720", "480", "360"]

def arquivos_da_playlist(pasta_playlist):

    # Lista os arquivos prontos de uma playlist (ignorando os parciais), em ordem, junto com o título de cada um
    # O título vem do próprio nome do arquivo, que o yt-dlp montou como "001 - Título.ext"
    arquivos = []
    for arq in sorted(glob.glob(os.path.join(glob.escape(pasta_playlist), "*"))):
        if os.path.isfile(arq) and not arq.endswith((".part", ".ytdl", ".temp")):
            arquivos.append((arq, os.path.splitext(os.path.basename(arq))[0]))
    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo da playlist foi encontrado na pasta temporária.")
    return arquivos

class RegistradorPlaylist:

    """
    "Ouvinte" das mensagens do yt-dlp usado nas playlists
    Lá o yt-dlp pula os vídeos que falham e só escreve o erro no terminal; com este registrador
    ele guarda esses erros numa lista, para avisar o usuário no final (e descobrir se o disco encheu)
    """

    def __init__(self, falhas):
        self.falhas = falhas

    def debug(self, mensagem):
        # As linhas de progresso ("[download]  42.0% ...") chegam aqui o tempo todo: não imprimo para não poluir o terminal
        if not mensagem.startswith('[download]'):
            print(mensagem)

    def info(self, mensagem):
        self.debug(mensagem)

    def warning(self, mensagem):
        pass

    def error(self, mensagem):
        print(mensagem)
        self.falhas.append(mensagem)

# --- Conversão de Links do Vimeo ---
# Desde 2026 o Vimeo exige login para ler a página comum do vídeo (vimeo.com/ID), e o yt-dlp falha com
# "The web client only works when logged-in". Já o player embutido (player.vimeo.com/video/ID) funciona sem login
# reconhece padrões como 'vimeo.com/ID', 'vimeo.com/ID/CODIGO' (vídeo não listado), 'vimeo.com/channels/NOME/ID',
# 'vimeo.com/groups/NOME/videos/ID', 'vimeo.com/album/NOME/video/ID', 'vimeo.com/showcase/NOME/video/ID', 'vimeo.com/video/ID' e 'vimeo.com/m/ID'
# links de coleções inteiras (showcase, álbuns, perfis) não batem com o padrão e seguem sem alteração
# '[0-9]' em vez de '\d': no Python, '\d' também aceita dígitos de outros alfabetos (ex: os arábicos '١٢٣')
# O código do vídeo não listado tem sempre 10 caracteres hexadecimais, a mesma regra usada pelo yt-dlp
# re.IGNORECASE ignora maiúsculas e minúsculas (ex: 'VIMEO.com' também é reconhecido)
PADRAO_LINK_VIMEO = re.compile(
    r'^https?://(?:www\.)?vimeo\.com/'
    r'(?:channels/[^/]+/|groups/[^/]+/videos/|(?:album|showcase)/[^/]+/video/|videos?/|m/)?'
    r'([0-9]+)(?:/([0-9a-f]{10}))?/?(?:[?#].*)?$',
    re.IGNORECASE
)

def converter_link_vimeo(url):
    
    # Devolve o link do player embutido, qualquer link que não seja de um vídeo do Vimeo volta igual
    encontrado = PADRAO_LINK_VIMEO.match(url.strip())
    
    if not encontrado:
        return url

    id_video, codigo_privado = encontrado.groups()
    link_player = f"https://player.vimeo.com/video/{id_video}"
    
    # Vídeos não listados precisam do código extra, que no player vai no parâmetro '?h='
    if codigo_privado:
        link_player += f"?h={codigo_privado}"
    return link_player

def baixar_midia(url, tipo, formato, hook_progresso, nome_temporario, qualidade="melhor", baixar_playlist=False, falhas=None):

    """
    Baixa a mídia na pasta temporária e devolve uma LISTA de tuplas (caminho_do_arquivo, titulo)
    -> Vídeo único: lista com 1 item
    -> Playlist (com o switch ligado): um item para cada vídeo baixado
    'falhas' é uma lista opcional onde anoto os erros dos vídeos da playlist que não puderam ser baixados
    """

    if falhas is None:
        falhas = []

    # Links comuns do Vimeo passam a usar o player embutido, que não exige login
    url = converter_link_vimeo(url)

    # O download acontece na pasta temporária do aplicativo, e não direto na pasta que o usuário escolheu
    # (no Flatpak o app só pode escrever nos locais liberados pelo portal)
    # O molde termina em '.%(ext)s' para o yt-dlp colocar sozinho a extensão correta, evitando nomes como 'audio.mp3.mp3'
    if baixar_playlist:
        # Cada playlist ganha uma subpasta própria, e cada arquivo leva o número na lista + o título
        # '%(playlist_index|)03d' escreve o número com 3 dígitos (001, 002...) para os arquivos ficarem em ordem,
        # e '%(playlist_index& - |)s' coloca o " - " depois dele; os dois ficam vazios se o link não for uma playlist
        pasta_playlist = os.path.join(temp_dir, nome_temporario)
        molde_saida = os.path.join(pasta_playlist, "%(playlist_index|)03d%(playlist_index& - |)s%(title).150B.%(ext)s")
    else:
        molde_saida = os.path.join(temp_dir, nome_temporario + ".%(ext)s")

    # Configurações base de Download (ydl_opts)
    ydl_opts = {
        'outtmpl': molde_saida,

        # Conecta a função da nossa barra de progresso no sistema do yt-dlp
        'progress_hooks': [hook_progresso],

        # Indica para o yt-dlp onde encontrar o executável do ffmpeg
        'ffmpeg_location': caminho_ffmpeg_dir,

        # Switch desligado: links com listas de reprodução baixam apenas o vídeo individual
        # Switch ligado: baixa a playlist inteira, pulando vídeos indisponíveis em vez de parar tudo
        'noplaylist': not baixar_playlist,
        'ignoreerrors': 'only_download' if baixar_playlist else False,

        # Mostra o progresso no console
        'quiet': False,
        'no_warnings': True,

        # Desativa códigos de cores (ANSI) para que o texto da barra de progresso fique limpo
        'color': 'no_color',

        # Otimização de rede por divisão de blocos e múltiplas conexões
        'concurrent_fragment_downloads': 5,  # Usa 5 conexões simultâneas para baixar os pedaços
        'http_chunk_size': 10485760,         # Divide em blocos de 10MB para download estável
    }

    if baixar_playlist:
        # Guarda os erros dos vídeos pulados (ver RegistradorPlaylist)
        ydl_opts['logger'] = RegistradorPlaylist(falhas)
    else:
        # O 'noplaylist' só vale para links que são vídeo E playlist ao mesmo tempo (ex: watch?v=...&list=...)
        # Num link que é só de playlist, o yt-dlp baixaria tudo; aqui limito ao primeiro vídeo
        ydl_opts['playlist_items'] = '1'

    # Se o usuário escolheu áudio, configuro para extrair o áudio
    if tipo == 'audio':
        ydl_opts['format'] = 'bestaudio/best'  # Pega a melhor qualidade de áudio
        # No yt-dlp, '0' significa a melhor qualidade variável (VBR); valores como '320' são a taxa de bits em kbps
        # (formatos sem perda, como wav e flac, ignoram esse valor)
        qualidade_audio = '0' if qualidade == "melhor" else qualidade
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': formato,
            'preferredquality': qualidade_audio,
        }]
        # Avisa o yt-dlp da extensão final: assim, ao retomar uma playlist, ele reconhece os áudios
        # que já foram convertidos e não baixa tudo de novo
        ydl_opts['final_ext'] = formato

    # Se o usuário escolheu vídeo, configuro para baixar vídeo e áudio juntos
    elif tipo == 'video':
        # Força o download de formatos que sejam naturalmente compatíveis
        # evitando que o FFmpeg precise re-renderizar o vídeo (poupando 100% de CPU)
        # Limite de altura (ex: '[height<=1080]'); vazio quando a escolha é a melhor qualidade
        limite = '' if qualidade == "melhor" else f'[height<={qualidade}]'

        # O '/best' no final é a última alternativa: se nada respeitar o limite, baixa o que existir em vez de falhar
        if formato == 'mp4':
            ydl_opts['format'] = f'bestvideo{limite}[ext=mp4]+bestaudio[ext=m4a]/bestvideo{limite}+bestaudio/best{limite}/best'
        else:
            ydl_opts['format'] = f'bestvideo{limite}+bestaudio/best{limite}/best'

        # O merge_output_format diz ao FFmpeg apenas para juntar o áudio e o vídeo (Muxing)
        ydl_opts['merge_output_format'] = formato

    # Evita exibir a URL bruta no terminal para proteger tokens/links privado
    print(f"[*] Preparando para baixar mídia ({tipo} - {formato})...")

    # Inicializa o yt-dlp com as configurações preparadas e dispara o download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    print("[*] Download concluído com sucesso")

    # Devolve os arquivos finais (já convertidos ou mesclados) que ficaram na pasta temporária
    if baixar_playlist:
        # Se algum vídeo falhou por falta de espaço, trato como disco cheio (o app pausa e avisa o usuário)
        for mensagem in falhas:
            if "No space left on device" in mensagem or "not enough space on the disk" in mensagem:
                raise OSError(errno.ENOSPC, mensagem)
        try:
            return arquivos_da_playlist(pasta_playlist)
        except FileNotFoundError:
            # Nenhum vídeo deu certo: mostra o primeiro erro do yt-dlp, que explica melhor o motivo
            if falhas:
                raise RuntimeError(falhas[0])
            raise

    # Link de playlist com o switch desligado: o yt-dlp devolve a playlist, então uso o primeiro vídeo dela
    if info and info.get('_type') == 'playlist' and info.get('entries'):
        info = next((item for item in info['entries'] if item), info)
    titulo = (info or {}).get('title') or nome_temporario
    return [(localizar_arquivo_final(info, nome_temporario), titulo)]