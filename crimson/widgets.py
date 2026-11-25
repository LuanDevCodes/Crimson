# Projeto Crimson - Widgets visuais personalizados (dropdown, barra de progresso, interruptor e fundo animado)
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import random       # Usado para gerar posições e tamanhos aleatórios das bolhas Frutiger Aero
import math         # Usado para a oscilação senoidal das bolhas

from PySide6.QtWidgets import QWidget, QComboBox, QProgressBar, QPushButton, QStyledItemDelegate
from PySide6.QtCore import Qt, QPointF, QTimer, QRectF
from PySide6.QtGui import (
    QColor, QCursor, QPainter, QPen, QPainterPath, QLinearGradient, QRadialGradient, QConicalGradient, QBrush,
    QImage, QPixmap
)

from crimson.estado import estado
from crimson.temas import TEMAS, VIDRO_TEMAS, cores_desativado

class ComboBoxModerno(QComboBox):

    """
    QComboBox customizado que desenha uma seta (chevron 'v') vetorial com anti-aliasing
    perfeito tanto no Windows quanto no Linux
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Limita a quantidade de itens visíveis para acionar a barra de rolagem estilizada
        self.setMaxVisibleItems(7)
        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view().setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # O delegate padrão do QComboBox ignora as regras '::item' do stylesheet (hover, altura, cantos)
        # Com o QStyledItemDelegate, a lista passa a obedecer o visual definido em estilo_lista_dropdown()
        self.setItemDelegate(QStyledItemDelegate(self))
        self.view().viewport().setAutoFillBackground(False)

        # A lista aberta mora dentro de uma "janelinha" popup separada (container)
        # Por padrão ela é quadrada e pintada com a cor de fundo da janela, criando aquela moldura "quebrada"
        # ao redor da lista arredondada, deixo o container sem borda e transparente para só a lista aparecer
        container = self.view().window()
        container.setObjectName("popupDropdown")
        container.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint
        )
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cor_seta = QColor(TEMAS[estado.tema_atual]["cor_fonte_botoes"])

        # Dropdown desativado, a seta fica no mesmo cinza do texto desativado
        if not self.isEnabled():
            cor_seta = QColor(cores_desativado(TEMAS[estado.tema_atual])[1])
        pen = QPen(cor_seta, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        cx = self.width() - 18
        cy = self.height() / 2.0

        caminho = QPainterPath()
        caminho.moveTo(QPointF(cx - 4.5, cy - 2.0))
        caminho.lineTo(QPointF(cx, cy + 2.5))
        caminho.lineTo(QPointF(cx + 4.5, cy - 2.0))
        painter.drawPath(caminho)
        painter.end()

class BarraProgressoModerna(QProgressBar):

    """
    QProgressBar customizado com renderização em cápsula e anti-aliasing
    Utiliza clipping por QPainterPath para garantir que o preenchimento (chunk)
    nunca apresente cantos retos/quadrados ao atingir as bordas da barra, seja
    no carregamento inicial (indeterminado) ou no progresso de downloads (0 a 100%)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self._pos_indeterminada = 0.0
        self._direcao = 1.0
        self._timer_indeterminado = QTimer(self)
        self._timer_indeterminado.timeout.connect(self._avancar_animacao)

    def _deve_animar(self):
        janela = self.window()
        minimizada = bool(janela and janela.isMinimized())
        return (self.minimum() == 0 and self.maximum() == 0) and (not estado.desativar_animacoes) and (not minimizada)

    def sincronizar_animacao(self):
        if self._deve_animar() and self.isVisible():
            if not self._timer_indeterminado.isActive():
                self._timer_indeterminado.start(25)  # 40 FPS suave
        else:
            if self._timer_indeterminado.isActive():
                self._timer_indeterminado.stop()
            if estado.desativar_animacoes:
                self._pos_indeterminada = 0.5
        self.update()

    def _avancar_animacao(self):
        if self._deve_animar():
            self._pos_indeterminada += 0.018 * self._direcao
            if self._pos_indeterminada >= 1.0:
                self._pos_indeterminada = 1.0
                self._direcao = -1.0
            elif self._pos_indeterminada <= 0.0:
                self._pos_indeterminada = 0.0
                self._direcao = 1.0
            self.update()
        else:
            if self._timer_indeterminado.isActive():
                self._timer_indeterminado.stop()

    def setRange(self, minimo, maximo):
        super().setRange(minimo, maximo)
        self.sincronizar_animacao()

    def showEvent(self, event):
        super().showEvent(event)
        self.sincronizar_animacao()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._timer_indeterminado.isActive():
            self._timer_indeterminado.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        raio = h / 2.0

        # Caminho exato da cápsula do trilho com recuo para a borda
        ret_trilho = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        caminho_capsula = QPainterPath()
        caminho_capsula.addRoundedRect(ret_trilho, raio - 1.0, raio - 1.0)

        cor = TEMAS[estado.tema_atual]

        # Fundo e borda do trilho conforme o tema
        if estado.tema_atual == "Frutiger Aero":
            grad_trilho = QLinearGradient(0, 0, 0, h)
            grad_trilho.setColorAt(0.0, QColor(200, 235, 255, 190))
            grad_trilho.setColorAt(0.5, QColor(235, 248, 255, 230))
            grad_trilho.setColorAt(1.0, QColor(190, 230, 255, 204))
            brush_trilho = QBrush(grad_trilho)
            pen_borda = QPen(QColor(115, 195, 250, 230), 1.5)
        elif estado.tema_atual in VIDRO_TEMAS:
            # Temas de vidro com trilho translúcido, deixando a cena aparecer por trás
            topo, base, borda = VIDRO_TEMAS[estado.tema_atual]["trilho"]
            grad_trilho = QLinearGradient(0, 0, 0, h)
            grad_trilho.setColorAt(0.0, QColor(*topo))
            grad_trilho.setColorAt(1.0, QColor(*base))
            brush_trilho = QBrush(grad_trilho)
            pen_borda = QPen(QColor(*borda), 1.2)
        elif estado.tema_atual == "Platinum Disc":
            grad_trilho = QLinearGradient(0, 0, 0, h)
            grad_trilho.setColorAt(0.0, QColor("#1A1E26"))
            grad_trilho.setColorAt(0.5, QColor("#282E3A"))
            grad_trilho.setColorAt(1.0, QColor("#1A1E26"))
            brush_trilho = QBrush(grad_trilho)
            pen_borda = QPen(QColor("#64748B"), 1.2)
        else:
            brush_trilho = QBrush(QColor(cor["cor_progresso_fundo"]))
            pen_borda = QPen(QColor(cor["cor_borda_card"]), 1.0)

        painter.fillPath(caminho_capsula, brush_trilho)

        # Clipping geométrico, garante que o chunk nunca ultrapasse a curvatura da cápsula
        painter.save()
        painter.setClipPath(caminho_capsula)

        largura_util = w - 4.0
        if self.minimum() == 0 and self.maximum() == 0:
            largura_chunk = max(90.0, largura_util * 0.32)
            deslocamento = (largura_util - largura_chunk) * self._pos_indeterminada
            ret_chunk = QRectF(2.0 + deslocamento, 2.0, largura_chunk, h - 4.0)
        else:
            val = max(self.minimum(), min(self.maximum(), self.value()))
            faixa = self.maximum() - self.minimum()
            fracao = (val - self.minimum()) / faixa if faixa > 0 else 0.0
            largura_chunk = largura_util * fracao
            ret_chunk = QRectF(2.0, 2.0, largura_chunk, h - 4.0)

        if ret_chunk.width() > 0:
            if estado.tema_atual == "Frutiger Aero":
                grad_chunk = QLinearGradient(0, 0, 0, h)
                grad_chunk.setColorAt(0.0, QColor("#AFF4FF"))
                grad_chunk.setColorAt(0.12, QColor("#52C5FF"))
                grad_chunk.setColorAt(0.48, QColor("#1AA5FF"))
                grad_chunk.setColorAt(0.52, QColor("#0087F0"))
                grad_chunk.setColorAt(1.0, QColor("#006DCF"))
                brush_chunk = QBrush(grad_chunk)
            elif estado.tema_atual in VIDRO_TEMAS:
                # Preenchimento em "plasma" com o gradiente ocupa a barra inteira, então a cor muda conforme o progresso
                cores_plasma = VIDRO_TEMAS[estado.tema_atual]["plasma"]
                grad_chunk = QLinearGradient(0, 0, w, 0)
                grad_chunk.setColorAt(0.0, QColor(cores_plasma[0]))
                grad_chunk.setColorAt(0.5, QColor(cores_plasma[1]))
                grad_chunk.setColorAt(1.0, QColor(cores_plasma[2]))
                brush_chunk = QBrush(grad_chunk)
            elif estado.tema_atual == "Platinum Disc":
                grad_chunk = QLinearGradient(0, 0, 0, h)
                grad_chunk.setColorAt(0.0, QColor("#E2E8F0"))
                grad_chunk.setColorAt(0.20, QColor("#94A3B8"))
                grad_chunk.setColorAt(0.50, QColor("#64748B"))
                grad_chunk.setColorAt(0.52, QColor("#475569"))
                grad_chunk.setColorAt(1.0, QColor("#708CAE"))
                brush_chunk = QBrush(grad_chunk)
            else:
                brush_chunk = QBrush(QColor(cor["cor_progresso_barra"]))

            caminho_chunk = QPainterPath()
            caminho_chunk.addRoundedRect(ret_chunk, raio - 2.0, raio - 2.0)
            painter.fillPath(caminho_chunk, brush_chunk)

        painter.restore()

        # Borda externa com anti-aliasing
        painter.setPen(pen_borda)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(caminho_capsula)
        painter.end()

class BotaoSwitchTema(QPushButton):

    """
    Interruptor (Switch) estilizado dinamicamente de acordo com o tema ativo
    Responsável por controlar se as animações do tema devem tocar ou ficar estáticas
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(48, 24)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        raio = h / 2.0
        ativo = self.isChecked()
        cor = TEMAS[estado.tema_atual]

        ret_trilho = QRectF(1.0, 1.0, w - 2.0, h - 2.0)
        caminho_trilho = QPainterPath()
        caminho_trilho.addRoundedRect(ret_trilho, raio - 1.0, raio - 1.0)

        if not self.isEnabled():
            # Switch bloqueado (ex: durante um download), trilho cinza, igual aos outros itens desativados
            fundo_cinza, _, borda_cinza = cores_desativado(cor)
            brush_trilho = QBrush(QColor(fundo_cinza))
            pen_borda = QPen(QColor(borda_cinza), 1.2)
        elif estado.tema_atual == "Frutiger Aero":
            if ativo:
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor("#46DC70"))
                grad_trilho.setColorAt(0.5, QColor("#24B84D"))
                grad_trilho.setColorAt(1.0, QColor("#1A9E3D"))
                pen_borda = QPen(QColor(24, 134, 52, 230), 1.3)
            else:
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor(195, 230, 255, 210))
                grad_trilho.setColorAt(0.5, QColor(225, 244, 255, 235))
                grad_trilho.setColorAt(1.0, QColor(180, 222, 250, 220))
                pen_borda = QPen(QColor(110, 182, 235, 220), 1.3)
            brush_trilho = QBrush(grad_trilho)
        elif estado.tema_atual in VIDRO_TEMAS:
            vidro = VIDRO_TEMAS[estado.tema_atual]
            if ativo:
                # Ligado, brilho de "plasma" com as cores do tema
                grad_trilho = QLinearGradient(0, 0, w, 0)
                grad_trilho.setColorAt(0.0, QColor(vidro["plasma"][0]))
                grad_trilho.setColorAt(1.0, QColor(vidro["plasma"][2]))
                pen_borda = QPen(QColor(255, 255, 255, 200), 1.2)
            else:
                # Desligado, vidro translúcido
                topo, base, borda = vidro["trilho"]
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor(*topo))
                grad_trilho.setColorAt(1.0, QColor(*base))
                pen_borda = QPen(QColor(*borda), 1.2)
            brush_trilho = QBrush(grad_trilho)
        elif estado.tema_atual == "Platinum Disc":
            if ativo:
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor("#8BA7CE"))
                grad_trilho.setColorAt(0.5, QColor("#547298"))
                grad_trilho.setColorAt(1.0, QColor("#405C80"))
                pen_borda = QPen(QColor("#C4D7F0"), 1.2)
            else:
                grad_trilho = QLinearGradient(0, 0, 0, h)
                grad_trilho.setColorAt(0.0, QColor("#181C24"))
                grad_trilho.setColorAt(0.5, QColor("#252B37"))
                grad_trilho.setColorAt(1.0, QColor("#181C24"))
                pen_borda = QPen(QColor("#64748B"), 1.2)
            brush_trilho = QBrush(grad_trilho)
        else:
            if ativo:
                brush_trilho = QBrush(QColor(cor["cor_botao_video"]))
                pen_borda = QPen(QColor(cor["cor_da_borda_botao_video"]), 1.2)
            else:
                brush_trilho = QBrush(QColor(cor["cor_progresso_fundo"]))
                pen_borda = QPen(QColor(cor["cor_borda_card"]), 1.2)

        painter.setPen(pen_borda)
        painter.setBrush(brush_trilho)
        painter.drawPath(caminho_trilho)

        diametro_pino = h - 6.0
        pos_x = (w - diametro_pino - 3.0) if ativo else 3.0
        ret_pino = QRectF(pos_x, 3.0, diametro_pino, diametro_pino)

        grad_pino = QLinearGradient(0, 3.0, 0, 3.0 + diametro_pino)
        if estado.tema_atual == "Platinum Disc":
            grad_pino.setColorAt(0.0, QColor("#FFFFFF"))
            grad_pino.setColorAt(0.5, QColor("#E2E8F0"))
            grad_pino.setColorAt(1.0, QColor("#94A3B8"))
            pen_pino = QPen(QColor("#475569"), 1.0)
        else:
            grad_pino.setColorAt(0.0, QColor("#FFFFFF"))
            grad_pino.setColorAt(1.0, QColor("#E6F2FA"))
            pen_pino = QPen(QColor(0, 0, 0, 45), 1.0)

        painter.setPen(pen_pino)
        painter.setBrush(QBrush(grad_pino))
        painter.drawEllipse(ret_pino)
        painter.end()

# --------------------------------------------------------------------------------------------------------------------
# --- Cena do Tema Star Hunter (espaço profundo) ---
# --------------------------------------------------------------------------------------------------------------------

class CenaStarHunter:

    """
    Céu do tema Star Hunter, usado no fundo da janela principal (animado) e no fundo das outras janelas (parado)
    -> Nebulosas e galáxia: desenhadas uma única vez numa imagem guardada (a parte pesada), que só "respira" e flutua
    -> Estrelas em 3 camadas de profundidade: cintilam, e as mais próximas andam mais rápido (efeito de paralaxe)
    -> De tempos em tempos, uma estrela cadente cruza o céu
    """

    def __init__(self):
        sorteio = random.Random(7)  # o céu é sempre o mesmo, só a animação muda
        self.tempo = 0
        self.estrelas = []
        cores = [QColor(255, 255, 255), QColor(200, 220, 255), QColor(255, 236, 200), QColor(190, 255, 240)]

        # Camada 0 = distante (pequena, fraca, quase parada) | camada 2 = próxima (maior, brilhante, anda mais)
        for camada, quantidade in ((0, 110), (1, 45), (2, 14)):
            for _ in range(quantidade):
                self.estrelas.append({
                    "x": sorteio.random(),
                    "y": sorteio.random(),
                    "camada": camada,
                    "raio": (0.6, 1.0, 1.6)[camada] * sorteio.uniform(0.8, 1.25),
                    "brilho": (0.45, 0.7, 0.95)[camada] * sorteio.uniform(0.75, 1.0),
                    "fase": sorteio.uniform(0, 6.28),
                    "ritmo": sorteio.uniform(0.02, 0.07),
                    "cor": sorteio.choice(cores)
                })
        self.cadente = None
        self.proxima_cadente = 120  # Quadros até a primeira estrela cadente (~5 segundos)
        self.cache = None
        self.cache_tamanho = None

    def _desenhar_cache(self, w, h):

        # Nebulosas, poeira escura e galáxia, desenhadas só quando a janela muda de tamanho
        # A imagem é 5% maior que a janela em cada lado, para o leve deslocamento das nebulosas não mostrar bordas
        margem = 0.05
        lw, lh = int(w * (1 + 2 * margem)), int(h * (1 + 2 * margem))
        imagem = QImage(lw, lh, QImage.Format.Format_ARGB32_Premultiplied)
        imagem.fill(Qt.GlobalColor.transparent)
        p = QPainter(imagem)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        sorteio = random.Random(11)
        escala = max(lw, lh)

        # O modo "Plus" soma as luzes: nuvens que se sobrepõem ficam mais brilhantes, como gás iluminado
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        nebulosas = [  # (centro x, centro y, espalhamento, cor, quantidade de nuvens, transparência)
            (0.26, 0.66, 0.22, QColor(255, 128, 48), 16, 34),   # laranja (inferior esquerda)
            (0.33, 0.58, 0.10, QColor(255, 196, 110), 8, 30),   # miolo amarelado da nebulosa laranja
            (0.70, 0.26, 0.20, QColor(70, 220, 175), 14, 30),   # verde-água (superior direita)
            (0.56, 0.42, 0.26, QColor(110, 70, 200), 14, 26),   # violeta (ligando as duas)
            (0.86, 0.80, 0.18, QColor(60, 110, 230), 10, 24)    # azul profundo (canto inferior)
        ]
        for cx, cy, espalhamento, cor, nuvens, alfa in nebulosas:
            for _ in range(nuvens):
                x = (cx + sorteio.gauss(0, espalhamento * 0.55)) * lw
                y = (cy + sorteio.gauss(0, espalhamento * 0.45)) * lh
                r = sorteio.uniform(0.06, 0.16) * escala
                grad = QRadialGradient(x, y, r)
                cor_centro = QColor(cor)
                cor_centro.setAlpha(alfa)
                cor_meio = QColor(cor)
                cor_meio.setAlpha(int(alfa * 0.35))
                cor_borda = QColor(cor)
                cor_borda.setAlpha(0)
                grad.setColorAt(0.0, cor_centro)
                grad.setColorAt(0.5, cor_meio)
                grad.setColorAt(1.0, cor_borda)
                p.setBrush(QBrush(grad))
                p.drawEllipse(QPointF(x, y), r, r)

        # Poeira escura por cima: dá textura e "recortes" nas nebulosas
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        for _ in range(18):
            x, y = sorteio.uniform(0.1, 0.9) * lw, sorteio.uniform(0.15, 0.9) * lh
            r = sorteio.uniform(0.04, 0.10) * escala
            grad = QRadialGradient(x, y, r)
            grad.setColorAt(0.0, QColor(6, 8, 22, 70))
            grad.setColorAt(1.0, QColor(6, 8, 22, 0))
            p.setBrush(QBrush(grad))
            p.drawEllipse(QPointF(x, y), r, r)

        # Galáxia espiral distante: um brilho oval inclinado, com o miolo quente e as bordas azuladas
        p.save()
        p.translate(0.82 * lw, 0.70 * lh)
        p.rotate(-16)
        largura_galaxia, altura_galaxia = 0.13 * escala, 0.035 * escala
        grad = QRadialGradient(0, 0, largura_galaxia)
        grad.setColorAt(0.0, QColor(255, 240, 235, 170))
        grad.setColorAt(0.12, QColor(255, 190, 200, 110))
        grad.setColorAt(0.45, QColor(120, 150, 255, 45))
        grad.setColorAt(1.0, QColor(80, 110, 230, 0))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        p.scale(1.0, altura_galaxia / largura_galaxia)  # "Achata" o círculo, transformando-o num oval
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(0, 0), largura_galaxia, largura_galaxia)
        p.restore()
        p.end()

        self.cache = QPixmap.fromImage(imagem)
        self.cache_tamanho = (w, h)

    def avancar(self):

        # Um passo da animação (chamado ~25 vezes por segundo)
        self.tempo += 1
        deriva = (0.000025, 0.00006, 0.00014)  # Velocidade de cada camada (paralaxe)
        for estrela in self.estrelas:
            estrela["fase"] += estrela["ritmo"]
            estrela["x"] -= deriva[estrela["camada"]]
            if estrela["x"] < -0.01:
                estrela["x"] += 1.02

        if self.cadente:
            self.cadente["vida"] += 1
            if self.cadente["vida"] > self.cadente["duracao"]:
                self.cadente = None
        else:
            self.proxima_cadente -= 1
            if self.proxima_cadente <= 0:
                angulo = math.radians(random.uniform(200, 222))  # Cai para a esquerda e para baixo
                self.cadente = {
                    "x": random.uniform(0.45, 1.0),
                    "y": random.uniform(0.02, 0.35),
                    "dx": math.cos(angulo),
                    "dy": -math.sin(angulo),
                    "vida": 0,
                    "duracao": random.randint(26, 36)
                }
                self.proxima_cadente = random.randint(140, 300)  # A próxima vem entre ~6 e ~12 segundos

    def desenhar(self, painter, w, h):

        # Fundo: azul-noite no topo, roxo profundo embaixo
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#060A1C"))
        grad.setColorAt(0.55, QColor("#0E1438"))
        grad.setColorAt(1.0, QColor("#1A0F33"))
        painter.fillRect(QRectF(0, 0, w, h), grad)

        # Nebulosas: a imagem pronta "respira" (opacidade) e flutua devagar (deslocamento)
        if self.cache_tamanho != (w, h):
            self._desenhar_cache(w, h)
        t = self.tempo
        painter.setOpacity(0.82 + 0.18 * math.sin(t * 0.012))
        dx = -w * 0.05 + math.sin(t * 0.004) * w * 0.012
        dy = -h * 0.05 + math.cos(t * 0.003) * h * 0.010
        painter.drawPixmap(QPointF(dx, dy), self.cache)
        painter.setOpacity(1.0)

        # Estrelas cintilando (a camada próxima ganha um halo de luz)
        painter.setPen(Qt.PenStyle.NoPen)
        for estrela in self.estrelas:
            pisca = 0.55 + 0.45 * math.sin(estrela["fase"])
            alfa = int(255 * estrela["brilho"] * pisca)
            x, y, r = estrela["x"] * w, estrela["y"] * h, estrela["raio"]
            if estrela["camada"] == 2:
                halo = QRadialGradient(x, y, r * 5)
                cor_halo = QColor(estrela["cor"])
                cor_halo.setAlpha(int(alfa * 0.35))
                cor_fim = QColor(estrela["cor"])
                cor_fim.setAlpha(0)
                halo.setColorAt(0.0, cor_halo)
                halo.setColorAt(1.0, cor_fim)
                painter.setBrush(QBrush(halo))
                painter.drawEllipse(QPointF(x, y), r * 5, r * 5)
            cor_estrela = QColor(estrela["cor"])
            cor_estrela.setAlpha(alfa)
            painter.setBrush(cor_estrela)
            painter.drawEllipse(QPointF(x, y), r, r)

        # Estrela cadente: cabeça brilhante com uma cauda que some aos poucos
        if self.cadente:
            c = self.cadente
            progresso = c["vida"] / c["duracao"]
            velocidade = 0.028
            hx = (c["x"] + c["dx"] * velocidade * c["vida"]) * w
            hy = (c["y"] + c["dy"] * velocidade * c["vida"]) * h
            cauda = min(w, h) * 0.22
            tx, ty = hx - c["dx"] * cauda, hy - c["dy"] * cauda
            forca = math.sin(progresso * math.pi)  # Acende e apaga suavemente
            grad = QLinearGradient(hx, hy, tx, ty)
            grad.setColorAt(0.0, QColor(255, 255, 255, int(230 * forca)))
            grad.setColorAt(0.3, QColor(190, 235, 255, int(120 * forca)))
            grad.setColorAt(1.0, QColor(150, 200, 255, 0))
            painter.setPen(QPen(QBrush(grad), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(hx, hy), QPointF(tx, ty))
            painter.setPen(Qt.PenStyle.NoPen)
            brilho = QRadialGradient(hx, hy, 7)
            brilho.setColorAt(0.0, QColor(255, 255, 255, int(220 * forca)))
            brilho.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(brilho))
            painter.drawEllipse(QPointF(hx, hy), 7, 7)

# --------------------------------------------------------------------------------------------------------------------
# --- Cena do Tema Komoki (floresta antiga com água) ---
# --------------------------------------------------------------------------------------------------------------------

class CenaKomoki:

    """
    Floresta antiga e enevoada com um espelho d'água, usada no fundo do tema Komoki
    -> Parte fixa (desenhada uma vez): névoa de luz, troncos distantes e próximos com musgo, copa, água e ilhas de musgo
    -> Parte animada: raios de sol que pulsam, folhas caindo com a brisa, luzinhas flutuando e ondulações na água
    """

    NIVEL_AGUA = 0.80  # Altura (de 0 a 1) onde começa o espelho d'água

    def __init__(self):
        sorteio = random.Random(5)  # Semente fixa: a floresta é sempre a mesma, só a animação muda
        self.tempo = 0

        # Raios de sol: posição do topo, largura, inclinação e fase (cada raio pulsa no seu ritmo)
        self.raios = [
            {"x": 0.18, "largura": 0.07, "inclinacao": 0.30, "fase": 0.0},
            {"x": 0.36, "largura": 0.11, "inclinacao": 0.34, "fase": 1.7},
            {"x": 0.52, "largura": 0.05, "inclinacao": 0.28, "fase": 3.1},
            {"x": 0.66, "largura": 0.09, "inclinacao": 0.32, "fase": 4.4}
        ]

        # Folhas: cada uma cai, balança de um lado para o outro e gira no ar
        cores_folhas = [QColor("#8DBF5A"), QColor("#6FA64A"), QColor("#B9D36A"), QColor("#4E8A43"), QColor("#D2C35A")]
        self.folhas = []
        for _ in range(13):
            self.folhas.append(self._nova_folha(sorteio, cores_folhas, sorteio.uniform(-0.1, 1.0)))
        self.cores_folhas = cores_folhas

        # Luzinhas: pontos de luz verde que flutuam devagar e acendem e apagam
        self.luzes = []
        for _ in range(16):
            self.luzes.append({
                "x": sorteio.uniform(0.05, 0.95), "y": sorteio.uniform(0.25, 0.86),
                "fase": sorteio.uniform(0, 6.28), "ritmo": sorteio.uniform(0.015, 0.035),
                "raio": sorteio.uniform(1.6, 2.6)
            })

        self.ondas = []            # Ondulações abertas na água neste momento
        self.proxima_onda = 30     # Quadros até a próxima ondulação
        self.cache = None
        self.cache_tamanho = None

    @staticmethod
    def _nova_folha(sorteio, cores, y_inicial):
        return {
            "x": sorteio.uniform(0.0, 1.0), "y": y_inicial,
            "velocidade": sorteio.uniform(0.0014, 0.0030),   # Queda por quadro (fração da altura)
            "amplitude": sorteio.uniform(0.0008, 0.0022),    # Quanto ela balança para os lados
            "fase": sorteio.uniform(0, 6.28), "ritmo": sorteio.uniform(0.03, 0.06),
            "angulo": sorteio.uniform(0, 360), "giro": sorteio.uniform(-2.5, 2.5),
            "tamanho": sorteio.uniform(5.5, 10.0), "cor": sorteio.choice(cores)
        }

    def _tronco(self, x, largura, topo, base, abertura):
        # Caminho de um tronco: sobe levemente afunilado e se abre em raízes na base
        caminho = QPainterPath()
        caminho.moveTo(x - largura * 0.42, topo)
        caminho.lineTo(x + largura * 0.42, topo)
        caminho.cubicTo(x + largura * 0.48, base * 0.7, x + largura * 0.5, base - abertura * 2,
                        x + largura * 0.5 + abertura, base)
        caminho.lineTo(x - largura * 0.5 - abertura, base)
        caminho.cubicTo(x - largura * 0.5, base - abertura * 2, x - largura * 0.48, base * 0.7,
                        x - largura * 0.42, topo)
        return caminho

    def _desenhar_cache(self, w, h):

        # Toda a parte fixa da floresta, desenhada só quando a janela muda de tamanho
        imagem = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        p = QPainter(imagem)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        sorteio = random.Random(9)
        agua = h * self.NIVEL_AGUA

        # Fundo: copa escura no alto, uma clareira de névoa iluminada e a mata escurecendo até a água
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#2E5640"))
        grad.setColorAt(0.20, QColor("#6E9A6E"))
        grad.setColorAt(0.45, QColor("#4B7A5E"))
        grad.setColorAt(0.78, QColor("#24473B"))
        grad.setColorAt(1.0, QColor("#0F2626"))
        p.fillRect(QRectF(0, 0, w, h), grad)

        # Troncos distantes, apagados pela neblina
        for x in (0.12, 0.24, 0.44, 0.58, 0.83, 0.97):
            largura = w * sorteio.uniform(0.035, 0.055)
            p.setBrush(QColor(150, 190, 160, 70))
            p.drawPath(self._tronco(x * w, largura, 0, agua, largura * 0.4))

        # Faixa de neblina no meio da mata
        neblina = QLinearGradient(0, h * 0.30, 0, h * 0.70)
        neblina.setColorAt(0.0, QColor(210, 235, 200, 0))
        neblina.setColorAt(0.5, QColor(210, 235, 200, 45))
        neblina.setColorAt(1.0, QColor(210, 235, 200, 0))
        p.fillRect(QRectF(0, 0, w, h), neblina)

        # Troncos próximos, grossos e cobertos de musgo do lado da luz
        troncos = [(0.05, 0.12), (0.29, 0.07), (0.74, 0.13), (0.95, 0.09)]
        caminhos_troncos = []
        for x, fracao in troncos:
            largura = w * fracao
            caminho = self._tronco(x * w, largura, 0, agua + h * 0.01, largura * 0.55)
            caminhos_troncos.append(caminho)
            casca = QLinearGradient(x * w - largura / 2, 0, x * w + largura / 2, 0)
            casca.setColorAt(0.0, QColor("#4F7B4C"))   # lado iluminado, com musgo
            casca.setColorAt(0.35, QColor("#2A4A39"))
            casca.setColorAt(1.0, QColor("#15291F"))   # lado na sombra
            p.setBrush(QBrush(casca))
            p.drawPath(caminho)

            # Faixas de musgo escorrendo pelo lado iluminado do tronco
            # Cada faixa é um contorno ondulado, mais fino nas pontas, que aparece e some suavemente (gradiente)
            for _ in range(4):
                largura_faixa = largura * sorteio.uniform(0.05, 0.11)
                x_faixa = x * w - largura * sorteio.uniform(0.12, 0.38)
                y_inicio = sorteio.uniform(0.05, 0.55) * agua
                comprimento = sorteio.uniform(0.20, 0.45) * agua
                fase = sorteio.uniform(0, 6.28)
                passos = 10
                lado_esquerdo, lado_direito = [], []
                for i in range(passos + 1):
                    y = y_inicio + comprimento * i / passos
                    ondulacao = math.sin(i * 0.9 + fase) * largura_faixa * 0.4      # Faz a faixa serpentear
                    metade = largura_faixa * 0.5 * (0.35 + 0.65 * math.sin(math.pi * i / passos))  # Afina nas pontas
                    lado_esquerdo.append(QPointF(x_faixa + ondulacao - metade, y))
                    lado_direito.append(QPointF(x_faixa + ondulacao + metade, y))
                faixa = QPainterPath()
                faixa.moveTo(lado_esquerdo[0])
                for ponto in lado_esquerdo[1:] + lado_direito[::-1]:
                    faixa.lineTo(ponto)
                faixa.closeSubpath()
                musgo = QLinearGradient(0, y_inicio, 0, y_inicio + comprimento)
                musgo.setColorAt(0.0, QColor(120, 175, 90, 0))
                musgo.setColorAt(0.5, QColor(120, 175, 90, sorteio.randint(70, 110)))
                musgo.setColorAt(1.0, QColor(120, 175, 90, 0))
                p.setBrush(QBrush(musgo))
                p.drawPath(faixa)

        # Copa: tufos de folhagem escura emoldurando o topo, com algumas folhas iluminadas
        for _ in range(46):
            cx = sorteio.uniform(-0.05, 1.05) * w
            cy = sorteio.uniform(-0.06, 0.10) * h
            r = sorteio.uniform(0.03, 0.08) * w
            p.setBrush(QColor(sorteio.choice(["#18352A", "#1E3F30", "#234836", "#2F5A3E"])))
            p.drawEllipse(QPointF(cx, cy), r, r * 0.75)
        for _ in range(18):
            cx, cy = sorteio.uniform(0, 1) * w, sorteio.uniform(0.0, 0.12) * h
            p.setBrush(QColor(140, 190, 100, 70))
            p.drawEllipse(QPointF(cx, cy), w * 0.012, w * 0.008)

        # Água: verde-azulada, com o reflexo dos troncos de cabeça para baixo
        agua_grad = QLinearGradient(0, agua, 0, h)
        agua_grad.setColorAt(0.0, QColor("#2C5E58"))
        agua_grad.setColorAt(1.0, QColor("#0D2827"))
        p.fillRect(QRectF(0, agua, w, h - agua), agua_grad)
        p.save()
        p.setClipRect(QRectF(0, agua, w, h - agua))
        p.translate(0, agua * 2)
        p.scale(1, -1)  # Espelha na vertical, a partir do nível da água
        p.setBrush(QColor(10, 30, 26, 90))
        for caminho in caminhos_troncos:
            p.drawPath(caminho)
        p.restore()
        p.setBrush(QColor(200, 240, 215, 40))
        p.drawRect(QRectF(0, agua - 1, w, 1.5))  # Linha de luz na superfície

        # Ilhas de musgo sobre a água (verde vivo no topo, escuras embaixo)
        for x, y, largura in ((0.18, 0.90, 0.16), (0.52, 0.86, 0.10), (0.86, 0.93, 0.18), (0.40, 0.97, 0.12)):
            ilha = QLinearGradient(0, y * h - largura * w * 0.15, 0, y * h + largura * w * 0.12)
            ilha.setColorAt(0.0, QColor("#7DB863"))
            ilha.setColorAt(0.5, QColor("#3F7340"))
            ilha.setColorAt(1.0, QColor("#1C3A2A"))
            p.setBrush(QBrush(ilha))
            p.drawEllipse(QPointF(x * w, y * h), largura * w * 0.5, largura * w * 0.13)
        p.end()

        self.cache = QPixmap.fromImage(imagem)
        self.cache_tamanho = (w, h)

    def avancar(self):

        # Um passo da animação (chamado ~25 vezes por segundo)
        self.tempo += 1
        vento = 0.00035 + math.sin(self.tempo * 0.006) * 0.0006  # Brisa que vai e volta

        for folha in self.folhas:
            folha["fase"] += folha["ritmo"]
            folha["y"] += folha["velocidade"]
            folha["x"] += vento + math.cos(folha["fase"]) * folha["amplitude"]
            folha["angulo"] += folha["giro"] + vento * 900
            # Saiu da tela: volta a cair do topo, numa posição nova
            if folha["y"] > 1.05 or folha["x"] < -0.08 or folha["x"] > 1.08:
                nova = self._nova_folha(random, self.cores_folhas, random.uniform(-0.15, -0.03))
                folha.update(nova)

        for luz in self.luzes:
            luz["fase"] += luz["ritmo"]
            luz["x"] += math.sin(luz["fase"] * 0.7) * 0.0005
            luz["y"] += math.cos(luz["fase"] * 0.5) * 0.0004

        # Ondulações: nascem de tempos em tempos e se abrem até sumir
        for onda in self.ondas:
            onda["vida"] += 1
        self.ondas = [onda for onda in self.ondas if onda["vida"] < 80]
        self.proxima_onda -= 1
        if self.proxima_onda <= 0:
            self.ondas.append({"x": random.uniform(0.05, 0.95),
                               "y": random.uniform(self.NIVEL_AGUA + 0.03, 0.97), "vida": 0})
            self.proxima_onda = random.randint(50, 130)

    def desenhar(self, painter, w, h):

        # Parte fixa da floresta (imagem pronta)
        if self.cache_tamanho != (w, h):
            self._desenhar_cache(w, h)
        painter.drawPixmap(0, 0, self.cache)
        t = self.tempo
        painter.setPen(Qt.PenStyle.NoPen)

        # Raios de sol atravessando a copa: faixas inclinadas de luz dourada que pulsam e balançam
        for raio in self.raios:
            forca = 0.65 + 0.35 * math.sin(t * 0.018 + raio["fase"])
            x_topo = (raio["x"] + math.sin(t * 0.004 + raio["fase"]) * 0.01) * w
            largura = raio["largura"] * w
            deslocamento = raio["inclinacao"] * h  # Quanto o raio anda para a direita até chegar embaixo
            caminho = QPainterPath()
            caminho.moveTo(x_topo, 0)
            caminho.lineTo(x_topo + largura, 0)
            caminho.lineTo(x_topo + largura * 2.2 + deslocamento, h * self.NIVEL_AGUA)
            caminho.lineTo(x_topo + deslocamento, h * self.NIVEL_AGUA)
            caminho.closeSubpath()
            luz = QLinearGradient(0, 0, 0, h * self.NIVEL_AGUA)
            luz.setColorAt(0.0, QColor(255, 245, 200, int(70 * forca)))
            luz.setColorAt(0.6, QColor(255, 240, 190, int(28 * forca)))
            luz.setColorAt(1.0, QColor(255, 240, 190, 0))
            painter.setBrush(QBrush(luz))
            painter.drawPath(caminho)

        # Ondulações na água: elipses achatadas que se abrem e somem
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for onda in self.ondas:
            progresso = onda["vida"] / 80.0
            raio_onda = 4 + progresso * 34
            alfa = int(110 * (1 - progresso))
            painter.setPen(QPen(QColor(210, 245, 230, alfa), 1.0))
            painter.drawEllipse(QPointF(onda["x"] * w, onda["y"] * h), raio_onda, raio_onda * 0.28)
        painter.setPen(Qt.PenStyle.NoPen)

        # Luzinhas flutuando (como vaga-lumes ou espíritos da floresta)
        for luz_v in self.luzes:
            brilho = 0.5 + 0.5 * math.sin(luz_v["fase"])
            x, y, r = luz_v["x"] * w, luz_v["y"] * h, luz_v["raio"]
            halo = QRadialGradient(x, y, r * 5)
            halo.setColorAt(0.0, QColor(215, 255, 160, int(150 * brilho)))
            halo.setColorAt(1.0, QColor(215, 255, 160, 0))
            painter.setBrush(QBrush(halo))
            painter.drawEllipse(QPointF(x, y), r * 5, r * 5)
            painter.setBrush(QColor(240, 255, 210, int(230 * brilho)))
            painter.drawEllipse(QPointF(x, y), r * 0.6, r * 0.6)

        # Folhas caindo: cada uma gira e "vira" (o achatamento imita a folha girando em 3D)
        for folha in self.folhas:
            s = folha["tamanho"]
            painter.save()
            painter.translate(folha["x"] * w, folha["y"] * h)
            painter.rotate(folha["angulo"])
            painter.scale(1.0, 0.35 + 0.65 * abs(math.cos(folha["fase"] * 1.3)))
            forma = QPainterPath()
            forma.moveTo(-s, 0)
            forma.quadTo(0, -s * 0.55, s, 0)
            forma.quadTo(0, s * 0.55, -s, 0)
            painter.setBrush(folha["cor"])
            painter.drawPath(forma)
            painter.setPen(QPen(QColor(40, 70, 30, 120), 0.8))  # Nervura central
            painter.drawLine(QPointF(-s * 0.85, 0), QPointF(s * 0.85, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.restore()

# --------------------------------------------------------------------------------------------------------------------
# --- Cena do Tema Time Moves Slow (fim de tarde no interior, em pixel art) ---
# --------------------------------------------------------------------------------------------------------------------

class CenaTimeMovesSlow:

    """
    Pôr do sol numa cidadezinha do interior do Sul/Sudeste, em pixel art, onde o tempo parece ter parado
    -> Técnica: a cena é desenhada numa imagem minúscula (~220 px de largura) e ampliada sem suavização,
       num fator inteiro, então cada pixel da arte vira um quadradinho do mesmo tamanho na tela
    -> Parte fixa: céu em faixas de cor, sol no horizonte, morros e as silhuetas (casas, araucárias e postes)
    -> Parte animada (quase parada, de propósito): nuvens muito lentas, estrelas cintilando, fios balançando
       com o vento, o poste de luz que pisca de vez em quando, uma janela que apaga e acende e
       um bando de passarinhos cruzando o céu
    """

    LARGURA_ARTE = 220        # Largura aproximada da imagem pequena (em "pixels de arte")
    COR_SILHUETA = "#130A13"  # Quase preto, puxado para o roxo
    CORES_CEU = [             # Do alto do céu até o horizonte
        (0.00, (28, 20, 51)), (0.30, (58, 31, 74)), (0.55, (122, 46, 88)),
        (0.72, (194, 58, 62)), (0.86, (232, 104, 58)), (1.00, (247, 178, 94))
    ]

    def __init__(self):
        self.tempo = 0
        self.tamanho = None       # (largura, altura) da janela para a qual a arte foi preparada
        self.escala = 3           # Tamanho de cada pixel da arte na tela
        self.poste_aceso = True
        self.proxima_piscada = 300
        self.piscadas = 0
        self.janela_acesa = True
        self.proxima_janela = 900
        self.bando = None           # Bando de passarinhos cruzando o céu (None quando não há nenhum)
        self.proximo_bando = 250    # Quadros até o próximo bando (~10 segundos)

    def _cor_ceu(self, t):
        # Mistura as cores do céu conforme a altura (t = 0 no topo, 1 no horizonte)
        for (t1, c1), (t2, c2) in zip(self.CORES_CEU, self.CORES_CEU[1:]):
            if t <= t2:
                f = (t - t1) / (t2 - t1)
                return QColor(*(int(a + (b - a) * f) for a, b in zip(c1, c2)))
        return QColor(*self.CORES_CEU[-1][1])

    @staticmethod
    def _araucaria(p, x, base, altura, abertura):
        # Araucária: tronco fino e reto com a copa em forma de taça (galhos subindo até um topo achatado)
        topo = base - altura
        p.drawRect(x, topo + 3, 1, altura - 3)
        for lado in (-1, 1):
            for k in range(4):
                # Cada galho sai do tronco e sobe até a borda da copa, terminando num tufo de folhas
                ponta_x = x + lado * int(abertura * (1.0 - k * 0.22))
                ponta_y = topo - (3 - k) // 2
                p.drawLine(x, topo + 3 + k * 2, ponta_x, ponta_y)
                p.drawEllipse(ponta_x - 2, ponta_y - 1, 4, 2)
        p.drawEllipse(x - 2, topo - 1, 4, 2)

    @staticmethod
    def _fio(p, x1, y1, x2, y2, curvatura):
        # Fio entre dois postes, caindo numa curva suave no meio (como um fio de verdade)
        pontos = []
        passos = max(4, abs(x2 - x1) // 3)
        for i in range(passos + 1):
            t = i / passos
            pontos.append(QPointF(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t + curvatura * 4 * t * (1 - t)))
        for a, b in zip(pontos, pontos[1:]):
            p.drawLine(a, b)

    def _curvatura(self, curva, fase):
        # Curvatura do fio neste instante: o vento fica mais forte e mais fraco devagar, e o fio balança junto
        # O balanço é bem lento (um vai e volta a cada ~21 segundos), combinando com a calma do tema
        forca_vento = 0.6 + 0.4 * math.sin(self.tempo * 0.0015)
        return curva + math.sin(self.tempo * 0.012 + fase) * 1.3 * forca_vento

    def _preparar(self, w, h):

        # Monta as camadas fixas na resolução da arte (só quando a janela muda de tamanho)
        self.escala = max(2, round(w / self.LARGURA_ARTE))
        lw, lh = math.ceil(w / self.escala), math.ceil(h / self.escala)
        self.lw, self.lh = lw, lh
        sorteio = random.Random(3)
        horizonte = int(lh * 0.74)
        chao = int(lh * 0.88)

        # --- Céu em faixas de cor, com um "xadrez" de pixels (dithering) na transição entre as faixas ---
        self.ceu = QImage(lw, lh, QImage.Format.Format_RGB32)
        p = QPainter(self.ceu)
        faixas = 14
        for y in range(lh):
            posicao = min(y / horizonte, 0.999) * faixas
            faixa = int(posicao)
            p.fillRect(0, y, lw, 1, self._cor_ceu((faixa + 0.5) / faixas))
            if posicao - faixa > 0.72 and faixa + 1 < faixas:
                proxima = self._cor_ceu((faixa + 1.5) / faixas)
                for x in range(y % 2, lw, 2):
                    p.fillRect(x, y, 1, 1, proxima)

        # Sol se pondo: anéis de luz em degraus (sem degradê suave, como na pixel art)
        sol_x = int(lw * 0.46)
        p.setPen(Qt.PenStyle.NoPen)
        for raio, cor in ((15, QColor(247, 160, 80, 90)), (11, QColor(250, 190, 100, 150)), (8, QColor(255, 214, 140)), (6, QColor(255, 232, 170))):
            p.setBrush(cor)
            p.drawEllipse(sol_x - raio, horizonte - raio, raio * 2, raio * 2)

        # Morros distantes (roxo) e mais próximos (mais escuros), cobrindo a metade de baixo do sol
        for cor, nivel, ondas in ((QColor("#4A2342"), horizonte - 2, (0.05, 3, 0.13, 2)),
                                  (QColor("#2C1430"), horizonte + 5, (0.035, 4, 0.09, 2))):
            contorno = QPainterPath()
            contorno.moveTo(0, lh)
            for x in range(0, lw + 4, 3):
                contorno.lineTo(x, nivel + math.sin(x * ondas[0]) * ondas[1] + math.sin(x * ondas[2] + 1) * ondas[3])
            contorno.lineTo(lw, lh)
            contorno.closeSubpath()
            p.setBrush(cor)
            p.drawPath(contorno)
        p.end()

        # --- Silhuetas: tudo o que fica na frente do céu, numa imagem com fundo transparente ---
        self.silhuetas = QImage(lw, lh, QImage.Format.Format_ARGB32_Premultiplied)
        self.silhuetas.fill(Qt.GlobalColor.transparent)
        p = QPainter(self.silhuetas)
        p.setPen(Qt.PenStyle.NoPen)

        # Araucárias distantes (num roxo mais claro, como se estivessem no meio da neblina do fim de tarde)
        p.setPen(QColor("#3A1A34"))
        p.setBrush(QColor("#3A1A34"))
        for fx, altura, abertura in ((0.50, 18, 6), (0.58, 14, 5), (0.92, 20, 7)):
            self._araucaria(p, int(lw * fx), horizonte + 6, altura, abertura)

        cor = QColor(self.COR_SILHUETA)
        p.setPen(cor)
        p.setBrush(cor)

        # Chão e arbustos
        p.drawRect(0, chao, lw, lh - chao)
        for _ in range(int(lw / 6)):
            bx = sorteio.randint(0, lw)
            raio = sorteio.randint(2, 5)
            p.drawEllipse(bx - raio, chao - raio + 1, raio * 2, raio * 2)

        # Casas com janelas (as posições das janelas ficam guardadas para acender a luz depois)
        self.janelas = []
        for fx, largura, altura in ((0.08, 24, 12), (0.80, 28, 14)):
            cx = int(lw * fx)
            p.drawRect(cx, chao - altura, largura, altura)
            telhado = QPainterPath()
            telhado.moveTo(cx - 2, chao - altura)
            telhado.lineTo(cx + largura // 2, chao - altura - 8)
            telhado.lineTo(cx + largura + 2, chao - altura)
            telhado.closeSubpath()
            p.drawPath(telhado)
            p.drawRect(cx + largura - 6, chao - altura - 9, 2, 5)   # Chaminé
            for jx in range(cx + 4, cx + largura - 4, 8):
                self.janelas.append((jx, chao - altura + 4))

        # Araucárias próximas
        for fx, altura, abertura in ((0.27, 30, 10), (0.66, 24, 8)):
            self._araucaria(p, int(lw * fx), chao, altura, abertura)

        # Postes com travessas e fios caindo em curva entre eles
        topos = []
        for fx in (0.17, 0.53, 0.89):
            px = int(lw * fx)
            topo = chao - int(lh * 0.22)
            p.drawRect(px, topo, 1, chao - topo)
            p.drawRect(px - 5, topo + 2, 11, 1)            # Travessa de cima
            p.drawRect(px - 3, topo + 6, 7, 1)             # Travessa de baixo
            for dx in (-5, 0, 5):
                p.drawRect(px + dx, topo + 1, 1, 1)        # Isoladores
            topos.append((px, topo + 2))
        p.drawRect(topos[1][0] + 1, topos[1][1] + 7, 3, 5)  # Transformador no poste do meio

        # Fios: não entram na imagem fixa, pois balançam com o vento (são desenhados a cada quadro)
        # Cada fio guarda (x1, y1, x2, y2, curvatura, fase do balanço); os 3 fios de um mesmo vão balançam quase juntos
        self.fios = []
        pontos_fio = [(-2, topos[0][1] + 3)] + topos + [(lw + 2, topos[2][1] + 4)]
        fases_vaos = [sorteio.uniform(0, 6.28) for _ in range(len(pontos_fio) - 1)]
        for desvio, curva in ((-5, 5), (0, 7), (5, 6)):
            for vao, ((x1, y1), (x2, y2)) in enumerate(zip(pontos_fio, pontos_fio[1:])):
                self.fios.append((x1 + desvio, y1, x2 + desvio, y2, curva, fases_vaos[vao] + sorteio.uniform(0, 0.6)))

        # Fios de um poste mais próximo, fora da tela à direita, cruzando o céu lá no alto
        for y_inicio, curva in ((int(lh * 0.10), 10), (int(lh * 0.14), 12)):
            self.fios.append((lw + 2, y_inicio, -2, y_inicio + int(lh * 0.08), curva, sorteio.uniform(0, 6.28)))

        # Passarinhos pousados no fio do meio (os fios do meio são os itens 4 a 7 da lista; o vão 1 e o 2 ficam entre os postes)
        self.pousados = []
        for fx in (0.34, 0.38, 0.72):
            x = int(lw * fx)
            vao = 1 if x < topos[1][0] else 2
            self.pousados.append((x, 4 + vao))

        # Poste de luz da rua: haste, braço curvo e a luminária (a luz dela é desenhada na parte animada)
        lx = int(lw * 0.765)
        topo_luz = chao - int(lh * 0.17)
        p.drawRect(lx, topo_luz, 1, chao - topo_luz)
        p.drawRect(lx - 4, topo_luz, 4, 1)
        p.drawRect(lx - 6, topo_luz, 3, 2)
        self.lampada = (lx - 5, topo_luz + 2)
        p.end()

        # Estrelas (só na parte alta do céu) e nuvens (cada nuvem é uma imagenzinha pronta)
        self.estrelas = [{"x": sorteio.randint(0, lw - 1), "y": sorteio.randint(0, int(horizonte * 0.42)),
                          "fase": sorteio.uniform(0, 6.28), "ritmo": sorteio.uniform(0.02, 0.06),
                          "brilho": sorteio.uniform(0.4, 1.0)} for _ in range(55)]
        self.nuvens = []
        for _ in range(5):
            largura = sorteio.randint(14, 36)
            self.nuvens.append({"x": sorteio.uniform(-largura, lw), "y": sorteio.randint(int(lh * 0.28), int(lh * 0.60)),
                                "velocidade": sorteio.uniform(0.006, 0.016), "imagem": self._nuvem(sorteio, largura)})
        self.tamanho = (w, h)

    @staticmethod
    def _nuvem(sorteio, largura):
        # Nuvem em pixel art: degraus de retângulos, escura em cima e iluminada pelo sol na borda de baixo
        altura = max(4, largura // 5)
        imagem = QImage(largura, altura + 1, QImage.Format.Format_ARGB32_Premultiplied)
        imagem.fill(Qt.GlobalColor.transparent)
        p = QPainter(imagem)
        for linha in range(altura):
            recuo = int(abs(linha - altura * 0.6) * sorteio.uniform(1.0, 2.2))
            p.fillRect(recuo, linha, max(2, largura - recuo * 2), 1, QColor(90, 36, 64))
        p.fillRect(2, altura - 1, largura - 4, 1, QColor(224, 106, 62))   # Borda iluminada pelo sol
        p.fillRect(4, altura, largura - 8, 1, QColor(170, 70, 60))
        p.end()
        return imagem

    def avancar(self):

        # Um passo da animação: quase tudo muda muito devagar, para passar a sensação de tempo parado
        self.tempo += 1
        if self.tamanho is None:
            return
        for nuvem in self.nuvens:
            nuvem["x"] += nuvem["velocidade"]
            if nuvem["x"] > self.lw:
                nuvem["x"] = -nuvem["imagem"].width()
        for estrela in self.estrelas:
            estrela["fase"] += estrela["ritmo"]

        # O poste de luz pisca de vez em quando (algumas piscadas rápidas, depois fica aceso de novo)
        self.proxima_piscada -= 1
        if self.piscadas > 0:
            if self.tempo % 3 == 0:
                self.poste_aceso = not self.poste_aceso
                self.piscadas -= 1
        elif self.proxima_piscada <= 0:
            self.piscadas = random.choice((2, 4, 6))
            self.proxima_piscada = random.randint(400, 1000)
        else:
            self.poste_aceso = True

        # Uma das janelas apaga e acende muito raramente (alguém andando pela casa)
        self.proxima_janela -= 1
        if self.proxima_janela <= 0:
            self.janela_acesa = not self.janela_acesa
            self.proxima_janela = random.randint(600, 1500)

        # Bando de passarinhos voando devagar pelo céu, em formação de "V"
        if self.bando:
            self.bando["x"] += 0.25
            if self.bando["x"] > self.lw + 30:
                self.bando = None
        else:
            self.proximo_bando -= 1
            if self.proximo_bando <= 0:
                self.bando = self._novo_bando()
                self.proximo_bando = random.randint(700, 1600)  # O próximo vem entre ~30 e ~60 segundos

    def _novo_bando(self):

        # Monta a formação: o líder na frente e os outros atrás, alternando entre os dois lados do "V"
        # Cada passarinho tem um pequeno desvio e uma fase própria, para as asas não baterem todas juntas
        # O bando voa no alto do céu, acima dos fios, onde não se confunde com as linhas e não fica atrás dos cards
        membros = [(0, 0, random.randint(0, 15))]
        for i in range(1, random.randint(4, 7)):
            fileira = (i + 1) // 2
            lado = 1 if i % 2 else -1
            membros.append((-6 * fileira + random.randint(-1, 1), lado * fileira + random.randint(-1, 0), random.randint(0, 15)))
        return {"x": -10.0, "y": random.randint(int(self.lh * 0.05), int(self.lh * 0.08)), "membros": membros}

    def desenhar(self, painter, w, h):
        if self.tamanho != (w, h):
            self._preparar(w, h)

        # Monta o quadro na resolução da arte: céu, estrelas, nuvens, passarinho, silhuetas e luzes
        quadro = self.ceu.copy()
        p = QPainter(quadro)  # Sem antialiasing: as bordas ficam "quadradas", como na pixel art
        p.setPen(Qt.PenStyle.NoPen)
        for estrela in self.estrelas:
            pisca = 0.5 + 0.5 * math.sin(estrela["fase"])
            alfa = int(255 * estrela["brilho"] * (0.25 + 0.75 * pisca))
            x, y = estrela["x"], estrela["y"]
            p.fillRect(x, y, 1, 1, QColor(255, 236, 220, alfa))
            # As estrelas mais fortes, no auge do brilho, ganham uma cruzinha de luz (o "cintilar" da pixel art)
            if estrela["brilho"] > 0.75 and pisca > 0.8:
                cor_raio = QColor(255, 236, 220, alfa // 3)
                for rx, ry in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p.fillRect(x + rx, y + ry, 1, 1, cor_raio)
        for nuvem in self.nuvens:
            p.drawImage(int(nuvem["x"]), nuvem["y"], nuvem["imagem"])
        if self.bando:
            cor_passaro = QColor(self.COR_SILHUETA)
            for dx, dy, fase in self.bando["membros"]:
                # Cada passarinho sobe e desce um pouquinho e bate as asas no seu próprio ritmo
                x = int(self.bando["x"] + dx)
                y = int(self.bando["y"] + dy + math.sin((self.tempo + fase) * 0.05))
                p.fillRect(x, y, 1, 1, cor_passaro)
                if ((self.tempo + fase) // 8) % 2 == 0:   # Asas para cima
                    p.fillRect(x - 2, y - 1, 2, 1, cor_passaro)
                    p.fillRect(x + 1, y - 1, 2, 1, cor_passaro)
                else:                                      # Asas abertas
                    p.fillRect(x - 2, y, 2, 1, cor_passaro)
                    p.fillRect(x + 1, y, 2, 1, cor_passaro)
        p.drawImage(0, 0, self.silhuetas)

        # Fios balançando com o vento e os passarinhos pousados, que balançam junto com o fio
        cor_silhueta = QColor(self.COR_SILHUETA)
        p.setPen(cor_silhueta)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for x1, y1, x2, y2, curva, fase in self.fios:
            self._fio(p, x1, y1, x2, y2, self._curvatura(curva, fase))
        p.setPen(Qt.PenStyle.NoPen)
        for x, indice in self.pousados:
            x1, y1, x2, y2, curva, fase = self.fios[indice]
            t = (x - x1) / (x2 - x1)
            y = int(y1 + (y2 - y1) * t + self._curvatura(curva, fase) * 4 * t * (1 - t))
            p.fillRect(x, y - 2, 2, 2, cor_silhueta)
            p.fillRect(x + 2, y - 1, 1, 1, cor_silhueta)

        # Janelas acesas (amarelo quente); a primeira é a que apaga e acende
        for indice, (jx, jy) in enumerate(self.janelas):
            if indice == 0 and not self.janela_acesa:
                continue
            p.fillRect(jx, jy, 3, 3, QColor(255, 212, 90))

        # Luz do poste da rua: a luminária e um cone de luz em degraus até o chão
        if self.poste_aceso:
            lx, ly = self.lampada
            p.fillRect(lx - 1, ly - 1, 3, 1, QColor(255, 240, 180))
            chao = int(self.lh * 0.88)
            for degrau, alfa in ((0, 40), (1, 24), (2, 12)):
                abertura = 3 + degrau * 4
                cone = QPainterPath()
                cone.moveTo(lx - 1 - degrau, ly)
                cone.lineTo(lx + 1 + degrau, ly)
                cone.lineTo(lx + abertura, chao)
                cone.lineTo(lx - abertura, chao)
                cone.closeSubpath()
                p.setBrush(QColor(255, 210, 120, alfa))
                p.drawPath(cone)
        p.end()

        # Amplia a arte para o tamanho da janela, sem suavizar (cada pixel vira um quadradinho nítido)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawImage(QRectF(0, 0, self.lw * self.escala, self.lh * self.escala), quadro)
        painter.restore()

# Cena de cada tema de vidro (usada no fundo da janela principal e dos diálogos)
CENAS_TEMATICAS = {"Star Hunter": CenaStarHunter, "Komoki": CenaKomoki, "Time Moves Slow": CenaTimeMovesSlow}

def pintar_fundo_cena(janela):

    """
    Pinta a cena do tema atual (parada) no fundo de uma janela de diálogo
    Cada janela guarda as próprias cenas, assim a imagem da parte fixa fica no tamanho certo para ela
    """

    if not hasattr(janela, "_cenas"):
        janela._cenas = {}
    if estado.tema_atual not in janela._cenas:
        janela._cenas[estado.tema_atual] = CENAS_TEMATICAS[estado.tema_atual]()
    painter = QPainter(janela)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    janela._cenas[estado.tema_atual].desenhar(painter, janela.width(), janela.height())

    # Véu escuro leve: nos diálogos, títulos e instruções ficam direto sobre a cena (sem card), e o véu garante a leitura
    # Cada tema pode pedir um véu mais forte com "veu_dialogo", sem essa chave, usa o padrão 60
    opacidade_veu = VIDRO_TEMAS[estado.tema_atual].get("veu_dialogo", 60)
    painter.fillRect(janela.rect(), QColor(0, 0, 0, opacidade_veu))
    painter.end()

# --------------------------------------------------------------------------------------------------------------------
# --- Superfície de Fundo Dinâmica & Efeito Frutiger Aero ---
# --------------------------------------------------------------------------------------------------------------------

class WidgetFundoCrimson(QWidget):
    """
    Widget central com suporte a renderização dinâmica
    - 'Frutiger Aero': desenha gradiente celeste límpido, feixe solar e bolhas vítreas flutuantes
    - 'Platinum Disc': desenha uma superfície metálica de platina escovada com disco de sulcos concêntricos
      e reflexo anisotrópico em rotação contínua (estética vinil/CD de platina e cromo polido)
    - 'Star Hunter': desenha o espaço profundo com nebulosas, estrelas cintilando e estrelas cadentes
    - 'Komoki': desenha uma floresta antiga com raios de sol, folhas caindo, luzinhas e água
    - 'Time Moves Slow': desenha um pôr do sol no interior em pixel art, com animações bem lentas
    - Outros temas: preenchimento estático suave poupando 100% de CPU
    """

    # Temas que têm animação no fundo (os outros são estáticos e não gastam CPU)
    TEMAS_ANIMADOS = ("Frutiger Aero", "Platinum Disc") + tuple(CENAS_TEMATICAS)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bolhas = []
        self.angulo_platina = 0.0
        self.brilho_platina = 0.0
        # Uma cena para cada tema de vidro (ex: {"Star Hunter": CenaStarHunter(), "Komoki": CenaKomoki()})
        self.cenas = {nome: Cena() for nome, Cena in CENAS_TEMATICAS.items()}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._atualizar_animacao)
        self._inicializar_bolhas()

    def _inicializar_bolhas(self):
        self.bolhas = []
        for _ in range(12):
            self.bolhas.append({
                "x": random.uniform(0.04, 0.96),
                "y": random.uniform(0.0, 1.0),
                "raio": random.uniform(10, 26),
                "velocidade": random.uniform(0.0016, 0.0038),
                "opacidade": random.uniform(0.35, 0.75),
                "fase": random.uniform(0.0, 6.28),
                "frequencia": random.uniform(0.03, 0.06)
            })

    def sincronizar_tema(self):
        janela = self.window()
        minimizada = bool(janela and janela.isMinimized())
        if estado.tema_atual in self.TEMAS_ANIMADOS and not estado.desativar_animacoes and not minimizada:
            if not self.timer.isActive():
                self.timer.start(40)  # ~25 FPS para fluidez impecável com consumo mínimo de CPU
        else:
            if self.timer.isActive():
                self.timer.stop()
        self.update()

    def _atualizar_animacao(self):
        janela = self.window()
        if estado.tema_atual not in self.TEMAS_ANIMADOS or estado.desativar_animacoes or (janela and janela.isMinimized()):
            self.timer.stop()
            return

        if estado.tema_atual == "Frutiger Aero":
            for b in self.bolhas:
                b["y"] -= b["velocidade"]
                b["fase"] += b["frequencia"]
                if b["y"] < -0.1:
                    b["y"] = 1.08
                    b["x"] = random.uniform(0.04, 0.96)
        elif estado.tema_atual == "Platinum Disc":
            self.angulo_platina = (self.angulo_platina + 0.5) % 360.0
            self.brilho_platina += 0.04
        elif estado.tema_atual in self.cenas:
            self.cenas[estado.tema_atual].avancar()

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if estado.tema_atual == "Frutiger Aero":
            # Gradiente Celeste Frutiger Aero (Azul Céu -> Ciano Aquático -> Verde Fresco)
            grad = QLinearGradient(0, 0, 0, self.height())
            grad.setColorAt(0.0, QColor("#1C8BF4"))   # Azul celeste
            grad.setColorAt(0.45, QColor("#56C8FF"))  # Ciano radiante
            grad.setColorAt(0.82, QColor("#B3F5CE"))  # Verde água límpido
            grad.setColorAt(1.0, QColor("#5DD64B"))   # Verde campestre vibrante
            painter.fillRect(self.rect(), grad)

            # Feixe de luz superior suave (efeito solar Frutiger Aero)
            luz = QRadialGradient(self.width() * 0.5, -self.height() * 0.2, self.width() * 0.75)
            luz.setColorAt(0.0, QColor(255, 255, 255, 95))
            luz.setColorAt(0.5, QColor(255, 255, 255, 25))
            luz.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillRect(self.rect(), luz)

            # Bolhas vítreas flutuantes com gradiente radial e reflexo especular
            w = self.width()
            h = self.height()
            for b in self.bolhas:
                bx = (b["x"] + math.sin(b["fase"]) * 0.018) * w
                by = b["y"] * h
                r = b["raio"]
                op = b["opacidade"]

                grad_bolha = QRadialGradient(bx - r * 0.3, by - r * 0.3, r * 1.3)
                grad_bolha.setColorAt(0.0, QColor(255, 255, 255, int(220 * op)))
                grad_bolha.setColorAt(0.35, QColor(255, 255, 255, int(50 * op)))
                grad_bolha.setColorAt(0.75, QColor(0, 210, 255, int(65 * op)))
                grad_bolha.setColorAt(1.0, QColor(255, 255, 255, int(140 * op)))

                painter.setPen(QPen(QColor(255, 255, 255, int(170 * op)), 1.2))
                painter.setBrush(QBrush(grad_bolha))
                painter.drawEllipse(QPointF(bx, by), r, r)

                # Ponto de reflexo superior vítreo
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, int(230 * op)))
                painter.drawEllipse(QPointF(bx - r * 0.35, by - r * 0.35), r * 0.22, r * 0.15)

        elif estado.tema_atual == "Platinum Disc":
            w = self.width()
            h = self.height()
            cx = w * 0.5
            cy = h * 0.52
            raio_disco = max(w, h) * 0.72

            # Base metálica: platina escura escovada profunda
            grad_base = QRadialGradient(cx, cy, raio_disco)
            grad_base.setColorAt(0.0, QColor("#2A313E"))
            grad_base.setColorAt(0.48, QColor("#1D222B"))
            grad_base.setColorAt(1.0, QColor("#13161C"))
            painter.fillRect(self.rect(), grad_base)

            # Reflexo anisotrópico rotativo (feixe de luz metálico em cruz/ampulheta)
            grad_conico = QConicalGradient(cx, cy, self.angulo_platina)
            c_luz1 = QColor(220, 235, 255, 42)
            c_luz2 = QColor(255, 255, 255, 65)
            c_sombra = QColor(10, 13, 18, 48)
            c_neutro = QColor(180, 200, 225, 14)

            grad_conico.setColorAt(0.0, c_neutro)
            grad_conico.setColorAt(0.12, c_luz1)
            grad_conico.setColorAt(0.18, c_luz2)
            grad_conico.setColorAt(0.24, c_luz1)
            grad_conico.setColorAt(0.35, c_sombra)
            grad_conico.setColorAt(0.50, c_neutro)
            grad_conico.setColorAt(0.62, c_luz1)
            grad_conico.setColorAt(0.68, c_luz2)
            grad_conico.setColorAt(0.74, c_luz1)
            grad_conico.setColorAt(0.85, c_sombra)
            grad_conico.setColorAt(1.0, c_neutro)
            painter.fillRect(self.rect(), grad_conico)

            # Sulcos circulares concêntricos do disco de platina (estilo vinil / mídia óptica)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            passos_anel = 9
            for i in range(1, passos_anel + 1):
                r = (raio_disco / passos_anel) * i
                op_linha = 18 if i % 2 == 0 else 34
                painter.setPen(QPen(QColor(215, 230, 252, op_linha), 1.0))
                painter.drawEllipse(QPointF(cx, cy), r, r)

            # Brilho especular sutil pulsante central (miolo do disco)
            pulso = (math.sin(self.brilho_platina) + 1.0) * 0.5
            r_centro = 50 + pulso * 6
            grad_centro = QRadialGradient(cx, cy, r_centro)
            grad_centro.setColorAt(0.0, QColor(255, 255, 255, int(50 + pulso * 25)))
            grad_centro.setColorAt(0.5, QColor(190, 215, 245, int(22 + pulso * 15)))
            grad_centro.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(grad_centro))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(cx, cy), r_centro, r_centro)

        elif estado.tema_atual in self.cenas:
            self.cenas[estado.tema_atual].desenhar(painter, self.width(), self.height())

        else:
            # Em outros temas, preenche com a cor sólida definida para a janela
            painter.fillRect(self.rect(), QColor(TEMAS[estado.tema_atual]["cor_fundo_janela"]))

        painter.end()
        super().paintEvent(event)