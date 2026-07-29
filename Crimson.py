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

# -------------------------------
# *******************************
# -------------------------------

caminho_base = os.path.dirname(os.path.abspath(__file__))
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
        ydl_opts['format'] = 'bestvideo+bestaudio/best' # Pega melhor vídeo + melhor áudio
        
        # Usa o ffmpeg para juntar o áudio e o vídeo no formato escolhido (ex: mp4)
        ydl_opts['merge_output_format'] = formato 

    print(f"[*] Preparando para baixar ({tipo} - {formato}): {url}")
    
    # Execução do download
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
                
                # pegando a velocidade e o ETA, e limpamos caso venham com cores residuais
                eta = re.sub(r'\x1b\[[0-9;]*[mK]', '', d.get('_eta_str', 'N/A')).strip()
                velocidade = re.sub(r'\x1b\[[0-9;]*[mK]', '', d.get('_speed_str', 'N/A')).strip()
                
                # Adiciona um espaço entre o número e a unidade de medida da velocidade (ex: 59.26MiB/s -> 59.26 MiB/s)
                # estava me dando toque
                velocidade = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', velocidade)
                
                # Formatação bem mais bonita e com um espaçamento visual agradável
                texto = f"Baixando: {percentual_float:.1f}%   |   Velocidade: {velocidade}   |   Tempo Restante: {eta}"
                
                # Atualiza a UI com segurança, o "after(0, ...)" diz pro Tkinter rodar isso assim que puder na thread principal
                janela.after(0, set_progresso_ui, percentual_float, texto)
            except:
                pass
        elif d['status'] == 'finished':
            janela.after(0, set_progresso_ui, 100, "Baixado - Aguarde a conversão (FFmpeg)...")

    # Atualiza os componentes visuais de fato
    def set_progresso_ui(valor, texto):
        barra_progresso['value'] = valor
        label_progresso.config(text=texto)

    # Função chamada quando a conversão e o download terminam
    def finalizar_com_sucesso(tipo, formato):
        messagebox.showinfo("Sucesso", f"Download do {tipo} ({formato}) concluído com sucesso")
        entrada_url.delete(0, tk.END)
        restaurar_botoes()
        
    def finalizar_com_erro(mensagem_erro):
        messagebox.showerror("Erro", f"Ocorreu um erro durante o download:\n{mensagem_erro}")
        restaurar_botoes()
        
    def restaurar_botoes():
        botao_baixar_audio.config(state=tk.NORMAL, text="Baixar Áudio")
        botao_baixar_video.config(state=tk.NORMAL, text="Baixar Vídeo")
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
            botao_ativo.config(text="Preparando...")
            
            # Exibe a barra de progresso na tela (elas estavam escondidas)
            barra_progresso.pack(pady=(15, 0))
            label_progresso.pack(pady=(5, 0))
            set_progresso_ui(0, "Iniciando Download")
            janela.update() 
            
            # O Threading cria uma "linha do tempo paralela" (segundo plano)
            # é obrigatório, pois se eu chamar a função de baixar direto aqui, 
            # ela vai travar o "mainloop" da janela gráfica, paralisando tudo
            def thread_download():
                try:
                    baixar_midia_youtube(url, tipo, formato, hook_progresso=atualizar_progresso)
                    
                    # Quando a função acima terminar, aviso a tela principal
                    janela.after(0, finalizar_com_sucesso, tipo, formato)
                except Exception as e:
                    janela.after(0, finalizar_com_erro, str(e))
            
            # Cria a thread e dá o "play" nela
            threading.Thread(target=thread_download, daemon=True).start()
            
        else:
            messagebox.showwarning("Aviso", "Por favor, insira uma URL válida")

    # Criação da janela principal da interface
    janela = tk.Tk()
    janela.title("Crimson - Download Youtube") # Título da janela
    janela.geometry("600x300") # (Largura x Altura)
    janela.eval('tk::PlaceWindow . center') # Centraliza a janela na tela

    # Texto de instrução principal na tela (Label)
    label_instrucao = tk.Label(janela, text="Insira a URL do vídeo do YouTube:", font=("Arial", 12))
    label_instrucao.pack(pady=(20, 5)) # pady=(topo, baixo) aplica margens diferentes

    # Campo onde o usuário vai digitar a URL (Entry)
    entrada_url = tk.Entry(janela, width=50, font=("Arial", 12))
    entrada_url.pack(pady=5)

    # Criação de um Frame (uma caixa invisível) para organizar os botões lado a lado
    frame_botoes = tk.Frame(janela)
    frame_botoes.pack(pady=20)

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
    botao_baixar_audio = tk.Button(frame_botoes, text="Baixar Áudio", font=("Arial", 11, "bold"), bg="#020f59", fg="white", command=lambda: iniciar_download('audio'))
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
    botao_baixar_video = tk.Button(frame_botoes, text="Baixar Vídeo", font=("Arial", 11, "bold"), bg="#2e4347", fg="white", command=lambda: iniciar_download('video'))
    botao_baixar_video.grid(row=0, column=3, padx=5)

    # ------------------------------------------------------------------
    # --- Componentes da Barra de Progresso (Download) ---
    
    # criando eles, mas não usando o '.pack()', por isso ficam escondidos inicialmente
    # Só vão aparecer quando o usuário clicar em baixar
    barra_progresso = ttk.Progressbar(janela, orient="horizontal", length=400, mode="determinate")
    label_progresso = tk.Label(janela, text="", font=("Arial", 10))

    # ------------------------------------------------------------------
    # --- Lógica da Tela de Carregamento (Update Inicial) ---
    
    # Esconde os elementos principais temporariamente para mostrar a animação de carregamento
    frame_botoes.pack_forget()
    entrada_url.pack_forget()
    label_instrucao.config(text="Procurando atualizações de segurança...")
    
    # mode="indeterminate" cria aquela barrinha que fica indo e voltando sem fim (estilo loading bootstrap)
    barra_loading = ttk.Progressbar(janela, orient="horizontal", length=300, mode="indeterminate")
    barra_loading.pack(pady=20)
    barra_loading.start(10) # Velocidade da animação (em ms)

    # Função que restaura a interface ao estado normal de uso
    def finalizar_loading():
        barra_loading.stop()
        barra_loading.pack_forget()
        label_instrucao.config(text="Insira a URL do vídeo do YouTube:")
        entrada_url.pack(pady=5)
        frame_botoes.pack(pady=20)

    # Função que roda em background para a barrinha poder animar sem travar
    def thread_atualizacao_inicial():
        try:
            print("[*] Verificando atualizações de segurança")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "--quiet"])
            print("[*] Tudo atualizado - Interface pronta!")
        except Exception:
            pass
        finally:
            janela.after(0, finalizar_loading)

    # Dá o play nessa rotina secundária
    threading.Thread(target=thread_atualizacao_inicial, daemon=True).start()

    # ------------------------------------------------------------------

    # Mantém a janela aberta rodando em loop
    janela.mainloop()