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

        # Dados do download em andamento
        self.estado_download = "parado"  # "rodando", "pausado", "cancelado"
        self.url_atual = ""
        self.caminho_salvamento_atual = ""  # Destino final escolhido pelo usuário na janela "Salvar como"
        self.nome_temporario_atual = ""  # Nome (sem extensão) do download na pasta temporária
        self.tipo_atual = ""
        self.formato_atual = ""


# Instância única, compartilhada por todos os módulos do Crimson
estado = EstadoApp()