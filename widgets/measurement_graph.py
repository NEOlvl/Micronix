"""
Measurement graph widget
"""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout


class MeasurementGraphWidget(QWidget):
    """Interactive measurement graph widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create plot widget
        self.plot_widget = pg.PlotWidget(background=None)
        self.plot_widget.setAntialiasing(True)

        # Установка темного фона для всего графика
        self.plot_widget.setBackground('#1a1b1e')  # Темный фон

        # Стиль осей
        styles = {'color': 'white', 'font-size': '12px'}
        self.plot_widget.setLabel('left', 'ДцБ', **styles)
        self.plot_widget.setLabel('bottom', 'Частота, ГГц', **styles)

        # Цвет линий сетки
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getPlotItem().getAxis('left').setPen(pg.mkPen(color=(255, 255, 255, 100)))
        self.plot_widget.getPlotItem().getAxis('bottom').setPen(pg.mkPen(color=(255, 255, 255, 100)))

        # Цвет текста на осях
        self.plot_widget.getPlotItem().getAxis('left').setTextPen('white')
        self.plot_widget.getPlotItem().getAxis('bottom').setTextPen('white')

        # Убираем рамку
        self.plot_widget.getPlotItem().getViewBox().setBorder(None)

        # Цвет линий сетки
        grid_pen = pg.mkPen(color=(255, 255, 255, 50), width=0.5)
        self.plot_widget.getPlotItem().getAxis('left').setGrid(255)
        self.plot_widget.getPlotItem().getAxis('bottom').setGrid(255)

        layout.addWidget(self.plot_widget)

    def plot_data(self, x_data, y_data, color='#7879F1', width=2, name=""):
        """Plot data with given style"""
        pen = pg.mkPen(color=color, width=width)
        return self.plot_widget.plot(x_data, y_data, pen=pen, name=name)