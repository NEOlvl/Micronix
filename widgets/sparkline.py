"""
Sparkline — лёгкий мини-график АЧХ для карточек измерений.

Рисуется QPainter'ом без pyqtgraph: десятки карточек не
создают тяжёлых PlotWidget. Фон прозрачный — виджет ставится
внутрь существующего контейнера #graphPreview, размеры
карточек не меняются.
"""

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QPen, QColor
from PyQt6.QtWidgets import QWidget


def _to_float(value):
    """Терпимый разбор числа/строки ('+8.0E+09' -> 8e9)."""
    try:
        return float(str(value).replace('E', 'e'))
    except (TypeError, ValueError):
        return None


class SparklineWidget(QWidget):
    """Миниатюрная кривая S21: линия + заливка + маркер резонанса."""

    def __init__(self, x=None, y=None, color='#7879F1', parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._points = []
        self._resonance = None  # (fx, fy) нормированные 0..1
        if x is not None and y is not None:
            self.set_data(x, y)

    def set_data(self, x, y):
        """Задать кривую (x в Гц, y в дБ). Нечисловые точки
        отбрасываются; пустые данные -> пустой виджет."""
        pairs = []
        for xv, yv in zip(x, y):
            fx, fy = _to_float(xv), _to_float(yv)
            if fx is not None and fy is not None:
                pairs.append((fx, fy))
        self._points = pairs
        self._resonance = None
        if pairs:
            # Резонанс — провал (notch) или пик (through):
            # маркируем экстремум с наибольшим отклонением от среднего
            mean_y = sum(p[1] for p in pairs) / len(pairs)
            dip = min(pairs, key=lambda p: p[1])
            peak = max(pairs, key=lambda p: p[1])
            target = (dip if (mean_y - dip[1]) >= (peak[1] - mean_y)
                      else peak)
            xmin = pairs[0][0]
            xmax = pairs[-1][0]
            span = xmax - xmin or 1.0
            self._resonance = ((target[0] - xmin) / span, target[1])
        self.update()

    def paintEvent(self, event):
        if len(self._points) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(6, 8, -6, -8)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        xs = [p[0] for p in self._points]
        ys = [p[1] for p in self._points]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        xspan = (xmax - xmin) or 1.0
        yspan = (ymax - ymin) or 1.0

        def to_px(fx, fy):
            return QPointF(
                rect.left() + (fx - xmin) / xspan * rect.width(),
                # небольшой запас по вертикали, чтобы экстремумы
                # не упирались в край
                rect.bottom() - (fy - ymin) / yspan * rect.height())

        path = QPainterPath()
        path.moveTo(to_px(*self._points[0]))
        for point in self._points[1:]:
            path.lineTo(to_px(*point))

        # Мягкая заливка под кривой
        fill = QPainterPath(path)
        fill.lineTo(to_px(self._points[-1][0], ymin))
        fill.lineTo(to_px(self._points[0][0], ymin))
        fill.closeSubpath()
        fill_color = QColor(self._color)
        fill_color.setAlpha(28)
        painter.fillPath(fill, fill_color)

        # Сама кривая
        pen = QPen(self._color)
        pen.setWidthF(1.6)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawPath(path)

        # Маркер резонанса
        if self._resonance is not None:
            fx_norm, fy = self._resonance
            fx = xmin + fx_norm * xspan
            center = to_px(fx, fy)
            dot = QColor(self._color).lighter(130)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(dot)
            painter.drawEllipse(center, 3.0, 3.0)
