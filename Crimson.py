# Projeto Crimson - Uma interface capaz de baixar vídeos do youtube de forma simples
# Criei esse projeto pela necessidade de uma ferramente útil e confiável para tal, nascendo assim ele :D

import os # Biblioteca para interagir com o sistema operacional (ex: navegar entre pastas, verificar se um arquivo existe, criar pastas e ler variáveis)
import sys # Necessário para identificar se está rodando como .exe
import glob # Para manipulação dos caminhos dos arquivos, além de ajudar na exclusão dos arquivos residuiais
import tkinter as tk # Biblioteca para a interface gráfica (nativa do python)
from tkinter import ttk # Necessário para elementos mais modernos como a Barra de Progresso
from tkinter import messagebox # Para exibir mensagens de alerta/sucesso na tela
from tkinter import filedialog # Para usar o "Salvar Como" nativo do Windows
import threading # Biblioteca para criar rotinas em segundo plano (evita que a tela trave)
import re # Usado para limpar textos gerados pelo yt-dlp
import subprocess # Usado para executar comandos do sistema (como atualizar o yt-dlp)
import webbrowser # Usado para abrir links na internet (como no caso dos links dos repositório usados)
import customtkinter as ctk # Biblioteca para conseguir estilizar melhor o aplicativo
import json # Biblioteca nativa para salvar e ler dados configurados usando esse formato de arquivo
import urllib.request # Biblioteca nativa para baixar arquivos da internet
import zipfile # Biblioteca nativa para extrair arquivos compactados
from PIL import Image # Biblioteca 'Pillow', não é nativa e ajuda na manipulação de imagens

# -------------------------------
# --- Setup de Diretórios do Aplicativo (AppData) e Persistência ---

# garantindo que o aplicativo salva os dados na pasta oficial do Windows para programas (Local AppData)
# Em vez de sujar o disco ou perder dados quando o usuário move a pasta
appdata_local = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
crimson_dir = os.path.join(appdata_local, 'Crimson')
lib_dir = os.path.join(crimson_dir, 'Lib')
config_dir = os.path.join(crimson_dir, 'Config')
config_file = os.path.join(config_dir, 'config.json')

# Cria as pastas caso elas não existam no computador desse usuário
os.makedirs(lib_dir, exist_ok=True)
os.makedirs(config_dir, exist_ok=True)

# --- Injeção de Dependência Modular ---
# Procura se o motor do yt-dlp já foi baixado na pasta Lib
# Se existir, forço o Python a ler as bibliotecas dessa pasta, ignorando bibliotecas nativas congeladas (PyInstaller)
path_yt_dlp = os.path.join(lib_dir, 'yt-dlp-master')

if os.path.exists(path_yt_dlp):
    sys.path.insert(0, path_yt_dlp) # O insert 0 diz pro Python: "Olhe aqui antes de qualquer outro lugar"

import yt_dlp # Agora sim ela é importada (Se a injeção existia, ele pegou a atualizada, senão, pegou a local como fallback)

# -------------------------------
# *******************************
# -------------------------------

# --- Funções de Leitura e Escrita do JSON ---
def carregar_configuracoes():
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass # Se o arquivo estiver corrompido, só ignora e retorna o padrão
    return {"idioma": "Portuguese", "tema": "Dark"}

def salvar_configuracoes(idioma, tema):
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({"idioma": idioma, "tema": tema}, f, indent=4)
        return True
    except:
        return False

# dicionário global de idiomas, uma tupla com os textos traduzidos em diferentes idiomas
config_atual = carregar_configuracoes()
idioma_atual = config_atual.get("idioma", "Portuguese")
tema_atual = config_atual.get("tema", "Dark") # Definindo um tema padrão (Claro ou Escuro)

# Definindo cores em tons pastéis para manter a harmonia visual de forma simples
TEMAS = {
    
    "Egg": {
        "cor_fundo_janela":             "#E9E3BC",              # cor de fundo da janela
        "cor_do_texto":                 "#333333",              # cor do texto
        "cor_botao_audio":              "#F2CC8F",              # cor do botão de áudio
        "cor_botao_audio_hover":        "#F4D49F",              # cor de dentro do botão quando o momento do hover acontece
        "cor_botao_video":              "#EDD66F",              # cor do botão de vídeo
        "cor_botao_video_hover":        "#EBCF6C",              # cor de dentro do botão quando o momento do hover acontece
        "cor_fonte_botoes":             "#333333",              # cor da fonte dos botões 
        "cor_barra_de_pesquisa":        "#FCF8E9",              # cor da barra de pesquisa
        "cor_texto_caixa_de_pesquisa":  "#725C04",              # cor do texto dentro da barra de pesquisa
        "cor_de_fundo_dropdown":        "#F2E9C4",              # cor de fundo dentro do dropdown
        "cor_do_hover_dropdown":        "#61612F",              # cor quando o mouse passa por cima
        "cor_da_borda_botao_video":     "#F5DD6E",              # cor da borda do vídeo
        "cor_da_borda_botao_audio":     "#F8E3BF",              # cor da borda do áudio
        "cor_do_texto_magua":           "#696969"               # cor da marca d' água
    },
    
    "Dark": {
        "cor_fundo_janela":             "#36363F",              # cor de fundo da janela
        "cor_do_texto":                 "#EDF2F4",              # cor do texto
        "cor_botao_audio":              "#8D99AE",              # cor do botão de áudio
        "cor_botao_audio_hover":        "#9EA9BD",              # cor de dentro do botão quando o momento do hover acontece
        "cor_botao_video":              "#457B9D",              # cor do botão de vídeo
        "cor_botao_video_hover":        "#568CAE",              # cor de dentro do botão quando o momento do hover acontece
        "cor_fonte_botoes":             "#FFFFFF",              # cor da fonte dos botões
        "cor_barra_de_pesquisa":        "#797986",              # cor da barra de pesquisa
        "cor_texto_caixa_de_pesquisa":  "#EDF2F4",              # cor do texto dentro da barra de pesquisa
        "cor_de_fundo_dropdown":        "#606071",              # cor de fundo dentro do dropdow
        "cor_do_hover_dropdown":        "#494949",              # cor quando o mouse passa por cima
        "cor_da_borda_botao_video":     "#325971",              # cor da borda do vídeo
        "cor_da_borda_botao_audio":     "#6A7A95",              # cor da borda do áudio
        "cor_do_texto_magua":           "#C9C9C9"               # cor da marca d' água
    },

    "Matcha": {
        "cor_fundo_janela":             "#B2CC8E",              # cor de fundo da janela
        "cor_do_texto":                 "#1B272C",              # cor do texto
        "cor_botao_audio":              "#5C7341",              # cor do botão de áudio
        "cor_botao_audio_hover":        "#6B864B",              # cor de dentro do botão quando o momento do hover acontece
        "cor_botao_video":              "#648C24",              # cor do botão de vídeo
        "cor_botao_video_hover":        "#77A62B",              # cor de dentro do botão quando o momento do hover acontece
        "cor_fonte_botoes":             "#FFFFFF",              # cor da fonte dos botões
        "cor_barra_de_pesquisa":        "#DBE6D1",              # cor da barra de pesquisa
        "cor_texto_caixa_de_pesquisa":  "#213313",              # cor do texto dentro da barra de pesquisa
        "cor_de_fundo_dropdown":        "#9AB086",              # cor de fundo dentro do dropdow
        "cor_do_hover_dropdown":        "#696969",              # cor quando o mouse passa por cima
        "cor_da_borda_botao_video":     "#5D8321",              # cor da borda do vídeo
        "cor_da_borda_botao_audio":     "#688548",              # cor da borda do áudio
        "cor_do_texto_magua":           "#375223"               # cor da marca d' água
    }
}

DICIONARIO_IDIOMAS = {
    "instrucao_init": {
        "Portuguese":       "Procurando atualizações de segurança...",
        "English":          "Checking for security updates..."
    },
    "instrucao_ready": {
        "Portuguese":       "Insira a URL do vídeo do YouTube:",
        "English":          "Enter the YouTube video URL:"
    },
    "cor_botao_audio": {
        "Portuguese":       "Baixar Áudio",
        "English":          "Download Audio"
    },
    "cor_botao_video": {
        "Portuguese":       "Baixar Vídeo",
        "English":          "Download Video"
    },
    "aba_sistema": {
        "Portuguese":       "Sistema",
        "English":          "System"
    },
    "aba_sobre": {
        "Portuguese":       "Sobre",
        "English":          "About"
    },
    "lbl_idioma": {
        "Portuguese":       "Idioma do Aplicativo:",
        "English":          "Application Language:"
    },
    "lbl_tema": {
        "Portuguese":       "Tema da Interface:",
        "English":          "Interface Theme:"
    },
    "lbl_versao": {
        "Portuguese":       "Versão atual: V.1.0.0",
        "English": "        Current version: V.1.0.0"
    },
    "txt_disclaimer": {
        "Portuguese":       "Desenvolvido sem fins comerciais\nQualquer distribuição deve ser gratuita\ne livre para todos\n",
        "English":          "Developed for non-commercial purposes\nAny distribution must be free\nand available to everyone\n"
    },
    "lbl_creditos": {
        "Portuguese":       "Créditos e agradecimentos à comunidade Open Source\n",
        "English":          "Credits and thanks to the Open Source community\n"
    },
    "link_crimson": {
        "Portuguese":       " Repositório Crimson",
        "English":          " Crimson Repository"
    },
    "link_ytdlp": {
        "Portuguese":       " Repositório yt-dlp",
        "English":          " yt-dlp Repository"
    },
    "link_ffmpeg": {
        "Portuguese":       " Repositório FFmpeg",
        "English":          " FFmpeg Repository"
    },
    "marca_dagua": {
        "Portuguese":       "Desenvolvido por LuanDevCodes",
        "English":          "Developed by LuanDevCodes"
    },
    "msg_sucesso_titulo": {
        "Portuguese":       "Sucesso",
        "English":          "Success"
    },
    "msg_sucesso_texto": {
        "Portuguese":       "Download e conversão concluídos com sucesso",
        "English":          "Download and conversion completed successfully"
    },
    "msg_erro_titulo": {
        "Portuguese":       "Erro",
        "English":          "Error"
    },
    "msg_erro_generico": {
        "Portuguese":       "Ocorreu um erro durante o download:\n",
        "English":          "An error occurred during the download:\n"
    },
    "msg_aviso_titulo": {
        "Portuguese":       "Aviso",
        "English":          "Warning"
    },
    "msg_aviso_url": {
        "Portuguese":       "Por favor, insira uma URL válida do YouTube",
        "English":          "Please enter a valid YouTube URL"
    },
    "progresso_baixando": {
        "Portuguese":       "Baixando",
        "English":          "Downloading"
    },
    "progresso_vel": {
        "Portuguese":       "Velocidade",
        "English":          "Speed"
    },
    "progresso_tempo": {
        "Portuguese":       "Tempo Restante",
        "English":          "ETA"
    },
    "progresso_init": {
        "Portuguese":       "Iniciando Download...",
        "English":          "Starting Download..."
    },
    "progresso_convertendo": {
        "Portuguese":       "Baixado - Aguarde a conversão (FFmpeg)...",
        "English":          "Downloaded - Please wait for conversion (FFmpeg)..."
    },
    "btn_baixar_inativo": {
        "Portuguese":       "Preparando...",
        "English":          "Preparing..."
    },
    "msg_excluir_titulo": {
        "Portuguese":       "Excluir Download",
        "English":          "Delete Download"
    },
    "msg_excluir_texto": {
        "Portuguese":       "Tem certeza que deseja cancelar e excluir o progresso desse download?",
        "English":          "Are you sure you want to cancel and delete the progress of this download?"
    },
    "msg_salvar_como": {
        "Portuguese":       "Salvar como...",
        "English":          "Save as..."
    }
}

# -------------------------------
# *******************************
# -------------------------------

caminho_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
caminho_ffmpeg_dir = os.path.join(caminho_base, 'ffmpeg') # Pasta do ffmpeg

# Adiciona a pasta do ffmpeg ao PATH do sistema apenas durante a execução do código
# é o método mais garantido para o yt-dlp (e qualquer outra lib) achar o ffmpeg no Windows
# é uma trava de segurança, funcionaria sem essa camada mas por via das dúvidas
os.environ["PATH"] = os.environ["PATH"] + os.pathsep + caminho_ffmpeg_dir

# --------------------------------------------------------------------------------------------------------------------
# ********************************************************************************************************************
# --------------------------------------------------------------------------------------------------------------------

# função responsável por baixar áudios ou vídeos do youtube
# --------------------------------------------------------------------------------------------------------------------
# --- Mecanismo de Pausa Customizado (O Truque da Exceção) ---
# O yt-dlp é excelente, mas não possui uma função nativa de "pausa"
# Para contornar isso, nós criamos nossa própria Classe de Erro (Exception) abaixo. A lógica funciona em 4 passos:
# 1. O yt-dlp aciona o "espião" (a função atualizar_progresso) a cada avanço percentual do download
# 2. Se o usuário tiver clicado no botão Pausa, o espião dispara esse erro abaixo intencionalmente (raise DownloadPausado)
# 3. O disparo do erro corta a linha de execução do yt-dlp na mesma hora, forçando ele a parar e deixar o arquivo '.part' salvo na pasta
# 4. A função 'thread_download' que estava rodando lá embaixo pega esse erro no bloco 'try...except' e simplesmente dá um "pass" (ignora), evitando que o aplicativo quebre ou trave
# Quando o usuário clica em "Continuar", apenas mando ele baixar novamente. O yt-dlp é inteligente, acha o arquivo '.part' na pasta e retoma de onde o corte ocorreu
class DownloadPausado(Exception):
    pass

estado_download = "parado" # "rodando", "pausado", "cancelado"
url_atual = ""
caminho_salvamento_atual = ""
tipo_atual = ""
formato_atual = ""

def baixar_midia_youtube(url, tipo, formato, hook_progresso, caminho_completo):

    # Configurações base de Download (ydl_opts)
    ydl_opts = {
        
        # Define o caminho exato de saída já com nome e extensão que o usuário escolheu
        'outtmpl': caminho_completo,
        
        # Conecta a função da nossa barra de progresso no sistema do yt-dlp
        'progress_hooks': [hook_progresso],
        
        # Indica para o yt-dlp onde encontrar o executável do ffmpeg
        'ffmpeg_location': caminho_ffmpeg_dir,
        
        # Mostra o progresso no console
        'quiet': False,
        'no_warnings': True,
        
        # Desativa códigos de cores (ANSI) para que o texto da barra de progresso fique limpo
        'color': 'no_color',
        
        # Bypasses para evitar limitador de velocidade do YouTube (Throttling) e compensar o uso do módulo puro
        # aconteceu depois que passei a usar a biblioteca de forma modular, com isso a velocidade dos meus testes iniciais volta ao normal
        'concurrent_fragment_downloads': 5, # Usa 5 conexões simultâneas para baixar os pedaços
        'http_chunk_size': 10485760,        # Divide em blocos de 10MB para download rápido
    }

    # Se o usuário escolheu áudio, configuro para extrair o áudio
    if tipo == 'audio':
        
        ydl_opts['format'] = 'bestaudio/best' # Pega a melhor qualidade de áudio
        
        # faço uso do postprocessor do yt-dlp que usa o ffmpeg para converter para o formato desejado (ex: mp3)
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': formato,
            'preferredquality': '192', # Qualidade do áudio (192kbps é um bom padrão)
        }]
    
    # Se o usuário escolheu vídeo, configuro para baixar vídeo e áudio juntos
    elif tipo == 'video':
        
        # Força o download de formatos que sejam naturalmente compatíveis
        # com o que o usuário pediu, evitando que o FFmpeg precise re-renderizar o vídeo (poupando 100% de CPU, experiência pessoal)
        if formato == 'mp4':
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            
        # O merge_output_format diz ao FFmpeg apenas para juntar o áudio e o vídeo (Muxing)
        # Isso leva pouco tempo e não gasta muito de CPU, diferentemente do FFmpegVideoConvertor
        ydl_opts['merge_output_format'] = formato

    print(f"[*] Preparando para baixar ({tipo} - {formato}): {url}")
    
    # Inicializa o yt-dlp com as configurações preparadas e dispara o download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    print(f"[*] Download concluído - Verifique a pasta '{caminho_salvamento_atual}'")

# -------------------------------
# *******************************
# -------------------------------

# Criando uma trava de segurança para caso eu use o Crimson como parte de uma automação ou outro projeto,
# evita que ele rode por completo se for "exportado" por assim dizer, ou seja, pode ser instanciado por funções específicas
if __name__ == '__main__':
    
    # --------------------------------------------------------------------------------------
    # funções para lidar com os processos em segundo plano e não travar a tela
    # --------------------------------------------------------------------------------------
    
    # Função que lida com as informações recebidas em tempo real do yt-dlp
    def atualizar_progresso(d):
        
        global estado_download
        
        # Injeta a trava de segurança para o Pausar/Cancelar
        if estado_download == "pausado":
            raise DownloadPausado("Download interrompido pelo usuário.")
            
        if d['status'] == 'downloading':
            try:
                # O yt-dlp pode mandar caracteres de cor para o console, usarei o re (Regex) para limpar tudo e pegar só o número
                percentual_str = d.get('_percent_str', '0%').strip()
                percentual_limpo = re.sub(r'\x1b\[[0-9;]*[mK]', '', percentual_str).replace('%', '')
                percentual_float = float(percentual_limpo)
                
                # pegando a velocidade e o ETA, e limpando para caso venham com cores residuais
                eta = re.sub(r'\x1b\[[0-9;]*[mK]', '', d.get('_eta_str', 'N/A')).strip()
                velocidade = re.sub(r'\x1b\[[0-9;]*[mK]', '', d.get('_speed_str', 'N/A')).strip()
                
                # Adiciona um espaço entre o número e a unidade de medida da velocidade (ex: 59.26MiB/s -> 59.26 MiB/s)
                # estava me dando toque
                velocidade = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', velocidade)
                
                # Formatação bem mais bonita e com um espaçamento visual agradável
                texto = f"{DICIONARIO_IDIOMAS['progresso_baixando'][idioma_atual]}: {percentual_float:.1f}%   |   {DICIONARIO_IDIOMAS['progresso_vel'][idioma_atual]}: {velocidade}   |   {DICIONARIO_IDIOMAS['progresso_tempo'][idioma_atual]}: {eta}"
                
                # Atualiza a UI com segurança, o "after(0, ...)" diz pro Tkinter rodar isso assim que puder na thread principal
                janela.after(0, set_progresso_ui, percentual_float, texto)
            except:
                pass
        elif d['status'] == 'finished':
            janela.after(0, set_progresso_ui, 100, DICIONARIO_IDIOMAS["progresso_convertendo"][idioma_atual])

    # Atualiza os componentes visuais de fato
    def set_progresso_ui(valor, texto):
        barra_progresso['value'] = valor
        label_progresso.config(text=texto)

    # Função chamada quando a conversão e o download terminam
    def finalizar_com_sucesso(tipo, formato):
        messagebox.showinfo(DICIONARIO_IDIOMAS["msg_sucesso_titulo"][idioma_atual], DICIONARIO_IDIOMAS["msg_sucesso_texto"][idioma_atual])
        entrada_url.delete(0, tk.END)
        restaurar_botoes()
        
    def finalizar_com_erro(mensagem_erro):
        messagebox.showerror(DICIONARIO_IDIOMAS["msg_erro_titulo"][idioma_atual], f"{DICIONARIO_IDIOMAS['msg_erro_generico'][idioma_atual]}{mensagem_erro}")
        restaurar_botoes()
        
    def restaurar_botoes():
        botao_baixar_audio.configure(state=tk.NORMAL, text=DICIONARIO_IDIOMAS["cor_botao_audio"][idioma_atual])
        botao_baixar_video.configure(state=tk.NORMAL, text=DICIONARIO_IDIOMAS["cor_botao_video"][idioma_atual])
        barra_progresso.pack_forget() # Esconde a barra da tela
        label_progresso.pack_forget() # Esconde o texto da tela
        
        entrada_url.configure(state=tk.NORMAL) # Desbloqueia a URL
        
        # Desativa os controles e torna a imagem translúcida
        botao_pausar.configure(state="disabled", image=img_pausa_inativa)
        botao_continuar.configure(state="disabled", image=img_continuar_inativa)
        botao_excluir.configure(state="disabled", image=img_excluir_inativa)

    # --------------------------------------------------------------------------------------
    # --- Funções de Controle (Pausar, Retomar e Excluir) ---
    def acionar_pausa():
        global estado_download
        
        estado_download = "pausado"
        botao_pausar.configure(state="disabled", image=img_pausa_inativa)
        botao_continuar.configure(state="normal", image=img_continuar)
        botao_excluir.configure(state="normal", image=img_excluir) # Só pode excluir se pausar antes, para evitar erros de arquivos abertos

    def acionar_retomar():
        global estado_download
        
        estado_download = "rodando"
        botao_pausar.configure(state="normal", image=img_pausa)
        botao_continuar.configure(state="disabled", image=img_continuar_inativa)
        botao_excluir.configure(state="disabled", image=img_excluir_inativa)
        
        # Cria a thread novamente para retomar o yt-dlp
        threading.Thread(target=thread_download, daemon=True).start()

    def acionar_excluir():
        
        # Exibe um alerta nativo de confirmação
        if messagebox.askyesno(DICIONARIO_IDIOMAS["msg_excluir_titulo"][idioma_atual], DICIONARIO_IDIOMAS["msg_excluir_texto"][idioma_atual]):
            
            global estado_download, caminho_salvamento_atual
            estado_download = "parado"
            
            # Limpa interface
            restaurar_botoes()
            
            # Limpa a URL
            entrada_url.delete(0, tk.END)
            
            # Tenta deletar o arquivo parcial .part ou .ytdl (O Windows pode estar segurando, por isso usei o try)
            try:
                # Extrai apenas o nome base  para garantir que todos os arquivos '.part' sejam apagafos certinho
                base_nome = os.path.splitext(caminho_salvamento_atual)[0] 
                
                # Procura todos os arquivos que começam com o nome base
                arquivos_residuais = glob.glob(base_nome + ".*")
                
                for arq in arquivos_residuais:
                    if arq.endswith(".part") or arq.endswith(".ytdl"):
                        try:
                            os.remove(arq)
                        except:
                            pass
            except:
                pass

    # A função de thread para o download, exibindo a barra
    def thread_download():
        try:
            baixar_midia_youtube(
                url_atual, 
                tipo_atual, 
                formato_atual, 
                hook_progresso=atualizar_progresso,
                caminho_completo=caminho_salvamento_atual
            )
            
            # Se não foi pausado e terminou tudo, exibe sucesso
            if estado_download == "rodando":
                janela.after(0, finalizar_com_sucesso, tipo_atual, formato_atual)
                
        except DownloadPausado:
            # Não exibe erro, apenas interrompe a linha do tempo (a UI já foi alterada)
            pass
        except Exception as e:
            janela.after(0, finalizar_com_erro, str(e))

    # Função chamada quando qualquer um dos botões principais é clicado
    def iniciar_download(tipo):
        
        global url_atual, tipo_atual, formato_atual, caminho_salvamento_atual, estado_download
        url = entrada_url.get() # Captura o texto que o usuário digitou
        
        if not url.strip(): 
            messagebox.showwarning(DICIONARIO_IDIOMAS["msg_aviso_titulo"][idioma_atual], DICIONARIO_IDIOMAS["msg_aviso_url"][idioma_atual])
            return

        if tipo == 'audio':
            formato = var_audio.get()
            botao_ativo = botao_baixar_audio
            file_types = [(f"Arquivo {formato.upper()}", f"*.{formato}")]
        else:
            formato = var_video.get()
            botao_ativo = botao_baixar_video
            file_types = [(f"Arquivo {formato.upper()}", f"*.{formato}")]
        
        # Pede ao usuário o local para salvar, definindo o tipo do arquivo
        caminho_completo = filedialog.asksaveasfilename(
            title=DICIONARIO_IDIOMAS["msg_salvar_como"][idioma_atual],
            defaultextension=f".{formato}",
            filetypes=file_types,
            initialdir=os.path.join(os.path.expanduser('~'), 'Downloads')
        )
        
        # Se o usuário clicou em cancelar no popup, aborta tudo sem avisos
        if not caminho_completo:
            return
            
        # Grava os dados globalmente para retomar depois
        url_atual = url
        tipo_atual = tipo
        formato_atual = formato
        caminho_salvamento_atual = caminho_completo
        estado_download = "rodando"
            
        # Desativa os botões principais
        botao_baixar_audio.configure(state=tk.DISABLED)
        botao_baixar_video.configure(state=tk.DISABLED)
        botao_ativo.configure(text=DICIONARIO_IDIOMAS["btn_baixar_inativo"][idioma_atual])
        
        # Controla a interface para o download
        frame_controles.pack_forget() # Dá um refresh na ordem
        barra_progresso.pack(pady=(15, 0))
        label_progresso.pack(pady=(5, 0))
        frame_controles.pack(pady=(20, 0)) # Re-pack abaixo da barra
        
        entrada_url.configure(state="readonly") # Bloqueia a edição
        
        # Habilita botão de pausar e mantém os demais inativos
        botao_pausar.configure(state="normal", image=img_pausa)
        botao_continuar.configure(state="disabled", image=img_continuar_inativa)
        botao_excluir.configure(state="disabled", image=img_excluir_inativa)
        
        set_progresso_ui(0, DICIONARIO_IDIOMAS["progresso_init"][idioma_atual])
        janela.update() 
        
        # Cria a thread e dá o "play" nela
        threading.Thread(target=thread_download, daemon=True).start()

    # Criação da janela principal da interface
    janela = tk.Tk()
    janela.title("Crimson - Video Downloader") # Título da janela
    janela.geometry("600x300") # (Largura x Altura)
    janela.eval('tk::PlaceWindow . center') # Centraliza a janela na tela

    # Texto de instrução principal na tela (Label puxando do dicionário)
    label_instrucao = tk.Label(janela, text=DICIONARIO_IDIOMAS["instrucao_ready"][idioma_atual], font=("Arial", 12))
    label_instrucao.pack(pady=(20, 5)) # pady=(topo, baixo) aplica margens diferentes

    # Campo onde o usuário vai digitar a URL (Entry)
    entrada_url = tk.Entry(janela, width=50, font=("Arial", 12))
    entrada_url.pack(pady=5)

    # ------------------------------------------------------------------
    # Criação de um Frame (uma caixa invisível) para organizar os botões lado a lado
    frame_botoes = tk.Frame(janela)
    frame_botoes.pack(pady=10)

    # ------------------------------------------------------------------
    # --- Seção do Áudio ---

    # Variável que guarda a escolha atual do dropdown (padrão mp3)
    var_audio = ctk.StringVar(value="mp3") 
    opcoes_audio = ["mp3", "m4a", "wav", "flac"] # Lista de formatos de áudio
    
    # Cria o dropdown usando customtkinter (estilo frontend moderno, bordas arredondadas)
    dropdown_audio = ctk.CTkOptionMenu(frame_botoes, variable=var_audio, values=opcoes_audio, font=("Arial", 12, "bold"), corner_radius=8, width=90)
    dropdown_audio.grid(row=0, column=0, padx=5) # grid organiza os itens em forma de tabela (linha/coluna)

    # Botão de baixar áudio usando ctk (CustomTkinter) para cantos arredondados
    # o parâmetro corner_radius controla o grau de arredondamento
    botao_baixar_audio = ctk.CTkButton(frame_botoes, text=DICIONARIO_IDIOMAS["cor_botao_audio"][idioma_atual], font=("Arial", 12, "bold"), command=lambda: iniciar_download('audio'), corner_radius=8)
    botao_baixar_audio.grid(row=0, column=1, padx=5)

    # ------------------------------------------------------------------
    # --- Seção do Vídeo ---

    # Variável que guarda a escolha atual do dropdown (padrão mp4)
    var_video = ctk.StringVar(value="mp4")
    opcoes_video = ["mp4", "mkv", "webm"] # Lista de formatos de vídeo
    
    # Cria o dropdown de vídeo
    dropdown_video = ctk.CTkOptionMenu(frame_botoes, variable=var_video, values=opcoes_video, font=("Arial", 12, "bold"), corner_radius=8, width=90)
    dropdown_video.grid(row=0, column=2, padx=(30, 5)) # padx maior na esquerda para afastar a seção de vídeo da seção de áudio

    # Botão de baixar vídeo
    botao_baixar_video = ctk.CTkButton(frame_botoes, text=DICIONARIO_IDIOMAS["cor_botao_video"][idioma_atual], font=("Arial", 12, "bold"), command=lambda: iniciar_download('video'), corner_radius=8)
    botao_baixar_video.grid(row=0, column=3, padx=5)

    # ------------------------------------------------------------------
    # --- Componentes da Barra de Progresso (Download) ---
    
    # criando eles, mas não usando o '.pack()', por isso ficam escondidos inicialmente
    # Só vão aparecer quando o usuário clicar em baixar
    barra_progresso = ttk.Progressbar(janela, orient="horizontal", length=400, mode="determinate")
    label_progresso = tk.Label(janela, text="", font=("Arial", 10))
    frame_controles = tk.Frame(janela)

    # ------------------------------------------------------------------
    # --- Carregamento dos Ícones ---
    
    # tk.PhotoImage não suporta o formato '.ico' nativamente, apenas '.png' ou '.gif'
    caminho_icons = os.path.join(caminho_base, "Icons")
    
    # O 'try/except' é uma trava de segurança
    # se a imagem ou a pasta não existirem ainda, ele simplesmente desiste e ignora, não quebrando a tela
    try:
        
        # Tenta carregar e aplicar o ícone do aplicativo na janela (topo da janela e barra de tarefas)
        # usei o glob para achar a imagem que tem Crimson no nome evitando problemas com o acento por causa da minha própria renomeação :P
        arquivos_icone = glob.glob(os.path.join(caminho_icons, "*Crimson*.png"))
        
        if arquivos_icone:
            img_icone_app = tk.PhotoImage(file=arquivos_icone[0])
            
            # O True faz com que esse ícone seja herdado por todas as janelas secundárias (como a de config)
            janela.iconphoto(True, img_icone_app)
            
        # Carregando as imagens originais brutas
        raw_config    = tk.PhotoImage(file=os.path.join(caminho_icons, "configuracoes.png"))
        raw_git       = tk.PhotoImage(file=os.path.join(caminho_icons, "github.png"))
        raw_community = tk.PhotoImage(file=os.path.join(caminho_icons, "comunidade.png"))
        
        try:
            # Carrega e converte para permitir manipulação de canais
            raw_pausa     = Image.open(os.path.join(caminho_icons, "pausa.png")).convert("RGBA")
            raw_continuar = Image.open(os.path.join(caminho_icons, "continuar.png")).convert("RGBA")
            raw_excluir   = Image.open(os.path.join(caminho_icons, "excluir.png")).convert("RGBA")
            
            # Função para criar versão inativa (translúcida/opacidade reduzida)
            # toda imagem com fundo transparente possuí quatro camadas, red, green, blue e alpha (que é a parte transparente em si)
            # na função abaixo eu separo ela por camadas e justamente altero a alpha, juntando tudo no final de novo
            def criar_inativa(img):
                r, g, b, a = img.split()
                
                # Reduz a opacidade para 30%
                a = a.point(lambda p: p * 0.3)
                return Image.merge("RGBA", (r, g, b, a))
            
            # usando das propriedades de composição para deixar a imagem translucida no momento da execução e já entregando ela ao ctkimage
            img_pausa_inativa       = ctk.CTkImage(criar_inativa(raw_pausa), size=(28, 28))
            img_continuar_inativa   = ctk.CTkImage(criar_inativa(raw_continuar), size=(28, 28))
            img_excluir_inativa     = ctk.CTkImage(criar_inativa(raw_excluir), size=(28, 28))
            
            img_pausa       = ctk.CTkImage(raw_pausa, size=(28, 28))
            img_continuar   = ctk.CTkImage(raw_continuar, size=(28, 28))
            img_excluir     = ctk.CTkImage(raw_excluir, size=(28, 28))
        except:
            img_pausa = None
            img_continuar = None
            img_excluir = None
            img_pausa_inativa = None
            img_continuar_inativa = None
            img_excluir_inativa = None
        
        # O .subsample(x, y) é um truque nativo do tkinter para diminuir imagens
        # ele funciona de maneira inversa, quanto menor o valor, maior o tamanho
        # isso acontece pq o subsample joga pixels fora por assim dizer, então quanto maior o valor, mais pixels serão
        # descartados a cada linha
        img_config      = raw_config.subsample(15, 15)
        img_git         = raw_git.subsample(9, 9)
        img_community   = raw_community.subsample(10, 10)
    except:
        img_config      = None
        img_git         = None
        img_community   = None
        img_pausa       = None
        img_continuar   = None
        img_excluir     = None
        img_pausa_inativa = None
        img_continuar_inativa = None
        img_excluir_inativa = None
        
    # Criando os 3 botões fixos de controle usando CustomTkinter para uma estética mais agradável
    botao_pausar = ctk.CTkButton(frame_controles, text="", image=img_pausa_inativa, command=acionar_pausa, state="disabled", width=40, height=40, corner_radius=8)
    botao_pausar.grid(row=0, column=0, padx=15)
    
    botao_continuar = ctk.CTkButton(frame_controles, text="", image=img_continuar_inativa, command=acionar_retomar, state="disabled", width=40, height=40, corner_radius=8)
    botao_continuar.grid(row=0, column=1, padx=15)
    
    botao_excluir = ctk.CTkButton(frame_controles, text="", image=img_excluir_inativa, command=acionar_excluir, state="disabled", width=40, height=40, corner_radius=8)
    botao_excluir.grid(row=0, column=2, padx=15)

    # ------------------------------------------------------------------
    # --- Configurações e Sobre (menu) ---
    
    def abrir_configuracoes():
        
        # tk.Toplevel cria uma nova janela flutuante sobre a principal
        jan_config = tk.Toplevel(janela)
        jan_config.title("Configurações e Sobre")
        jan_config.geometry("400x450")
        
        # Forçando a abertura no meio da tela (o comando Tcl/Tk PlaceWindow centraliza na tela principal)
        # Atenção: O método 'eval' pertence à 'janela' mãe (Tk) e não ao 'jan_config' (Toplevel)
        janela.eval(f'tk::PlaceWindow {str(jan_config)} center')
        
        # Bloqueia a interação com a janela de fundo (torna a janela 'modal')
        # modal é quando uma janela rouba a atenção do usuário, é um termo comum no front
        jan_config.transient(janela)
        jan_config.grab_set() 
        
        # ttk.Notebook é o componente responsável por gerenciar abas
        notebook = ttk.Notebook(jan_config)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Função que roda ao trocar de idioma no menu
        def atualizar_e_renderizar(selecao):
            
            global idioma_atual
            idioma_atual = selecao
            
            # Atualiza os botões da tela principal (mãe) que estão no escopo acima
            botao_baixar_audio.configure(text=DICIONARIO_IDIOMAS["cor_botao_audio"][idioma_atual])
            botao_baixar_video.configure(text=DICIONARIO_IDIOMAS["cor_botao_video"][idioma_atual])
            botao_config.config()
            label_instrucao.config(text=DICIONARIO_IDIOMAS["instrucao_ready"][idioma_atual])
            
            # Atualiza os títulos e rótulos da tela de config atual
            jan_config.title(f"{DICIONARIO_IDIOMAS['aba_sistema'][idioma_atual]} / {DICIONARIO_IDIOMAS['aba_sobre'][idioma_atual]}")
            notebook.tab(0, text=DICIONARIO_IDIOMAS["aba_sistema"][idioma_atual])
            notebook.tab(1, text=DICIONARIO_IDIOMAS["aba_sobre"][idioma_atual])
            
            label_idioma.config(text=DICIONARIO_IDIOMAS["lbl_idioma"][idioma_atual])
            label_tema.config(text=DICIONARIO_IDIOMAS["lbl_tema"][idioma_atual])
            label_versao.config(text=DICIONARIO_IDIOMAS["lbl_versao"][idioma_atual])
            label_disclaimer.config(text=DICIONARIO_IDIOMAS["txt_disclaimer"][idioma_atual])
            label_creditos.config(text=DICIONARIO_IDIOMAS["lbl_creditos"][idioma_atual])
            link_crimson.config(text=DICIONARIO_IDIOMAS["link_crimson"][idioma_atual])
            link_ytdlp.config(text=DICIONARIO_IDIOMAS["link_ytdlp"][idioma_atual])
            link_ffmpeg.config(text=DICIONARIO_IDIOMAS["link_ffmpeg"][idioma_atual])
            marca_dagua.config(text=DICIONARIO_IDIOMAS["marca_dagua"][idioma_atual])

        cor = TEMAS[tema_atual] # Pegando a cor atual para pintar a janela
        
        # ------------------------------------------------------------------
        # --- Aba Sistema ---
        aba_sistema = tk.Frame(notebook, bg=cor["cor_fundo_janela"])
        
        # O text puxa a língua ativa ao abrir a tela
        notebook.add(aba_sistema, text=DICIONARIO_IDIOMAS["aba_sistema"][idioma_atual])
        
        # Componentes do idioma
        label_idioma = tk.Label(aba_sistema, text=DICIONARIO_IDIOMAS["lbl_idioma"][idioma_atual], font=("Arial", 11), bg=cor["cor_fundo_janela"], fg=cor["cor_do_texto"])
        label_idioma.pack(pady=(20, 5))
        
        var_idioma = ctk.StringVar(value=idioma_atual)
        opcoes_idioma = ["Portuguese", "English"]
        
        # O customtkinter simplifica o OptionMenu e dispensa o asterisco (*) deixando o código mais limpo
        dropdown_idioma = ctk.CTkOptionMenu(aba_sistema, variable=var_idioma, values=opcoes_idioma, corner_radius=8, width=150, font=("Arial", 12, "bold"))
        dropdown_idioma.pack(pady=5)
        
        # ------------------------------------------------------------------
        # --- Componentes do Tema ---
        label_tema = tk.Label(aba_sistema, text=DICIONARIO_IDIOMAS["lbl_tema"][idioma_atual], font=("Arial", 11), bg=cor["cor_fundo_janela"], fg=cor["cor_do_texto"])
        label_tema.pack(pady=(20, 5))
        
        var_tema = ctk.StringVar(value=tema_atual)
        opcoes_tema = ["Dark", "Egg", "Matcha"]
        
        dropdown_tema = ctk.CTkOptionMenu(aba_sistema, variable=var_tema, values=opcoes_tema, corner_radius=8, width=150, font=("Arial", 12, "bold"))
        dropdown_tema.pack(pady=5)
        
        # ------------------------------------------------------------------
        # Lógica do Botão de Salvar
        def confirmar_e_salvar():
            
            # no geral as variáveis globais devvem ser declaradas no topo das funções, ajuda a evitar erros de compilação
            # numa execução quebrada aonde ela é chamada antes de ser declarada, experiência pessoal :P
            global idioma_atual, tema_atual
            
            novo_idioma = var_idioma.get()
            novo_tema = var_tema.get()
            
            # Texto da caixa de diálogo dinâmico com base no idioma atual
            titulo_msg = "Confirmar" if idioma_atual == "Portuguese" else "Confirm"
            texto_msg = "Tem certeza que deseja salvar as configurações atuais?" if idioma_atual == "Portuguese" else "Are you sure you want to save the current settings?"
            
            # Exibe o popup e checa a resposta do usuário
            if messagebox.askyesno(titulo_msg, texto_msg):
                
                # Atualiza as variáveis globais
                idioma_atual = novo_idioma
                tema_atual = novo_tema
                
                # Grava no arquivo .json recém criado no AppData
                salvar_configuracoes(idioma_atual, tema_atual)
                
                # Só agora aplica as mudanças visualmente para a tela se adaptar à escolha
                atualizar_e_renderizar(idioma_atual)
                aplicar_tema()
                
                # Mostra que deu bom
                texto_sucesso = "Configurações salvas com sucesso" if idioma_atual == "Portuguese" else "Settings saved successfully"
                messagebox.showinfo(titulo_msg, texto_sucesso)
                
                # Para evitar erro de tela, atualizo também as cores de dentro da janelinha de config manualmente
                nova_cor = TEMAS[tema_atual]
                jan_config.config(bg=nova_cor["cor_fundo_janela"])
                aba_sistema.config(bg=nova_cor["cor_fundo_janela"])
                aba_sobre.config(bg=nova_cor["cor_fundo_janela"])
                frame_repos.config(bg=nova_cor["cor_fundo_janela"])
                
                label_idioma.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto"])
                label_tema.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto"])
                label_versao.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto"])
                label_disclaimer.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto"])
                label_creditos.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto"])
                link_crimson.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto"])
                link_ytdlp.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto"])
                link_ffmpeg.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto"])
                marca_dagua.config(bg=nova_cor["cor_fundo_janela"], fg=nova_cor["cor_do_texto_magua"])
                
                dropdown_idioma.configure(fg_color=nova_cor["cor_botao_audio"], button_color=nova_cor["cor_botao_audio"], button_hover_color=nova_cor["cor_botao_audio_hover"], text_color=nova_cor["cor_fonte_botoes"], dropdown_fg_color=nova_cor["cor_de_fundo_dropdown"], dropdown_hover_color=nova_cor["cor_do_hover_dropdown"], dropdown_text_color=nova_cor["cor_do_texto"])
                dropdown_tema.configure(fg_color=nova_cor["cor_botao_audio"], button_color=nova_cor["cor_botao_audio"], button_hover_color=nova_cor["cor_botao_audio_hover"], text_color=nova_cor["cor_fonte_botoes"], dropdown_fg_color=nova_cor["cor_de_fundo_dropdown"], dropdown_hover_color=nova_cor["cor_do_hover_dropdown"], dropdown_text_color=nova_cor["cor_do_texto"])
                
        texto_botao_salvar = "Salvar e Aplicar" if idioma_atual == "Portuguese" else "Save & Apply"
        botao_salvar = ctk.CTkButton(aba_sistema, text=texto_botao_salvar, font=("Arial", 12, "bold"), command=confirmar_e_salvar, corner_radius=8, width=150)
        botao_salvar.pack(pady=20)
        
        # Pinta os dropdowns assim que a tela abre
        dropdown_idioma.configure(fg_color=cor["cor_botao_audio"], button_color=cor["cor_botao_audio"], button_hover_color=cor["cor_botao_audio_hover"], text_color=cor["cor_fonte_botoes"], dropdown_fg_color=cor["cor_de_fundo_dropdown"], dropdown_hover_color=cor["cor_do_hover_dropdown"], dropdown_text_color=cor["cor_do_texto"])
        dropdown_tema.configure(fg_color=cor["cor_botao_audio"], button_color=cor["cor_botao_audio"], button_hover_color=cor["cor_botao_audio_hover"], text_color=cor["cor_fonte_botoes"], dropdown_fg_color=cor["cor_de_fundo_dropdown"], dropdown_hover_color=cor["cor_do_hover_dropdown"], dropdown_text_color=cor["cor_do_texto"])
        
        # ------------------------------------------------------------------
        # --- Aba Sobre ---
        aba_sobre = tk.Frame(notebook, bg=cor["cor_fundo_janela"])
        notebook.add(aba_sobre, text=DICIONARIO_IDIOMAS["aba_sobre"][idioma_atual])
        
        label_versao = tk.Label(aba_sobre, text=DICIONARIO_IDIOMAS["lbl_versao"][idioma_atual], font=("Arial", 11, "bold"), bg=cor["cor_fundo_janela"], fg=cor["cor_do_texto"])
        label_versao.pack(pady=(10, 5))
        
        label_disclaimer = tk.Label(aba_sobre, text=DICIONARIO_IDIOMAS["txt_disclaimer"][idioma_atual], font=("Arial", 9), justify="center", bg=cor["cor_fundo_janela"], fg=cor["cor_do_texto"])
        label_disclaimer.pack(pady=(5, 15))
        
        # O compound=tk.TOP coloca a imagem cima do texto
        label_creditos = tk.Label(aba_sobre, text=DICIONARIO_IDIOMAS["lbl_creditos"][idioma_atual], image=img_community, compound=tk.TOP, font=("Arial", 9, "italic"), bg=cor["cor_fundo_janela"], fg=cor["cor_do_texto"])
        label_creditos.pack(pady=5)
        
        # Função para processar os cliques e chamar o webbrowser
        def abrir_link(url):
            webbrowser.open(url)

        # Criando um Frame só para agrupar e alinhar os repositórios (isso cria um bloco invisível que prende os ícones retos)
        frame_repos = tk.Frame(aba_sobre, bg=cor["cor_fundo_janela"])
        frame_repos.pack(pady=10)

        # 'cursor="hand2"' mostra o cursor de clique em formato de mãozinha (igual a uma página da internet)
        # O anchor="w" (West/Esquerda) joga os itens pra esquerda e os alinha juntos dentro do frame
        link_crimson = tk.Label(frame_repos, text=DICIONARIO_IDIOMAS["link_crimson"][idioma_atual], image=img_git, compound=tk.LEFT, font=("Arial", 10), fg=cor["cor_do_texto"], bg=cor["cor_fundo_janela"], cursor="hand2", anchor="w")
        link_crimson.pack(pady=5, fill="x")
        link_crimson.bind("<Button-1>", lambda e: abrir_link("https://github.com/LuanDevCodes/Crimson"))
        
        link_ytdlp = tk.Label(frame_repos, text=DICIONARIO_IDIOMAS["link_ytdlp"][idioma_atual], image=img_git, compound=tk.LEFT, font=("Arial", 10), fg=cor["cor_do_texto"], bg=cor["cor_fundo_janela"], cursor="hand2", anchor="w")
        link_ytdlp.pack(pady=5, fill="x")
        link_ytdlp.bind("<Button-1>", lambda e: abrir_link("https://github.com/yt-dlp/yt-dlp"))
        
        link_ffmpeg = tk.Label(frame_repos, text=DICIONARIO_IDIOMAS["link_ffmpeg"][idioma_atual], image=img_git, compound=tk.LEFT, font=("Arial", 10), fg=cor["cor_do_texto"], bg=cor["cor_fundo_janela"], cursor="hand2", anchor="w")
        link_ffmpeg.pack(pady=5, fill="x")
        link_ffmpeg.bind("<Button-1>", lambda e: abrir_link("https://github.com/BtbN/FFmpeg-Builds"))

        # --- Marca d'água (Rodapé Central) ---
        marca_dagua = tk.Label(aba_sobre, text=DICIONARIO_IDIOMAS["marca_dagua"][idioma_atual], font=("Arial", 8, "italic"), fg=cor["cor_do_texto_magua"], bg=cor["cor_fundo_janela"])
        
        # Para centralizar, usei o relx=0.5 (50% da tela na horizontal) e rely=1.0 (100% da tela na vertical)
        # O anchor="s" (South / Sul) diz para o Tkinter alinhar usando o centro da base do texto
        # y=-10 deixa margem de respiro pro fundo da janela
        marca_dagua.place(relx=0.5, rely=1.0, anchor="s", y=-10)

    # Criando o Botão de Configurações
    botao_config = tk.Button(janela, image=img_config, compound=tk.LEFT, font=("Arial", 9, "bold"), bg="#f0f0f0", command=abrir_configuracoes)

    # ------------------------------------------------------------------
    # --- Sistema de Temas e Animações ---
    
    def aplicar_tema():
        cor = TEMAS[tema_atual]
        
        # Pinta a janela principal e as caixas (frames) transparentes
        janela.config(bg=cor["cor_fundo_janela"])
        frame_botoes.config(bg=cor["cor_fundo_janela"])
        frame_controles.config(bg=cor["cor_fundo_janela"])
        
        # Pinta os textos na tela e os botões de ação
        label_instrucao.config(bg=cor["cor_fundo_janela"], fg=cor["cor_do_texto"])
        label_progresso.config(bg=cor["cor_fundo_janela"], fg=cor["cor_do_texto"])
        
        # Estiliza o campo de digitar o link (readonlybackground garante que a cor não mude quando bloqueado)
        entrada_url.config(bg=cor["cor_barra_de_pesquisa"], fg=cor["cor_texto_caixa_de_pesquisa"], insertbackground=cor["cor_do_texto"], relief="flat", readonlybackground=cor["cor_barra_de_pesquisa"])
        
        # Configuração para os botões de controle do CustomTkinter (fg_color transparent resolve a cor feia do DISABLED), usei o mesmo hover dos botões de áudio
        botao_pausar.configure(bg_color=cor["cor_fundo_janela"], fg_color="transparent", hover_color=cor["cor_botao_audio_hover"])
        botao_continuar.configure(bg_color=cor["cor_fundo_janela"], fg_color="transparent", hover_color=cor["cor_botao_audio_hover"])
        botao_excluir.configure(bg_color=cor["cor_fundo_janela"], fg_color="transparent", hover_color=cor["cor_botao_audio_hover"])
        
        # Configuração para os botões e menus do CustomTkinter (agora tem hover nativo e bordas arredondadas sem complexidade)
        botao_baixar_audio.configure(fg_color=cor["cor_botao_audio"], hover_color=cor["cor_botao_audio_hover"], text_color=cor["cor_fonte_botoes"], text_color_disabled=cor["cor_fonte_botoes"], border_width=2, border_color=cor["cor_da_borda_botao_audio"])
        botao_baixar_video.configure(fg_color=cor["cor_botao_video"], hover_color=cor["cor_botao_video_hover"], text_color=cor["cor_fonte_botoes"], text_color_disabled=cor["cor_fonte_botoes"], border_width=2, border_color=cor["cor_da_borda_botao_video"])
        
        dropdown_audio.configure(fg_color=cor["cor_botao_audio"], button_color=cor["cor_botao_audio"], button_hover_color=cor["cor_botao_audio_hover"], text_color=cor["cor_fonte_botoes"], dropdown_fg_color=cor["cor_de_fundo_dropdown"], dropdown_hover_color=cor["cor_do_hover_dropdown"], dropdown_text_color=cor["cor_do_texto"])
        dropdown_video.configure(fg_color=cor["cor_botao_video"], button_color=cor["cor_botao_video"], button_hover_color=cor["cor_botao_video_hover"], text_color=cor["cor_fonte_botoes"], dropdown_fg_color=cor["cor_de_fundo_dropdown"], dropdown_hover_color=cor["cor_do_hover_dropdown"], dropdown_text_color=cor["cor_do_texto"])
        
        # Botões do Tkinter nativo continuam usando config normal
        botao_config.config(bg=cor["cor_fundo_janela"], relief="flat", borderwidth=0)

    # ------------------------------------------------------------------
    # --- Lógica da Tela de Carregamento (Update Inicial) ---
    
    # Esconde a interface principal para colocar a barrinha de carregamento (apenas no início)
    frame_botoes.pack_forget()
    entrada_url.pack_forget()
    label_instrucao.config(text=DICIONARIO_IDIOMAS["instrucao_init"][idioma_atual])
    
    # mode="indeterminate" cria aquela barrinha que fica indo e voltando sem fim
    barra_loading = ttk.Progressbar(janela, orient="horizontal", length=300, mode="indeterminate")
    barra_loading.pack(pady=20)
    barra_loading.start(10) # Velocidade da animação (em ms)

    # Função que restaura a interface ao estado normal de uso
    def finalizar_loading():
        barra_loading.stop()
        barra_loading.pack_forget()
        label_instrucao.config(text=DICIONARIO_IDIOMAS["instrucao_ready"][idioma_atual])
        entrada_url.pack(pady=5)
        frame_botoes.pack(pady=10)
        frame_controles.pack(pady=(20, 0)) # Fica fixo abaixo dos outros
        
        # O botão do menu de configurações é revelado no fim do loading
        botao_config.place(x=10, y=10) 

    # Função que roda em background para a barrinha poder animar sem travar
    def thread_atualizacao_inicial():
        try:
            print("[*] Verificando atualizações de segurança (Motor yt-dlp)")
            
            # URL para baixar o código-fonte (master branch) constante e mais atualizado direto do GitHub
            url_master = "https://github.com/yt-dlp/yt-dlp/archive/refs/heads/master.zip"
            caminho_zip = os.path.join(lib_dir, "yt-dlp-master.zip")
            
            # Baixa o zip (Usando apenas as bibliotecas nativas do python)
            urllib.request.urlretrieve(url_master, caminho_zip)
            
            # Extrai o zip dentro da nossa pasta 'Lib' no AppData
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(lib_dir)
                
            # Limpa o arquivo zip que foi baixado, já que o conteúdo foi extraído
            os.remove(caminho_zip)
            
            # Garante que a injeção modular esteja no sys.path para caso o app acabe de abrir pela primeira vez
            path_extraido = os.path.join(lib_dir, "yt-dlp-master")
            
            if path_extraido not in sys.path:
                sys.path.insert(0, path_extraido)
                
            print("[*] Motor atualizado e injetado - Interface pronta")
        except Exception as e:
            print(f"[*] Não foi possível atualizar o motor online: {e}")
            pass
        finally:
            janela.after(0, finalizar_loading)

    # Dá o play nessa rotina secundária
    threading.Thread(target=thread_atualizacao_inicial, daemon=True).start()

    # ------------------------------------------------------------------

    # Aplica o tema pela primeira vez antes de exibir a tela
    aplicar_tema()

    # Mantém a janela aberta rodando em loop
    janela.mainloop()