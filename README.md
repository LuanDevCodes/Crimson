<h1 align="center">
  <img src="Icons/Crimson.png" width="40" valign="middle"> 
  Projeto Crimson - Interface de Download Multi-Plataforma
</h1>

## = Descrição do Projeto
O Crimson é uma aplicação desenvolvida em Python com uma interface gráfica moderna (PySide6 / Qt6) criada para facilitar e automatizar o download de vídeos e áudios de diversas plataformas na internet. O projeto encapsula o poder da biblioteca `yt-dlp` e a capacidade de processamento de mídia do `FFmpeg` por trás de uma tela amigável, elegante e com anti-aliasing nativo no Windows e Linux. A aplicação também lida de forma autônoma com atualizações de segurança internas, esquivando-se ativamente do erro "403: Forbidden" imposto por constantes mudanças nos algoritmos dos sites suportados. A ideia do projeto nasceu de uma necessidade pessoal minha e da ideia de facilitar esse tipo de situação.

## Δ Bibliotecas e Ferramentas
- **Python 3.x**
- **yt-dlp**: Motor principal responsável por buscar e realizar a extração bruta das mídias.
- **PySide6 (Qt6)**: Interface gráfica com anti-aliasing nativo vetorial, visual uniforme em todas as distribuições Linux e no Windows, estilo Fusion e cards modulares responsivos.
- **Threading**: Módulo responsável por criar rotinas em segundo plano, evitando o congelamento da interface gráfica durante o processo de download.
- **json & os & platform**: Orquestradas em conjunto para lidar com a pasta oficial de configurações do usuário (adaptada por sistema operacional) e salvar o estado da aplicação via memória persistente.
- **urllib.request & zipfile**: Usados para orquestrar o motor modular com streaming em blocos e timeout de segurança, agindo como ponte de download direto com a source master do `yt-dlp`.
- **subprocess & re**: Utilizados para operar ferramentas (como limpar processos fantasmas) e tratar os dados de progresso e velocidade com expressões regulares pré-compiladas.
- **webbrowser**: Módulo nativo do Python usado para transformar os links dos repositórios no Painel de Créditos em botões clicáveis de redirecionamento.
- **Pillow (PIL)**: Manipulação avançada de canais RGBA com cache inteligente em memória RAM para desempenho instantâneo.

## § Funcionalidades
- **Download Flexível e Descomplicado**: Escolha entre baixar apenas áudio ou vídeo (com as qualidades mescladas perfeitamente) através de dropdowns visuais (`mp3`, `mp4`, `mkv`, `webm`, etc).
- **Processamento Assíncrono (Zero-Freeze)**: As operações de download pesado e gravação de arquivos não disputam espaço com a renderização visual. Tudo ocorre em *threads* separadas, com a barra de progresso, velocidade e ETA atualizando de forma lisa e constante na thread principal.
- **Download reformulado**: Implementação de uma divisão inteligente de rede. O sistema corta a requisição da mídia em blocos (`http_chunk_size`) e abre 5 conexões de download simultâneas, contornando o estrangulamento de velocidade imposto por alguns sites e voando nas taxas de transferência.
- **Blindagem do Auto-Update Silencioso**: No exato momento em que o aplicativo é inicializado, uma tela de loading bloqueia o uso enquanto a thread secundária verifica e aplica silenciosamente a última versão do `yt-dlp` com timeout de proteção para conexões lentas ou offline.
- **Conversão por Fator Externo (FFmpeg)**: O motor de extração puxa nativamente os vídeos na melhor qualidade, mas geralmente separadamente da faixa de áudio de alta resolução. O Crimson aciona o FFmpeg de maneira integrada para mesclar essas duas camadas ou convertê-las para formatos específicos.
- **Internacionalização Completa em Tempo Real (15 Idiomas Nativos)**: Suporte integral a Português, Inglês, Espanhol, Chinês, Japonês, Sul Coreano, Russo, Ucraniano, Indonésio, Filipino, Vietnamita, Norueguês, Hauçá, Bambara e Latim. A troca é instantânea pelo Painel de Configurações, sem necessidade de reiniciar.
- **Identidade Visual e 5 Temas Dinâmicos**: O aplicativo suporta variações completas de tema com paletas harmoniosas: `Dark` (escuro moderno), `Egg` (creme aconchegante), `Matcha` (verde suave), `Savage` (vermelho vivo e carmesim puro) e `Platinum Disc` (cinza titânio metálico).
- **Eficiência Extrema para Computadores Modestos**:
  - *Cache em RAM de Ícones*: O disco só é lido uma única vez; acessos subsequentes ocorrem em microssegundos direto da memória.
  - *Throttling de Progresso (~16 FPS / 60ms)*: Reduz em ~85% a sobrecarga de repaints na thread de interface durante conexões velozes.
  - *Coleta Ativa de Memória*: Chamadas explícitas de liberação de memória (`gc.collect`) ao pausar, cancelar, finalizar downloads e na limpeza de processos.
- **Persistência de Dados e Roteamento Seguro**: O aplicativo memoriza as preferências do usuário salvando um `.json` seguro na pasta de configurações do sistema. No Windows usa `%LOCALAPPDATA%`, no Linux segue o padrão XDG (`~/.local/share/Crimson`).
- **Janela Centralizada no Monitor Principal**: A posição de abertura da janela é calculada matematicamente com base nas dimensões reais da tela, garantindo centralização mesmo em setups multi-monitor.
- **Gestão de Processos**: Um botão nativo no painel de configurações capaz de "varrer" e finalizar processos órfãos em segundo plano (como threads residuais do FFmpeg), adaptado por sistema operacional (`taskkill` no Windows, `pkill` no Linux).
- **Controle de Instâncias (Anti-Spam)**: As janelas do sistema (como as Plataformas e Configurações) possuem um bloqueio inteligente e modal que impede a abertura simultânea de dezenas de abas ao clicar repetidas vezes.
- **Menu de Contexto Intuitivo**: Interaja com a barra de pesquisa usando o botão direito do mouse para *Colar* links ou *Apagar* seleções de texto de forma rápida.

## ಄ Idiomas Suportados

| Idioma | Código | Status |
|---|---|---|
| Português (Brasil) | `Portuguese` | ✅ Completo |
| English | `English` | ✅ Completo |
| Español | `Spanish` | ✅ Completo |
| 中文 (Mandarim Simplificado) | `Chinese` | ✅ Completo |
| 日本語 (Japonês) | `Japanese` | ✅ Completo |
| 한국어 (Sul Coreano) | `Korean` | ✅ Completo |
| Русский (Russo) | `Russian` | ✅ Completo |
| Українська (Ucraniano) | `Ukrainian` | ✅ Completo |
| Bahasa Indonesia | `Indonesian` | ✅ Completo |
| Filipino / Tagalog | `Filipino` | ✅ Completo |
| Tiếng Việt (Vietnamita) | `Vietnamese` | ✅ Completo |
| Norsk (Norueguês) | `Norwegian` | ✅ Completo |
| Harshen Hausa (Hauçá) | `Hausa` | ✅ Completo |
| Bamanankan (Bambara) | `Bambara` | ✅ Completo |
| Latina (Latim) | `Latin` | ✅ Completo |

A troca de idioma é feita em tempo real pelo Painel de Configurações, sem necessidade de reiniciar o aplicativo.

## ദ്ദി( • ᴗ - ) ✧ Sistemas Operacionais Suportados

O Crimson detecta automaticamente o sistema operacional em execução e adapta seu comportamento (caminhos de pasta, localização do FFmpeg, comandos de processo, etc.)

### Windows
| Versão | Status |
|---|---|
| Windows 10 / 11 | ✅ Suporte completo |

### Linux
> [!NOTE]
> No Linux, o `ffmpeg` precisa estar instalado via gerenciador de pacotes da sua distribuição. O PySide6 e demais dependências são instalados no ambiente virtual Python. Consulte o [Guia Linux](GUIA_Linux.md) para instruções detalhadas.

| Família | Exemplos de Distros | Status |
|---|---|---|
| **Arch Linux** | CachyOS *(testado)*, Manjaro, EndeavourOS, Arch puro | ✅ Suporte completo |
| **Debian / Ubuntu** | Ubuntu, Linux Mint, Pop!\_OS, Zorin OS | ✅ Suporte completo |
| **Fedora / RHEL** | Fedora, AlmaLinux, Rocky Linux | ✅ Suporte completo |
| **openSUSE** | Tumbleweed, Leap | ✅ Suporte completo |
| **Alpine Linux** | Alpine puro | ✅ Suporte completo |

## ❏ Interface Visual

### → Release 2.3.0 (Atual)
<div align="center">
  <p><b>Visão Geral da Nova Interface (PySide6 / Tema Dark)</b></p>
  <img src="Capturas/V.2.3.0/Crimson_com_janela.png" alt="Janela Principal do Crimson" width="85%">
  
  <br><br>
  
  <p><b>Download Assíncrono com Atualização em Tempo Real</b></p>
  <img src="Capturas/V.2.3.0/Crimson_download_iniciando.png" alt="Iniciando Download" width="45%">
  &nbsp;
  <img src="Capturas/V.2.3.0/Crimson_download_progresso_download.png" alt="Progresso do Download" width="45%">

  <br><br>

  <p><b>Painel de Configurações Dinâmicas e Créditos</b></p>
  <img src="Capturas/V.2.3.0/Crimson_aba_configurações.png" alt="Aba Configurações" width="45%">
  &nbsp;
  <img src="Capturas/V.2.3.0/Crimson_aba_sobre.png" alt="Aba Sobre e Repositórios" width="45%">
</div>

<br>

### ← Versões Anteriores (Histórico de Evolução)
<div align="center">
  <p><b>Release 2.2.0</b></p>
  <img src="Capturas/V.2.2.0/Crimson_com_janela.png" alt="Janela Principal V.2.2.0" width="45%">
  &nbsp;
  <img src="Capturas/V.2.2.0/Crimson_download_progresso_download.png" alt="Progresso V.2.2.0" width="45%">

  <br><br>

  <p><b>Versão Beta (Protótipo Inicial em Tkinter)</b></p>
  <img src="Capturas/Versão%20Beta/Tela%20inicial%20de%20abertura%20do%20programa%20-%20V.01.png" alt="Tela de Abertura do Programa (Loading) Beta" width="45%">
  &nbsp;
  <img src="Capturas/Versão%20Beta/Primeira%20home%20page%20do%20programa%20-%20V.01.png" alt="Home Page do Programa Beta" width="45%">
</div>

<br>

## + Guia de Uso e Configuração de Ambiente
Caso você venha a clonar este repositório para inspecionar, executar ou modificar o código através de uma IDE local, existem alguns pré-requisitos fundamentais para o funcionamento.

### Windows
O Crimson não confia na instalação global das dependências no computador do usuário. Ele exige e rastreia o **FFmpeg** em um escopo totalmente local (na mesma pasta do código):

1. **Instale as Bibliotecas**: Instale as bibliotecas com `pip install -r requirements.txt`.
2. **Setup do FFmpeg**: Crie uma pasta chamada `ffmpeg` na raiz deste projeto (onde o arquivo `Crimson.py` está localizado).
3. Baixe os binários de execução do FFmpeg (.exe) e aloque-os dentro dessa pasta (ffmpeg.exe, ffplay.exe e ffprobe.exe):
**[ » Acessar Repositório do FFmpeg Builds ](https://github.com/BtbN/FFmpeg-Builds/releases)**

4. Ao rodar o código pela IDE, o Python irá ler o caminho relativo dessa pasta de forma inteligente e injetar temporariamente nas Variáveis de Ambiente (`os.environ["PATH"]`).

### Linux
No Linux, o FFmpeg é instalado pelo sistema, não sendo necessária pasta local. Consulte o **[Guia Linux completo](GUIA_Linux.md)** para o passo a passo de instalação de dependências, execução e compilação do executável.

## ° Tecnologias Avançadas de Bypass e Otimização
O Crimson passou por otimizações no seu núcleo para resolver gargalos históricos de bloqueios anti-bot, uso excessivo de CPU e falhas de bibliotecas engessadas:
- **Bypass Anônimo (Apple Vision Pro & Android VR)**: com o versionamento de segurança agressivo (`--pre` Nightly), o Crimson acessa endpoints experimentais de alguns servidores restritos. Ele simula chamadas em nome dos óculos de realidade virtual da Apple e do Android, que recebem fluxos de dados sem limitação de cookies e qualidade (1080p e 4K puros).
- **Uso reduzido de CPU e GPU**: Adoção de PySide6 (Qt6) com renderização nativa Fusion, cache de ícones em RAM e throttling na barra de progresso, economizando cerca de 85% de ciclos da CPU gráfica.
- **Injeção Modular de Motor de Download**: O Crimson faz um parse direto com a base do GitHub. Usando apenas bibliotecas puras, ele baixa a Source Code Master e manipula o radar interno do Python (`sys.path.insert`) para forçá-lo a compilar com o novo pacote na memória.

## • Arquitetura de Compilação (O Teste de "Releases")
O Crimson nasce não só como uma utilidade do dia a dia, mas também com o papel de ser um **projeto de homologação para o sistema de "Releases" do GitHub**.

A arquitetura final do projeto tem como objetivo compilar (via **PyInstaller**) tanto as lógicas do Python quanto os binários do `FFmpeg` na construção de um único artefato autossuficiente. No Windows, esse artefato é um `.exe` portátil; no Linux, um binário ELF compilado. Esse pacote encapsulado será testado nas publicações de Release do GitHub, servindo como modelo para que qualquer pessoa consiga baixar o software de forma limpa e no melhor conceito "Plug and Play".

---

## ◉ Créditos e Repositórios
Este projeto foi criado com o auxílio de inteligências artificiais (AI), buscando melhoria contínua e novos aprendizados, mas sem omitir seu uso na estruturação e suporte à codificação. 
Além disso, só foi possível graças às excelentes comunidades *Open Source* e aos desenvolvedores e artistas que fornecem ferramentas vitais de forma livre. Meus mais profundos agradecimentos a:

### ◓ Tecnologias Base
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**: Motor principal de extração de mídias.
- **[FFmpeg Builds](https://github.com/BtbN/FFmpeg-Builds/releases)**: Processador e conversor integrado de mídia.

### ◒ Design e Ícones (Flaticon)
Os ícones utilizados na interface gráfica pertencem integralmente aos seus respectivos criadores, licenciados para uso gratuito com atribuição através da plataforma **Flaticon**:
- [Ponto de interrogação - ícone criado por Magnific - Flaticon](https://www.flaticon.com/br/icones-gratis/ponto-de-interrogacao)
- [Lixeira - ícone criado por Mayor Icons - Flaticon](https://www.flaticon.com/br/icones-gratis/desperdicio)
- [Continuar - ícone criado por sonnycandra - Flaticon](https://www.flaticon.com/br/icones-gratis/botao-play)
- [Pausar - ícone criado por Slidicon - Flaticon](https://www.flaticon.com/br/icones-gratis/pausa)
- [Configurações - ícone criado por Pixel perfect - Flaticon](https://www.flaticon.com/br/icones-gratis/configuracoes)
- [Comunidade - ícone criado por Soremba - Flaticon](https://www.flaticon.com/br/icones-gratis/comunidade)
- [Github - ícone criado por riajulislam - Flaticon](https://www.flaticon.com/br/icones-gratis/github)
- [Limpeza - ícone criado por Us and Up - Flaticon](https://www.flaticon.com/br/icones-gratis/vassoura)

---

<br>

**Desenvolvido por Luan** <br>
*Ad Infinitum*