# Projeto Crimson - Uma interface capaz de baixar vídeos do youtube de forma simples
# Criei esse projeto pela necessidade d euma ferramente útil e confiável para tal, nascendo assim ele :D

import yt_dlp # Biblioteca necessária para baixar os vídeos do youtube de forma crua por assim dizer
import os # Biblioteca para interagir com o sistema operacional (ex: navegar entre pastas, verificar se um arquivo existe, criar pastas e ler variáveis)
import sys # Necessário para identificar se está rodando como .exe
import tkinter as tk # Biblioteca para a interface gráfica (nativa do python)
from tkinter import ttk # Necessário para elementos mais modernos como a Barra de Progresso
from tkinter import messagebox # Para exibir mensagens de alerta/sucesso na tela
import threading # Biblioteca para criar rotinas em segundo plano (evita que a tela trave)
import re # Usado para limpar textos gerados pelo yt-dlp
import subprocess # Usado para executar comandos do sistema (como atualizar o yt-dlp)
import webbrowser # Usado para abrir links na internet (como no caso dos links dos repositório usados)

# -------------------------------
# *******************************
# -------------------------------

# dicionário global de idiomas, uma tupla com os textos traduzidos em diferentes idiomas

idioma_atual = "Portuguese"

DICIONARIO_IDIOMAS = {
    "instrucao_init": {
        "Portuguese": "Procurando atualizações de segurança...",
        "English": "Checking for security updates..."
    },
    "instrucao_ready": {
        "Portuguese": "Insira a URL do vídeo do YouTube:",
        "English": "Enter the YouTube video URL:"
    },
    "btn_audio": {
        "Portuguese": "Baixar Áudio",
        "English": "Download Audio"
    },
    "btn_video": {
        "Portuguese": "Baixar Vídeo",
        "English": "Download Video"
    },
    "aba_sistema": {
        "Portuguese": "Sistema",
        "English": "System"
    },
    "aba_sobre": {
        "Portuguese": "Sobre",
        "English": "About"
    },
    "lbl_idioma": {
        "Portuguese": "Idioma do Aplicativo:",
        "English": "Application Language:"
    },
    "lbl_versao": {
        "Portuguese": "Versão atual: V.1.0.0",
        "English": "Current version: V.1.0.0"
    },
    "txt_disclaimer": {
        "Portuguese": "Desenvolvido sem fins comerciais\nQualquer distribuição deve ser gratuita\ne livre para todos\n",
        "English": "Developed for non-commercial purposes\nAny distribution must be free\nand available to everyone\n"
    },
    "lbl_creditos": {
        "Portuguese": "Créditos e agradecimentos à comunidade Open Source\n",
        "English": "Credits and thanks to the Open Source community\n"
    },
    "link_crimson": {
        "Portuguese": " Repositório Crimson",
        "English": " Crimson Repository"
    },
    "link_ytdlp": {
        "Portuguese": " Repositório yt-dlp",
        "English": " yt-dlp Repository"
    },
    "link_ffmpeg": {
        "Portuguese": " Repositório FFmpeg",
        "English": " FFmpeg Repository"
    },
    "marca_dagua": {
        "Portuguese": "Desenvolvido por LuanDevCodes",
        "English": "Developed by LuanDevCodes"
    },
    "msg_sucesso_titulo": {
        "Portuguese": "Sucesso",
        "English": "Success"
    },
    "msg_sucesso_texto": {
        "Portuguese": "Download e conversão concluídos com sucesso",
        "English": "Download and conversion completed successfully"
    },
    "msg_erro_titulo": {
        "Portuguese": "Erro",
        "English": "Error"
    },
    "msg_erro_generico": {
        "Portuguese": "Ocorreu um erro durante o download:\n",
        "English": "An error occurred during the download:\n"
    },
    "msg_aviso_titulo": {
        "Portuguese": "Aviso",
        "English": "Warning"
    },
    "msg_aviso_url": {
        "Portuguese": "Por favor, insira uma URL válida do YouTube",
        "English": "Please enter a valid YouTube URL"
    },
    "progresso_baixando": {
        "Portuguese": "Baixando",
        "English": "Downloading"
    },
    "progresso_vel": {
        "Portuguese": "Velocidade",
        "English": "Speed"
    },
    "progresso_tempo": {
        "Portuguese": "Tempo Restante",
        "English": "ETA"
    },
    "progresso_init": {
        "Portuguese": "Iniciando Download...",
        "English": "Starting Download..."
    },
    "progresso_convertendo": {
        "Portuguese": "Baixado - Aguarde a conversão (FFmpeg)...",
        "English": "Downloaded - Please wait for conversion (FFmpeg)..."
    },
    "btn_baixar_inativo": {
        "Portuguese": "Preparando...",
        "English": "Preparing..."
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
def baixar_midia_youtube(url, tipo, formato, hook_progresso, pasta_destino='Downloads'):
    
    # validação da pasta e caso não exista, ela é criada
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Configurações base de Download (ydl_opts)
    ydl_opts = {
        
        # Define o caminho de saída: pasta_destino / titulo_do_video.extensao
        'outtmpl': os.path.join(pasta_destino, '%(title)s.%(ext)s'),
        
        # Conecta a função da nossa barra de progresso no sistema do yt-dlp
        'progress_hooks': [hook_progresso],
        
        # Indica para o yt-dlp onde encontrar o executável do ffmpeg
        'ffmpeg_location': caminho_ffmpeg_dir,
        
        # Mostra o progresso no console
        'quiet': False,
        'no_warnings': True,
        
        # Desativa códigos de cores (ANSI) para que o texto da barra de progresso fique limpo
        'color': 'no_color',
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
        
    print(f"[*] Download concluído - Verifique a pasta '{pasta_destino}'")

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
        botao_baixar_audio.config(state=tk.NORMAL, text=DICIONARIO_IDIOMAS["btn_audio"][idioma_atual])
        botao_baixar_video.config(state=tk.NORMAL, text=DICIONARIO_IDIOMAS["btn_video"][idioma_atual])
        barra_progresso.pack_forget() # Esconde a barra da tela
        label_progresso.pack_forget() # Esconde o texto da tela

    # --------------------------------------------------------------------------------------

    # Função chamada quando qualquer um dos botões é clicado
    def iniciar_download(tipo):
        url = entrada_url.get() # Captura o texto que o usuário digitou
        
        if tipo == 'audio':
            formato = var_audio.get()
            botao_ativo = botao_baixar_audio
        else:
            formato = var_video.get()
            botao_ativo = botao_baixar_video
        
        if url.strip(): 
            
            # Desativa os botões para evitar duplo clique durante o download
            botao_baixar_audio.config(state=tk.DISABLED)
            botao_baixar_video.config(state=tk.DISABLED)
            
            # Muda o texto do botão clicado para dar feedback ao usuário
            botao_ativo.config(text=DICIONARIO_IDIOMAS["btn_baixar_inativo"][idioma_atual])
            
            # Exibe a barra de progresso na tela (elas estavam escondidas)
            barra_progresso.pack(pady=(15, 0))
            label_progresso.pack(pady=(5, 0))
            set_progresso_ui(0, DICIONARIO_IDIOMAS["progresso_init"][idioma_atual])
            janela.update() 
            
            # O Threading cria uma "linha do tempo paralela" (segundo plano)
            # é obrigatório, pois se eu chamar a função de baixar direto aqui, 
            # ela vai travar o "mainloop" da janela gráfica, paralisando tudo
            def thread_download():
                try:
                    baixar_midia_youtube(
                        url, 
                        tipo, 
                        formato, 
                        hook_progresso=atualizar_progresso
                    )
                    
                    # Quando a função acima terminar, aviso a tela principal
                    janela.after(0, finalizar_com_sucesso, tipo, formato)
                except Exception as e:
                    janela.after(0, finalizar_com_erro, str(e))
            
            # Cria a thread e dá o "play" nela
            threading.Thread(target=thread_download, daemon=True).start()
            
        else:
            messagebox.showwarning(DICIONARIO_IDIOMAS["msg_aviso_titulo"][idioma_atual], DICIONARIO_IDIOMAS["msg_aviso_url"][idioma_atual])

    # Criação da janela principal da interface
    janela = tk.Tk()
    janela.title("Crimson - Download Youtube") # Título da janela
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
    var_audio = tk.StringVar(value="mp3") 
    opcoes_audio = ["mp3", "m4a", "wav", "flac"] # Lista de formatos de áudio
    
    # Cria o dropdown (OptionMenu) de áudio
    dropdown_audio = tk.OptionMenu(frame_botoes, var_audio, *opcoes_audio)
    dropdown_audio.grid(row=0, column=0, padx=5) # grid organiza os itens em forma de tabela (linha/coluna)

    # Botão de baixar áudio usando lambda para passar o argumento 'audio' para a função
    # se eu usar ela sem a lambda, a função vai rodar sozinha quando a tela abrir, o lambda cria uma mini função anônima que segura a execução até o clique do botão
    botao_baixar_audio = tk.Button(frame_botoes, text=DICIONARIO_IDIOMAS["btn_audio"][idioma_atual], font=("Arial", 11, "bold"), bg="#020f59", fg="white", command=lambda: iniciar_download('audio'))
    botao_baixar_audio.grid(row=0, column=1, padx=5)

    # ------------------------------------------------------------------
    # --- Seção do Vídeo ---

    # Variável que guarda a escolha atual do dropdown (padrão mp4)
    var_video = tk.StringVar(value="mp4")
    opcoes_video = ["mp4", "mkv", "webm"] # Lista de formatos de vídeo
    
    # Cria o dropdown de vídeo
    dropdown_video = tk.OptionMenu(frame_botoes, var_video, *opcoes_video)
    dropdown_video.grid(row=0, column=2, padx=(30, 5)) # padx maior na esquerda para afastar a seção de vídeo da seção de áudio

    # Botão de baixar vídeo
    botao_baixar_video = tk.Button(frame_botoes, text=DICIONARIO_IDIOMAS["btn_video"][idioma_atual], font=("Arial", 11, "bold"), bg="#2e4347", fg="white", command=lambda: iniciar_download('video'))
    botao_baixar_video.grid(row=0, column=3, padx=5)

    # ------------------------------------------------------------------
    # --- Componentes da Barra de Progresso (Download) ---
    
    # criando eles, mas não usando o '.pack()', por isso ficam escondidos inicialmente
    # Só vão aparecer quando o usuário clicar em baixar
    barra_progresso = ttk.Progressbar(janela, orient="horizontal", length=400, mode="determinate")
    label_progresso = tk.Label(janela, text="", font=("Arial", 10))

    # ------------------------------------------------------------------
    # --- Carregamento dos Ícones ---
    
    # tk.PhotoImage não suporta o formato '.ico' nativamente, apenas '.png' ou '.gif'
    caminho_icons = os.path.join(caminho_base, "Icons")
    
    # O 'try/except' é uma trava de segurança
    # se a imagem ou a pasta não existirem ainda, ele simplesmente desiste e ignora, não quebrando a tela
    try:
        # Carregando as imagens originais brutas
        raw_config    = tk.PhotoImage(file=os.path.join(caminho_icons, "configuracoes.png"))
        raw_git       = tk.PhotoImage(file=os.path.join(caminho_icons, "github.png"))
        raw_community = tk.PhotoImage(file=os.path.join(caminho_icons, "comunidade.png"))
        
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
            botao_baixar_audio.config(text=DICIONARIO_IDIOMAS["btn_audio"][idioma_atual])
            botao_baixar_video.config(text=DICIONARIO_IDIOMAS["btn_video"][idioma_atual])
            botao_config.config()
            label_instrucao.config(text=DICIONARIO_IDIOMAS["instrucao_ready"][idioma_atual])
            
            # Atualiza os títulos e rótulos da tela de config atual
            jan_config.title(f"{DICIONARIO_IDIOMAS['aba_sistema'][idioma_atual]} / {DICIONARIO_IDIOMAS['aba_sobre'][idioma_atual]}")
            notebook.tab(0, text=DICIONARIO_IDIOMAS["aba_sistema"][idioma_atual])
            notebook.tab(1, text=DICIONARIO_IDIOMAS["aba_sobre"][idioma_atual])
            
            label_idioma.config(text=DICIONARIO_IDIOMAS["lbl_idioma"][idioma_atual])
            label_versao.config(text=DICIONARIO_IDIOMAS["lbl_versao"][idioma_atual])
            label_disclaimer.config(text=DICIONARIO_IDIOMAS["txt_disclaimer"][idioma_atual])
            label_creditos.config(text=DICIONARIO_IDIOMAS["lbl_creditos"][idioma_atual])
            link_crimson.config(text=DICIONARIO_IDIOMAS["link_crimson"][idioma_atual])
            link_ytdlp.config(text=DICIONARIO_IDIOMAS["link_ytdlp"][idioma_atual])
            link_ffmpeg.config(text=DICIONARIO_IDIOMAS["link_ffmpeg"][idioma_atual])
            marca_dagua.config(text=DICIONARIO_IDIOMAS["marca_dagua"][idioma_atual])

        # ------------------------------------------------------------------
        # --- Aba Sistema ---
        aba_sistema = tk.Frame(notebook)
        
        # O text puxa a língua ativa ao abrir a tela
        notebook.add(aba_sistema, text=DICIONARIO_IDIOMAS["aba_sistema"][idioma_atual])
        
        # Componentes do idioma
        label_idioma = tk.Label(aba_sistema, text=DICIONARIO_IDIOMAS["lbl_idioma"][idioma_atual], font=("Arial", 11))
        label_idioma.pack(pady=(20, 5))
        
        var_idioma = tk.StringVar(value=idioma_atual)
        opcoes_idioma = ["Portuguese", "English"]
        
        # O parâmetro 'command=atualizar_e_renderizar' atrela a função ao clique do menu
        # o asterisco é necessário pois com ele é possível realizar o desempacotamento, como estou passando ela
        # como uma lista inteira, preciso dele para deixar tudo devidamente separado (pelas virgulas), não permitindo que ele confunda com apenas um botão
        dropdown_idioma = tk.OptionMenu(aba_sistema, var_idioma, *opcoes_idioma, command=atualizar_e_renderizar)
        dropdown_idioma.pack(pady=5)
        
        # ------------------------------------------------------------------
        # --- Aba Sobre ---
        aba_sobre = tk.Frame(notebook)
        notebook.add(aba_sobre, text=DICIONARIO_IDIOMAS["aba_sobre"][idioma_atual])
        
        label_versao = tk.Label(aba_sobre, text=DICIONARIO_IDIOMAS["lbl_versao"][idioma_atual], font=("Arial", 11, "bold"))
        label_versao.pack(pady=(10, 5))
        
        label_disclaimer = tk.Label(aba_sobre, text=DICIONARIO_IDIOMAS["txt_disclaimer"][idioma_atual], font=("Arial", 9), justify="center")
        label_disclaimer.pack(pady=(5, 15))
        
        # O compound=tk.TOP coloca a imagem perfeitamente ACIMA do texto!
        label_creditos = tk.Label(aba_sobre, text=DICIONARIO_IDIOMAS["lbl_creditos"][idioma_atual], image=img_community, compound=tk.TOP, font=("Arial", 9, "italic"))
        label_creditos.pack(pady=5)
        
        # Função para processar os cliques e chamar o webbrowser
        def abrir_link(url):
            webbrowser.open(url)

        # Criando um Frame só para agrupar e alinhar os repositórios (isso cria um bloco invisível que prende os ícones retos)
        frame_repos = tk.Frame(aba_sobre)
        frame_repos.pack(pady=10)

        # 'cursor="hand2"' mostra o cursor de clique em formato de mãozinha (igual a uma página da internet)
        # O anchor="w" (West/Esquerda) joga os itens pra esquerda e os alinha juntos dentro do frame
        link_crimson = tk.Label(frame_repos, text=DICIONARIO_IDIOMAS["link_crimson"][idioma_atual], image=img_git, compound=tk.LEFT, font=("Arial", 10), fg="black", cursor="hand2", anchor="w")
        link_crimson.pack(pady=5, fill="x")
        link_crimson.bind("<Button-1>", lambda e: abrir_link("https://github.com/LuanDevCodes/Crimson"))
        
        link_ytdlp = tk.Label(frame_repos, text=DICIONARIO_IDIOMAS["link_ytdlp"][idioma_atual], image=img_git, compound=tk.LEFT, font=("Arial", 10), fg="black", cursor="hand2", anchor="w")
        link_ytdlp.pack(pady=5, fill="x")
        link_ytdlp.bind("<Button-1>", lambda e: abrir_link("https://github.com/yt-dlp/yt-dlp"))
        
        link_ffmpeg = tk.Label(frame_repos, text=DICIONARIO_IDIOMAS["link_ffmpeg"][idioma_atual], image=img_git, compound=tk.LEFT, font=("Arial", 10), fg="black", cursor="hand2", anchor="w")
        link_ffmpeg.pack(pady=5, fill="x")
        link_ffmpeg.bind("<Button-1>", lambda e: abrir_link("https://github.com/BtbN/FFmpeg-Builds"))

        # --- Marca d'água (Rodapé Central) ---
        marca_dagua = tk.Label(aba_sobre, text=DICIONARIO_IDIOMAS["marca_dagua"][idioma_atual], font=("Arial", 8, "italic"), fg="gray")
        
        # Para centralizar, usei o relx=0.5 (50% da tela na horizontal) e rely=1.0 (100% da tela na vertical)
        # O anchor="s" (South / Sul) diz para o Tkinter alinhar usando o centro da base do texto
        # y=-10 deixa margem de respiro pro fundo da janela
        marca_dagua.place(relx=0.5, rely=1.0, anchor="s", y=-10)

    # Criando o Botão de Configurações
    botao_config = tk.Button(janela, image=img_config, compound=tk.LEFT, font=("Arial", 9, "bold"), bg="#f0f0f0", command=abrir_configuracoes)

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
        
        # O botão do menu de configurações é revelado no fim do loading
        botao_config.place(x=10, y=10) 

    # Função que roda em background para a barrinha poder animar sem travar
    def thread_atualizacao_inicial():
        try:
            print("[*] Verificando atualizações de segurança")
            subprocess.run([sys.executable, "-m", "pip", "install", "-U", "--pre", "yt-dlp", "--quiet"])
            print("[*] Tudo atualizado - Interface pronta")
        except Exception:
            pass
        finally:
            janela.after(0, finalizar_loading)

    # Dá o play nessa rotina secundária
    threading.Thread(target=thread_atualizacao_inicial, daemon=True).start()

    # ------------------------------------------------------------------

    # Mantém a janela aberta rodando em loop
    janela.mainloop()