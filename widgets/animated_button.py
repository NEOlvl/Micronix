"""
Animated button widget
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtWidgets import QPushButton


class AnimatedButton(QPushButton):
    """Simple animated button without geometry changes"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._scale = 1.0

        # Анимация масштаба вместо геометрии
        self._scale_animation = QPropertyAnimation(self, b"scale")
        self._scale_animation.setDuration(100)
        self._scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = pyqtProperty(float, get_scale, set_scale)

    def enterEvent(self, event):
        self._scale_animation.setStartValue(1.0)
        self._scale_animation.setEndValue(1.05)  # Увеличение на 5%
        self._scale_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.0)
        self._scale_animation.start()
        super().leaveEvent(event)