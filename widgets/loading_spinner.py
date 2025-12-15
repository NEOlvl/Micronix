"""
Loading spinner widget
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QWidget


class LoadingSpinner(QWidget):
    """Loading spinner animation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update_rotation)
        self._timer.start(50)

    def update_rotation(self):
        self._angle = (self._angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        # Draw spinner arcs
        for i in range(8):
            alpha = 255 - (i * 32)
            painter.setBrush(QColor(120, 121, 241, alpha))
            painter.drawPie(5, 5, 30, 30, self._angle + (i * 45) * 16, 30 * 16)