"""
Gradient background widget
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from PyQt6.QtWidgets import QWidget


class GradientBackground(QWidget):
    """Gradient background widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Устанавливаем атрибут для распространения фона на дочерние виджеты
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(34, 35, 38))
        gradient.setColorAt(1, QColor(25, 26, 29))

        painter.fillRect(self.rect(), gradient)