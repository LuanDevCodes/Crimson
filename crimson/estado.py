# Projeto Crimson - Estado compartilhado da aplicação
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

# POR QUE ESTE ARQUIVO EXISTE:
# Antes, o idioma, o tema e os dados do download atual eram variáveis globais soltas, alteradas com 'global'
# Ao dividir o programa em vários arquivos isso dá problema: 'from x import idioma_atual' copia o valor
# naquele instante, e se outro arquivo mudar o idioma depois, a cópia fica desatualizada
# A solução é guardar tudo dentro de um objeto. Todos os arquivos importam o mesmo objeto 'estado'
# e leem/escrevem nele (ex: estado.idioma_atual), então todos enxergam sempre o valor mais recente
# O Python carrega cada arquivo uma única vez, então existe só uma instância (um "singleton" natural)

from crimson.config import carregar_configuracoes

class EstadoApp:
    def __init__(self):

        # Lê as configurações salvas em disco (ou usa os valores padrão se for a primeira execução)
        config_atual = carregar_configuracoes()
        self.idioma_atual = config_atual.get("idioma", "English")
        self.tema_atual = config_atual.get("tema", "Frutiger Aero")
        self.desativar_animacoes = bool(config_atual.get("desativar_animacoes", False))

        # Opções da aba Avançado (o .get com valor padrão protege quem ainda tem um config.json antigo)
        self.baixar_playlist = bool(config_atual.get("baixar_playlist", False))
        self.qualidade_audio = config_atual.get("qualidade_audio", "livre")  # "livre", "melhor", "320", "192" ou "128"
        self.qualidade_video = config_atual.get("qualidade_video", "livre")  # "livre", "melhor", "2160", "1440", "1080", "720", "480" ou "360"
        self.pasta_padrao = config_atual.get("pasta_padrao", "")  # Vazio = sem pasta padrão (abre o "Salvar como")

        # Validação, valores estranhos (ex: config.json editado à mão) voltam para o padrão
        # (o idioma e o tema já são conferidos no idiomas.py, aqui só garanto que são textos)
        if self.qualidade_audio not in ("livre", "melhor", "320", "192", "128"):
            self.qualidade_audio = "livre"
        if self.qualidade_video not in ("livre", "melhor", "2160", "1440", "1080", "720", "480", "360"):
            self.qualidade_video = "livre"
        if not isinstance(self.pasta_padrao, str):
            self.pasta_padrao = ""
        if not isinstance(self.idioma_atual, str):
            self.idioma_atual = "English"
        if not isinstance(self.tema_atual, str):
            self.tema_atual = "Frutiger Aero"

        # Dados do download em andamento
        self.estado_download = "parado"  # "rodando", "pausado", "cancelado"
        self.url_atual = ""
        self.caminho_salvamento_atual = ""  # Destino final escolhido pelo usuário na janela "Salvar como"
        self.pasta_destino_atual = ""       # Pasta de destino quando o nome do arquivo vem do título (pasta padrão ou playlist)
        self.playlist_atual = False         # Se o download em andamento é de playlist (fixado no início, mesmo que o switch mude)
        self.nome_temporario_atual = ""     # Nome (sem extensão) do download na pasta temporária
        self.tipo_atual = ""
        self.formato_atual = ""
        self.qualidade_atual = "melhor"  # Qualidade usada no download em andamento (mantida ao pausar e retomar)

        # Arquivamento Sequencial, lista de URLs que serão baixadas uma após a outra (vazia = modo normal)
        self.fila_urls = []
        self.fila_proximo = 0  # Posição do próximo link a baixar (ao recomeçar uma fila cancelada, os já baixados são pulados)


# Instância única, compartilhada por todos os módulos do Crimson
estado = EstadoApp()