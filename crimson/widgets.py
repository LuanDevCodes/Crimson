# Projeto Crimson - Widgets visuais personalizados (dropdown, barra de progresso, interruptor e fundo animado)
# Copyright (C) 2026 LuanDevCodes
# SPDX-License-Identifier: GPL-3.0-or-later

import random       # Usado para gerar posições e tamanhos aleatórios das bolhas Frutiger Aero
import math         # Usado para a oscilação senoidal das bolhas

from PySide6.QtWidgets import QWidget, QComboBox, QProgressBar, QPushButton, QStyledItemDelegate
from PySide6.QtCore import Qt, QPointF, QTimer, QRectF
from PySide6.QtGui import (
    QColor, QCursor, QPainter, QPen, QPainterPath, QLinearGradient, QRadialGradient, QConicalGradient, QBrush
)

from crimson.estado import estado
from crimson.temas import TEMAS

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

        if estado.tema_atual == "Frutiger Aero":
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
# --- Superfície de Fundo Dinâmica & Efeito Frutiger Aero ---
# --------------------------------------------------------------------------------------------------------------------

class WidgetFundoCrimson(QWidget):
    """
    Widget central com suporte a renderização dinâmica
    - 'Frutiger Aero': desenha gradiente celeste límpido, feixe solar e bolhas vítreas flutuantes
    - 'Platinum Disc': desenha uma superfície metálica de platina escovada com disco de sulcos concêntricos
      e reflexo anisotrópico em rotação contínua (estética vinil/CD de platina e cromo polido)
    - Outros temas: preenchimento estático suave poupando 100% de CPU
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bolhas = []
        self.angulo_platina = 0.0
        self.brilho_platina = 0.0
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
        if estado.tema_atual in ("Frutiger Aero", "Platinum Disc") and not estado.desativar_animacoes and not minimizada:
            if not self.timer.isActive():
                self.timer.start(40)  # ~25 FPS para fluidez impecável com consumo mínimo de CPU
        else:
            if self.timer.isActive():
                self.timer.stop()
        self.update()

    def _atualizar_animacao(self):
        janela = self.window()
        if estado.tema_atual not in ("Frutiger Aero", "Platinum Disc") or estado.desativar_animacoes or (janela and janela.isMinimized()):
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

        else:
            # Em outros temas, preenche com a cor sólida definida para a janela
            painter.fillRect(self.rect(), QColor(TEMAS[estado.tema_atual]["cor_fundo_janela"]))

        painter.end()
        super().paintEvent(event)