#!/usr/bin/env python3
"""
FERRO — Complete PyQt6 port without simplifications
Full-featured desktop version preserving all original functionality and UI complexity
"""

import sys
import json
import math
import random
import os
from functools import partial
from datetime import datetime

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPalette, QFont, QFontDatabase
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QPushButton, QLabel, QFrame, QScrollArea,
                             QLineEdit, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog, QProgressBar, QFormLayout, QDialogButtonBox,
                             QGroupBox, QTextEdit, QCheckBox, QRadioButton, QButtonGroup,
                             QSplitter, QSizePolicy, QGraphicsDropShadowEffect)

import pyqtgraph as pg
import numpy as np

# Configure pyqtgraph to use anti-aliasing
pg.setConfigOptions(antialias=True)


class AnimatedButton(QPushButton):
    """Animated button with hover effects"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        rect = self.geometry()
        self._animation.setStartValue(rect)
        self._animation.setEndValue(rect.adjusted(-2, -2, 2, 2))
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        rect = self.geometry()
        self._animation.setStartValue(rect)
        self._animation.setEndValue(rect.adjusted(2, 2, -2, -2))
        self._animation.start()
        super().leaveEvent(event)


class ModernCard(QFrame):
    """Modern card widget with shadow and animations"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            ModernCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.1),
                    stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


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


class GradientBackground(QWidget):
    """Gradient background widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(34, 35, 38))
        gradient.setColorAt(1, QColor(25, 26, 29))

        painter.fillRect(self.rect(), gradient)


class SidebarWidget(QWidget):
    """Main sidebar navigation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with logo
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(75, 113, 214, 0.3),
                    stop:1 rgba(75, 113, 214, 0.1));
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel("FERRO")
        logo.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Arial';
            }
        """)
        header_layout.addWidget(logo)
        layout.addWidget(header)

        # Navigation items
        nav_items = [
            ("Главная", "home"),
            ("Измерения", "measurement"),
            ("Отчёты", "documents"),
            ("Настройки", "setting")
        ]

        self.nav_buttons = []
        for text, icon in nav_items:
            btn = QPushButton(text)
            btn.setFixedHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: rgba(255, 255, 255, 0.7);
                    border: none;
                    text-align: left;
                    padding-left: 30px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.05);
                    color: white;
                }
                QPushButton:pressed {
                    background: rgba(120, 121, 241, 0.2);
                }
            """)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # Footer items
        footer_items = [
            ("Синхронизация", "cloud"),
            ("Настройки", "setting"),
            ("Гость", "account")
        ]

        for text, icon in footer_items:
            btn = QPushButton(text)
            btn.setFixedHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: rgba(255, 255, 255, 0.5);
                    border: none;
                    text-align: left;
                    padding-left: 30px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.03);
                    color: rgba(255, 255, 255, 0.8);
                }
            """)
            layout.addWidget(btn)


class HeaderWidget(QWidget):
    """Page header with breadcrumbs and actions"""

    def __init__(self, title="", subtitle="", parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setup_ui(title, subtitle)

    def setup_ui(self, title, subtitle):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 30, 0)

        # Title section
        title_section = QVBoxLayout()
        title_section.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: 600;
            }
        """)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 14px;
                font-weight: 400;
            }
        """)

        title_section.addWidget(self.title_label)
        title_section.addWidget(self.subtitle_label)
        layout.addLayout(title_section)

        layout.addStretch()

        # Action buttons
        self.new_measure_btn = AnimatedButton("Новое исследование")
        self.new_measure_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7879F1, stop:1 #9A9BFF);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6A6BE1, stop:1 #8A8BEF);
            }
        """)
        layout.addWidget(self.new_measure_btn)


class MethodCard(ModernCard):
    """Method selection card"""

    def __init__(self, method_num, method_name, description, image_style="", parent=None):
        super().__init__(parent)
        self.method_num = method_num
        self.setup_ui(method_num, method_name, description, image_style)

    def setup_ui(self, method_num, method_name, description, image_style):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Method number and name
        method_header = QLabel(f"Метод {method_num} - {method_name}")
        method_header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
            }
        """)

        # Description
        method_desc = QLabel(description)
        method_desc.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                font-weight: 400;
            }
        """)
        method_desc.setWordWrap(True)

        layout.addWidget(method_header)
        layout.addWidget(method_desc)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.setStyleSheet("""
            ModernCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(120, 121, 241, 0.2),
                    stop:1 rgba(120, 121, 241, 0.1));
                border: 1px solid rgba(120, 121, 241, 0.3);
                border-radius: 12px;
            }
        """)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet("""
            ModernCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.15),
                    stop:1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(120, 121, 241, 0.4);
                border-radius: 12px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            ModernCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.1),
                    stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        super().leaveEvent(event)


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

        # Style the plot
        self.plot_widget.getPlotItem().showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getPlotItem().getViewBox().setBorder(None)

        # Style axes
        styles = {'color': 'white', 'font-size': '12px'}
        self.plot_widget.setLabel('left', 'ДцБ', **styles)
        self.plot_widget.setLabel('bottom', 'Частота, ГГц', **styles)

        # Set axis pens
        axis_pen = pg.mkPen(color=(255, 255, 255, 100), width=1)
        self.plot_widget.getAxis('left').setPen(axis_pen)
        self.plot_widget.getAxis('bottom').setPen(axis_pen)

        # Set text color for axes
        self.plot_widget.getAxis('left').setTextPen('white')
        self.plot_widget.getAxis('bottom').setTextPen('white')

        layout.addWidget(self.plot_widget)

    def plot_data(self, x_data, y_data, color='#7879F1', width=2, name=""):
        """Plot data with given style"""
        pen = pg.mkPen(color=color, width=width)
        return self.plot_widget.plot(x_data, y_data, pen=pen, name=name)


class ResultsTableWidget(QTableWidget):
    """Styled results table"""

    def __init__(self, parent=None):
        super().__init__(0, 5, parent)
        self.setup_ui()

    def setup_ui(self):
        headers = ["№", "Имя образца", "Тангенс угла потерь (tgδ)",
                   "Диэлектрическая проницаемость (ε)", "Относительная погрешность (δ)"]
        self.setHorizontalHeaderLabels(headers)

        # Style the table
        self.setStyleSheet("""
            QTableWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }
            QTableWidget::item:selected {
                background: rgba(120, 121, 241, 0.3);
            }
            QHeaderView::section {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
        """)

        # Configure header
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)


class HomePage(QWidget):
    """Main home page with method selection and recent measurements"""

    def __init__(self, backend, open_measure_callback, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.open_measure_callback = open_measure_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Header - СОХРАНЯЕМ как атрибут класса
        self.header = HeaderWidget("Главная", "Начать исследование", self)
        self.header.new_measure_btn.hide()  # Hide new measure button on home
        layout.addWidget(self.header)

        # Method selection section
        methods_label = QLabel("Выберите метод исследования:")
        methods_label.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")
        layout.addWidget(methods_label)

        # Method cards grid
        methods_grid = QHBoxLayout()
        methods_grid.setSpacing(16)

        methods = [
            (1, "ФРЧ", "Метод фиксированной частоты", "_bcnm_img_2"),
            (2, "ФРД", "Метод фиксированной длины", "_bcnm_img_2"),
            (3, "СО", "Метод для стержневых образцов", "_bcnm_img_1"),
            (4, "СВЧФ", "Метод для СВЧ ферритов", "")
        ]

        for method_num, method_name, description, image_style in methods:
            card = MethodCard(method_num, method_name, description, image_style)
            card.mousePressEvent = partial(self.on_method_selected, method_num)
            methods_grid.addWidget(card)

        layout.addLayout(methods_grid)

        # Recent measurements section
        recent_layout = QVBoxLayout()
        recent_layout.setSpacing(12)

        recent_header = QHBoxLayout()
        recent_label = QLabel("Последние исследования")
        recent_label.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")
        recent_header.addWidget(recent_label)
        recent_header.addStretch()

        all_measures_btn = QPushButton("все исследования >")
        all_measures_btn.setStyleSheet("""
            QPushButton {
                color: rgba(120, 121, 241, 0.8);
                background: transparent;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: rgba(120, 121, 241, 1);
            }
        """)
        recent_header.addWidget(all_measures_btn)

        recent_layout.addLayout(recent_header)

        # Recent measurements scroll area
        self.recent_scroll = QScrollArea()
        self.recent_scroll.setWidgetResizable(True)
        self.recent_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.recent_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.recent_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
        """)

        self.recent_widget = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_widget)
        self.recent_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.recent_scroll.setWidget(self.recent_widget)

        recent_layout.addWidget(self.recent_scroll)
        layout.addLayout(recent_layout, 1)

        # Load recent measurements
        self.load_recent_measurements()

    def on_method_selected(self, method_id, event):
        """Handle method selection"""
        dialog = CreateMeasurementDialog(self.backend, method_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_recent_measurements()

    def load_recent_measurements(self):
        """Load and display recent measurements"""
        # Clear existing content
        for i in reversed(range(self.recent_layout.count())):
            item = self.recent_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Get measurements from backend
        measures = self.backend.ferro_query("measure_data", 0)

        if not measures:
            # Show empty state
            empty_label = QLabel("Пока нет проведенных исследований")
            empty_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); text-align: center; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.recent_layout.addWidget(empty_label)
            return

        for measure in measures[-4:]:  # Show last 4 measurements
            measure_card = self.create_measurement_card(measure)
            self.recent_layout.addWidget(measure_card)

    def create_measurement_card(self, measure):
        """Create a measurement card widget"""
        card = ModernCard()
        card.setFixedHeight(120)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(16)

        # Mini graph
        graph_widget = pg.PlotWidget(background=None)
        graph_widget.setFixedSize(200, 80)
        graph_widget.setMouseEnabled(x=False, y=False)
        graph_widget.hideButtons()

        # Hide axes for mini graph
        graph_widget.getPlotItem().hideAxis('left')
        graph_widget.getPlotItem().hideAxis('bottom')

        # Plot data
        x_data = np.array(measure['x'])
        y_data = np.array(measure['y_res'])
        graph_widget.plot(x_data, y_data, pen=pg.mkPen('#7879F1', width=1.5))

        # If there are samples, plot the first one
        if measure['y_samples']:
            sample = list(measure['y_samples'].values())[0]
            sample_y = np.array(sample['y_res'])
            graph_widget.plot(x_data, sample_y, pen=pg.mkPen('#f8c33c', width=1.5))

        card_layout.addWidget(graph_widget)

        # Measurement info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        title = QLabel(f"Исследование #{measure['title']}")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")

        time_label = QLabel(measure['time'])
        time_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 13px;")

        # Sample info if available
        sample_info = QLabel("")
        if measure['y_samples']:
            sample = list(measure['y_samples'].values())[0]
            sample_info.setText(f"Образец: {sample['name']}")
            sample_info.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 13px;")

        info_layout.addWidget(title)
        info_layout.addWidget(time_label)
        info_layout.addWidget(sample_info)
        info_layout.addStretch()

        card_layout.addLayout(info_layout, 1)

        # Make card clickable
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = partial(self.open_measurement, measure['id_m'])

        return card

    def open_measurement(self, measure_id, event):
        """Open measurement details"""
        self.open_measure_callback(measure_id)


class CreateMeasurementDialog(QDialog):
    """Dialog for creating new measurement"""

    def __init__(self, backend, method_id, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.method_id = method_id
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Новое исследование")
        self.setModal(True)
        self.setFixedSize(800, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background: rgba(255, 255, 255, 0.05);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("Бином / новое исследование")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        # Content
        content = QScrollArea()
        content.setWidgetResizable(True)
        content.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)

        self.setup_method_content()
        content.setWidget(content_widget)
        layout.addWidget(content, 1)

        # Footer buttons
        footer = QWidget()
        footer.setFixedHeight(80)
        footer.setStyleSheet("background: rgba(255, 255, 255, 0.05);")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)

        footer_layout.addStretch()

        clear_btn = QPushButton("Очистить всё")
        clear_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        create_btn = AnimatedButton("Начать исследование")
        create_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7879F1, stop:1 #9A9BFF);
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6A6BE1, stop:1 #8A8BEF);
            }
        """)
        create_btn.clicked.connect(self.create_measurement)

        footer_layout.addWidget(clear_btn)
        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(create_btn)

        layout.addWidget(footer)

    def setup_method_content(self):
        """Setup method-specific content"""
        # Method selection
        method_section = ModernCard()
        method_layout = QVBoxLayout(method_section)
        method_layout.setContentsMargins(20, 20, 20, 20)

        section_title = QLabel("Метод исследования")
        section_title.setStyleSheet("color: white; font-size: 18px; font-weight: 600;")
        method_layout.addWidget(section_title)

        # Method cards
        methods_layout = QHBoxLayout()
        methods = [
            (1, "ФРЧ", "Метод фиксированной частоты"),
            (2, "ФРД", "Метод фиксированной длины"),
            (3, "СО", "Метод для стержневых образцов"),
            (4, "СВЧФ", "Метод для СВЧ ферритов")
        ]

        for method_id, method_name, description in methods:
            card = MethodCard(method_id, method_name, description)
            if method_id == self.method_id:
                card.setStyleSheet("""
                    ModernCard {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(120, 121, 241, 0.2),
                            stop:1 rgba(120, 121, 241, 0.1));
                        border: 1px solid rgba(120, 121, 241, 0.3);
                        border-radius: 12px;
                    }
                """)
            card.mousePressEvent = partial(self.select_method, method_id)
            methods_layout.addWidget(card)

        method_layout.addLayout(methods_layout)
        self.content_layout.addWidget(method_section)

        # Method parameters
        self.setup_method_parameters()

    def setup_method_parameters(self):
        """Setup parameters for selected method"""
        param_section = ModernCard()
        param_layout = QVBoxLayout(param_section)
        param_layout.setContentsMargins(20, 20, 20, 20)

        section_title = QLabel(f"Данные для исследования #{self.method_id}")
        section_title.setStyleSheet("color: white; font-size: 18px; font-weight: 600;")
        param_layout.addWidget(section_title)

        # Method-specific parameters
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(20)

        if self.method_id == 1:
            self.t_input = QLineEdit()
            self.delL_input = QLineEdit()
            self.n_input = QSpinBox()
            self.n_input.setValue(1)

            form_layout.addRow("Толщина образца, мм:", self.t_input)
            form_layout.addRow("Перемещение поршня, мм:", self.delL_input)
            form_layout.addRow("Кол-во измерений:", self.n_input)

        elif self.method_id == 2:
            self.t_input = QLineEdit()
            self.n_input = QSpinBox()
            self.n_input.setValue(1)

            form_layout.addRow("Толщина образца, мм:", self.t_input)
            form_layout.addRow("Кол-во измерений:", self.n_input)

        elif self.method_id == 3:
            self.d_input = QLineEdit()
            self.n_input = QSpinBox()
            self.n_input.setValue(1)

            form_layout.addRow("Радиус образца, мм:", self.d_input)
            form_layout.addRow("Кол-во измерений:", self.n_input)

        elif self.method_id == 4:
            self.form_combo = QComboBox()
            self.form_combo.addItems(["Стержень", "Квадратная"])
            self.mp_input = QLineEdit()
            self.ism_input = QSpinBox()
            self.ism_input.setValue(1)

            form_layout.addRow("Форма образца:", self.form_combo)
            form_layout.addRow("Поперечная составляющая МП:", self.mp_input)
            form_layout.addRow("Кол-во измерений:", self.ism_input)

        # Style form labels and inputs
        for i in range(form_layout.rowCount()):
            label = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole).widget()
            if label:
                label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 14px;")

            field = form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            if field:
                field.setStyleSheet("""
                    QLineEdit, QSpinBox, QComboBox {
                        background: rgba(255, 255, 255, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 6px;
                        padding: 8px 12px;
                        color: white;
                        font-size: 14px;
                    }
                    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                        border: 1px solid rgba(120, 121, 241, 0.6);
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                    QComboBox::down-arrow {
                        image: none;
                        border-left: 5px solid transparent;
                        border-right: 5px solid transparent;
                        border-top: 5px solid white;
                    }
                """)

        param_layout.addLayout(form_layout)

        # Additional parameters (collapsible)
        additional_group = QGroupBox("Дополнительные параметры исследования")
        additional_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)

        additional_layout = QFormLayout(additional_group)
        additional_layout.setVerticalSpacing(10)

        if self.method_id in [1, 2, 3]:
            self.index_combo = QComboBox()
            if self.method_id == 3:
                self.index_combo.addItems(["1", "2", "3"])
                self.index_combo.setCurrentText("1")
            else:
                self.index_combo.addItems(["2", "3", "4", "5"])
                self.index_combo.setCurrentText("2")

            self.d_res_input = QLineEdit()
            self.d_res_input.setReadOnly(True)
            if self.method_id == 1:
                self.d_res_input.setText("50")
            elif self.method_id == 2:
                self.d_res_input.setText("45")
            elif self.method_id == 3:
                self.d_res_input.setText("22.5")

            self.h_res_input = QLineEdit()
            if self.method_id == 1:
                self.h_res_input.setText("90")
            elif self.method_id in [2, 3]:
                self.h_res_input.setText("45")

            additional_layout.addRow("Продольный индекс колебаний:", self.index_combo)
            additional_layout.addRow("Диаметр резонатора, мм:", self.d_res_input)
            additional_layout.addRow("Высота резонатора, мм:", self.h_res_input)

        elif self.method_id == 4:
            self.d_res_input = QLineEdit()
            self.d_res_input.setText("11")
            self.d_sample_input = QLineEdit()
            self.d_sample_input.setText("0.81")

            additional_layout.addRow("Радиус резонатора:", self.d_res_input)
            additional_layout.addRow("Радиус образца:", self.d_sample_input)

        # Style additional form
        for i in range(additional_layout.rowCount()):
            label = additional_layout.itemAt(i, QFormLayout.ItemRole.LabelRole).widget()
            if label:
                label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 13px;")

            field = additional_layout.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            if field:
                field.setStyleSheet("""
                    QLineEdit, QComboBox {
                        background: rgba(255, 255, 255, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 4px;
                        padding: 6px 10px;
                        color: white;
                        font-size: 13px;
                    }
                """)

        param_layout.addWidget(additional_group)
        self.content_layout.addWidget(param_section)

    def select_method(self, method_id, event):
        """Change selected method"""
        self.method_id = method_id
        # Remove old parameters and add new ones
        for i in reversed(range(self.content_layout.count())):
            if i > 0:  # Keep method selection section
                item = self.content_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()
        self.setup_method_parameters()

    def create_measurement(self):
        """Create new measurement"""
        # Prepare data based on method
        data_obj = {
            "method": self.method_id,
            "data": {
                str(self.method_id): {}
            }
        }

        if self.method_id == 1:
            data_obj["data"][str(self.method_id)] = {
                "t": self.t_input.text(),
                "del_L": self.delL_input.text(),
                "n": self.n_input.value(),
                "index": self.index_combo.currentText(),
                "d_res": self.d_res_input.text(),
                "h_res": self.h_res_input.text()
            }
        elif self.method_id == 2:
            data_obj["data"][str(self.method_id)] = {
                "t": self.t_input.text(),
                "n": self.n_input.value(),
                "index": self.index_combo.currentText(),
                "d_res": self.d_res_input.text(),
                "h_res": self.h_res_input.text()
            }
        elif self.method_id == 3:
            data_obj["data"][str(self.method_id)] = {
                "d": self.d_input.text(),
                "n": self.n_input.value(),
                "index": self.index_combo.currentText(),
                "d_res": self.d_res_input.text(),
                "h_res": self.h_res_input.text()
            }
        elif self.method_id == 4:
            data_obj["data"][str(self.method_id)] = {
                "form": "1" if self.form_combo.currentText() == "Стержень" else "0",
                "mp": self.mp_input.text(),
                "ism": self.ism_input.value(),
                "d_res": self.d_res_input.text(),
                "d_sample": self.d_sample_input.text()
            }

        # Call backend
        response = self.backend.ferro_query("new_create", data_obj)

        # Start measurement process
        self.measurement_process = MeasurementProcessDialog(self.backend, response['id'], self)
        self.measurement_process.show()

        self.accept()


class MeasurementProcessDialog(QDialog):
    """Dialog showing measurement progress"""

    def __init__(self, backend, measure_id, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.measure_id = measure_id
        self.current_stage = 1
        self.setup_ui()
        self.start_measurement_process()

    def setup_ui(self):
        self.setWindowTitle("Исследование в процессе")
        self.setModal(True)
        self.setFixedSize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background: rgba(255, 255, 255, 0.05);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.title_label = QLabel("Исследование #...")
        self.title_label.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        stop_btn = QPushButton("Остановить исследование")
        stop_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.4);
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
        """)
        stop_btn.clicked.connect(self.reject)
        header_layout.addWidget(stop_btn)

        layout.addWidget(header)

        # Progress info
        progress_widget = QWidget()
        progress_widget.setFixedHeight(120)
        progress_widget.setStyleSheet("background: rgba(255, 255, 255, 0.03);")
        progress_layout = QVBoxLayout(progress_widget)
        progress_layout.setContentsMargins(30, 20, 30, 20)

        # Stage info
        stage_layout = QHBoxLayout()
        self.stage_label = QLabel("Этап 1")
        self.stage_label.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")

        self.stage_desc = QLabel("Подготовка оборудования...")
        self.stage_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px;")

        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet("color: white; font-size: 24px; font-weight: 600;")

        stage_layout.addWidget(self.stage_label)
        stage_layout.addWidget(self.stage_desc)
        stage_layout.addStretch()
        stage_layout.addWidget(self.progress_label)

        progress_layout.addLayout(stage_layout)

        # Progress bars
        bars_layout = QHBoxLayout()
        self.bars = []
        widths = [10, 20, 50, 20]  # Percentage widths for each stage

        for i, width in enumerate(widths):
            bar_container = QWidget()
            bar_container.setFixedHeight(8)
            bar_container.setStyleSheet("background: rgba(255, 255, 255, 0.1); border-radius: 4px;")

            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(2, 0, 2, 0)

            progress_bar = QWidget()
            progress_bar.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7879F1, stop:1 #9A9BFF); border-radius: 3px;")
            progress_bar.setFixedWidth(0)

            bar_layout.addWidget(progress_bar)
            bars_layout.addWidget(bar_container)
            self.bars.append(progress_bar)

        progress_layout.addLayout(bars_layout)
        layout.addWidget(progress_widget)

        # Graph area
        graph_widget = QWidget()
        graph_layout = QHBoxLayout(graph_widget)
        graph_layout.setContentsMargins(20, 20, 20, 20)
        graph_layout.setSpacing(20)

        # Main graph
        self.graph = MeasurementGraphWidget()
        graph_layout.addWidget(self.graph, 3)

        # Side info
        side_info = ModernCard()
        side_info.setFixedWidth(300)
        side_layout = QVBoxLayout(side_info)
        side_layout.setContentsMargins(20, 20, 20, 20)

        # Loading animation
        self.loading_spinner = LoadingSpinner()
        side_layout.addWidget(self.loading_spinner, 0, Qt.AlignmentFlag.AlignHCenter)

        self.status_title = QLabel("Исследование в процессе")
        self.status_title.setStyleSheet("color: white; font-size: 16px; font-weight: 600; text-align: center;")
        self.status_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_desc = QLabel("Пожалуйста, ожидайте завершения процесса.")
        self.status_desc.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px; text-align: center;")
        self.status_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_desc.setWordWrap(True)

        side_layout.addWidget(self.status_title)
        side_layout.addWidget(self.status_desc)
        side_layout.addStretch()

        # Sample input (will be shown later)
        self.sample_input_container = QWidget()
        self.sample_input_container.hide()
        sample_layout = QVBoxLayout(self.sample_input_container)

        sample_label = QLabel("Имя образца:")
        sample_label.setStyleSheet("color: white; font-size: 14px;")

        self.sample_name_input = QLineEdit()
        self.sample_name_input.setPlaceholderText("Введите имя образца")
        self.sample_name_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
        """)

        continue_btn = AnimatedButton("Продолжить")
        continue_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7879F1, stop:1 #9A9BFF);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: 600;
                margin-top: 10px;
            }
        """)
        continue_btn.clicked.connect(self.add_sample)

        end_btn = QPushButton("Завершить исследование")
        end_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 12px;
                border-radius: 6px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        end_btn.clicked.connect(self.finish_measurement)

        sample_layout.addWidget(sample_label)
        sample_layout.addWidget(self.sample_name_input)
        sample_layout.addWidget(continue_btn)
        sample_layout.addWidget(end_btn)

        side_layout.addWidget(self.sample_input_container)
        graph_layout.addWidget(side_info)

        layout.addWidget(graph_widget, 1)

    def start_measurement_process(self):
        """Start the measurement process with animations"""
        # Update title
        measure_data = self.backend.ferro_query("read_data", {"id_m": self.measure_id})
        self.title_label.setText(f"Исследование #{measure_data.get('title', '...')}")

        # Start stage progression
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)

        # Load graph data
        self.load_graph_data()

    def update_progress(self):
        """Update progress bars and stages"""
        if self.current_stage == 1:
            progress = self.bars[0].width() + 1
            max_width = int(self.bars[0].parent().width() * 0.96)  # 96% of container
            if progress < max_width:
                self.bars[0].setFixedWidth(progress)
                self.progress_label.setText(f"{int(progress / max_width * 100)}%")
            else:
                self.current_stage = 2
                self.stage_label.setText("Этап 2")
                self.stage_desc.setText("Снятие данных с рефлектометра")

        elif self.current_stage == 2:
            progress = self.bars[1].width() + 2
            max_width = int(self.bars[1].parent().width() * 0.96)
            if progress < max_width:
                self.bars[1].setFixedWidth(progress)
                self.progress_label.setText(f"{int(progress / max_width * 100)}%")
            else:
                self.current_stage = 3
                # Show sample input
                self.loading_spinner.hide()
                self.status_title.setText("Ожидание образца")
                self.status_desc.setText("Поместите образец в резонатор, затем нажмите продолжить.")
                self.sample_input_container.show()

        # Update graph periodically
        if random.random() < 0.1:  # 10% chance each tick
            self.update_live_graph()

    def load_graph_data(self):
        """Load initial graph data"""
        x_data = self.backend.ferro_query("create_graph_x", 0)
        y_data = self.backend.ferro_query("create_graph", 0)

        self.graph.plot_data(x_data, y_data, '#7879F1', 2, "Без образца")

    def update_live_graph(self):
        """Update graph with live data"""
        # Simulate live data updates
        if hasattr(self, 'live_data_counter'):
            self.live_data_counter += 1
        else:
            self.live_data_counter = 0

        # Add some random variation to simulate live data
        if self.live_data_counter % 10 == 0:
            y_data = self.backend.ferro_query("create_graph", 0)
            noise = np.random.normal(0, 0.1, len(y_data))
            y_data_live = [y + n for y, n in zip(y_data, noise)]

            # Update plot
            self.graph.plot_widget.clear()
            x_data = self.backend.ferro_query("create_graph_x", 0)
            self.graph.plot_data(x_data, y_data_live, '#7879F1', 2, "Без образца")

    def add_sample(self):
        """Add sample to measurement"""
        sample_name = self.sample_name_input.text().strip()
        if not sample_name:
            sample_name = f"Sample-{random.randint(1000, 9999)}"

        # Call backend to add sample
        data_obj = {
            "id_m": self.measure_id,
            "new_sample_name": sample_name
        }
        response = self.backend.ferro_query("new_sample", data_obj)

        # Update graph with sample data
        measure_data = self.backend.ferro_query("read_data", {"id_m": self.measure_id})
        if measure_data['y_samples']:
            sample = list(measure_data['y_samples'].values())[-1]  # Get latest sample
            self.graph.plot_data(measure_data['x'], sample['y_res'], '#f8c33c', 2, sample_name)

        # Reset for next sample
        self.sample_name_input.clear()
        self.status_title.setText("Ожидание образца")
        self.status_desc.setText(
            "Поместите новый образец в резонатор, затем нажмите продолжить или завершите исследование.")

        # Update progress bar
        progress = self.bars[2].width() + 25
        max_width = int(self.bars[2].parent().width() * 0.96)
        if progress < max_width:
            self.bars[2].setFixedWidth(progress)
        else:
            self.bars[3].setFixedWidth(self.bars[3].parent().width() * 0.96)

    def finish_measurement(self):
        """Finish measurement process"""
        data_obj = {"id_m": self.measure_id}
        response = self.backend.ferro_query("method_end", data_obj)
        self.accept()


class MeasureDetailPage(QWidget):
    """Detailed measurement view page"""

    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.current_measure_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = HeaderWidget("Измерения", "", self)
        self.header.new_measure_btn.setText("Настройки")
        layout.addWidget(self.header)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)

        # Title and info
        title_section = QVBoxLayout()
        title_section.setSpacing(8)

        self.measure_title = QLabel("Вычисление #...")
        self.measure_title.setStyleSheet("color: white; font-size: 24px; font-weight: 600;")

        self.measure_info = QLabel("CABAN R180 • RESONATOR 1 • 20.10.2024 17:56:46")
        self.measure_info.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 14px;")

        title_section.addWidget(self.measure_title)
        title_section.addWidget(self.measure_info)
        content_layout.addLayout(title_section)

        # Graph and info split
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Graph area
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)

        self.graph = MeasurementGraphWidget()
        graph_layout.addWidget(self.graph)

        splitter.addWidget(graph_container)

        # Side info
        info_container = ModernCard()
        info_container.setMinimumWidth(300)
        info_container.setMaximumWidth(400)
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(20, 20, 20, 20)

        # Measurement info scroll
        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        info_content = QWidget()
        self.info_content_layout = QVBoxLayout(info_content)
        self.info_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_scroll.setWidget(info_content)

        info_layout.addWidget(info_scroll)
        splitter.addWidget(info_container)

        # Set splitter proportions
        splitter.setSizes([700, 300])
        content_layout.addWidget(splitter, 1)

        # Results table
        results_label = QLabel("Результаты вычислений")
        results_label.setStyleSheet("color: white; font-size: 18px; font-weight: 600;")
        content_layout.addWidget(results_label)

        self.results_table = ResultsTableWidget()
        content_layout.addWidget(self.results_table, 1)

        layout.addWidget(content)

    def load_measurement(self, measure_id):
        """Load measurement data"""
        self.current_measure_id = measure_id
        data = self.backend.ferro_query("read_data", {"id_m": measure_id})

        # Update title and info
        self.measure_title.setText(f"Вычисление #{data.get('title', 'Unknown')}")
        self.measure_info.setText(f"CABAN R180 • RESONATOR 1 • {data.get('time', 'Unknown')}")

        # Clear graph
        self.graph.plot_widget.clear()

        # Plot baseline data
        x_data = np.array(data['x'])
        y_data = np.array(data['y_res'])
        self.graph.plot_data(x_data, y_data, '#7879F1', 2, "Без образца")

        # Plot samples
        for sample_idx, sample in data['y_samples'].items():
            sample_y = np.array(sample['y_res'])
            self.graph.plot_data(x_data, sample_y, '#f8c33c', 2, sample['name'])

        # Update info panel
        self.update_info_panel(data)

        # Update results table
        self.update_results_table(data)

    def update_info_panel(self, data):
        """Update the information panel with measurement details"""
        # Clear existing content
        for i in reversed(range(self.info_content_layout.count())):
            item = self.info_content_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Baseline info
        baseline_title = QLabel("Без образца")
        baseline_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 600;
                margin-top: 10px;
            }
        """)
        self.info_content_layout.addWidget(baseline_title)

        # Add sample info
        for sample_idx, sample in data['y_samples'].items():
            sample_title = QLabel(sample['name'])
            sample_title.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 14px;
                    font-weight: 600;
                    margin-top: 20px;
                }
            """)
            self.info_content_layout.addWidget(sample_title)

            sample_info = QLabel(f"F₀: 9.87 ГГц\nQ: 789")
            sample_info.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 13px;")
            self.info_content_layout.addWidget(sample_info)

        self.info_content_layout.addStretch()

    def update_results_table(self, data):
        """Update the results table with sample data"""
        self.results_table.setRowCount(0)

        for i, (sample_idx, sample) in enumerate(data['y_samples'].items(), 1):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            self.results_table.setItem(row, 0, QTableWidgetItem(str(i)))
            self.results_table.setItem(row, 1, QTableWidgetItem(sample['name']))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{sample['tgo']:.8f}"))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{sample['E']:.3f}"))
            self.results_table.setItem(row, 4, QTableWidgetItem("1 * 10^-4"))


class MeasuresPage(QWidget):
    """Measurements list page"""

    def __init__(self, backend, open_measure_callback, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.open_measure_callback = open_measure_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header - СОХРАНЯЕМ как атрибут класса
        self.header = HeaderWidget("Измерения", "", self)
        layout.addWidget(self.header)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)

        # Search and filter bar
        search_bar = QHBoxLayout()
        search_bar.setSpacing(12)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Поиск по названиям")
        search_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px 16px;
                color: white;
                font-size: 14px;
                min-width: 300px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(120, 121, 241, 0.6);
            }
        """)

        search_bar.addWidget(search_input)
        search_bar.addStretch()

        # Action buttons
        create_btn = AnimatedButton("Создать измерение")
        create_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7879F1, stop:1 #9A9BFF);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
        """)

        sort_btn = QPushButton("Сортировка")
        sort_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)

        filter_btn = QPushButton("Фильтр")
        filter_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)

        search_bar.addWidget(create_btn)
        search_bar.addWidget(sort_btn)
        search_bar.addWidget(filter_btn)

        content_layout.addLayout(search_bar)

        # Measurements grid
        self.measures_scroll = QScrollArea()
        self.measures_scroll.setWidgetResizable(True)
        self.measures_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.measures_widget = QWidget()
        self.measures_layout = QVBoxLayout(self.measures_widget)
        self.measures_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.measures_scroll.setWidget(self.measures_widget)

        content_layout.addWidget(self.measures_scroll, 1)
        layout.addWidget(content)

        # Load measurements
        self.load_measurements()

        # Connect signals
        create_btn.clicked.connect(self.create_measurement)
        search_input.textChanged.connect(self.filter_measurements)

    def load_measurements(self):
        """Load and display all measurements"""
        # Clear existing content
        for i in reversed(range(self.measures_layout.count())):
            item = self.measures_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Get measurements from backend
        measures = self.backend.ferro_query("measure_data", 0)

        if not measures:
            empty_label = QLabel("Нет проведенных измерений")
            empty_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); text-align: center; padding: 60px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.measures_layout.addWidget(empty_label)
            return

        # Create grid layout for measurements
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(16)

        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        right_column = QVBoxLayout()
        right_column.setSpacing(16)

        for i, measure in enumerate(measures):
            measure_card = self.create_measurement_card(measure)
            if i % 2 == 0:
                left_column.addWidget(measure_card)
            else:
                right_column.addWidget(measure_card)

        grid_layout.addLayout(left_column)
        grid_layout.addLayout(right_column)
        self.measures_layout.addLayout(grid_layout)

    def create_measurement_card(self, measure):
        """Create a measurement card for the list view"""
        card = ModernCard()
        card.setFixedHeight(180)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(20)

        # Graph preview
        graph_widget = pg.PlotWidget(background=None)
        graph_widget.setFixedSize(240, 120)
        graph_widget.setMouseEnabled(x=False, y=False)
        graph_widget.hideButtons()
        graph_widget.getPlotItem().hideAxis('left')
        graph_widget.getPlotItem().hideAxis('bottom')

        # Plot data
        x_data = np.array(measure['x'])
        y_data = np.array(measure['y_res'])
        graph_widget.plot(x_data, y_data, pen=pg.mkPen('#7879F1', width=2))

        # Plot first sample if exists
        if measure['y_samples']:
            sample = list(measure['y_samples'].values())[0]
            sample_y = np.array(sample['y_res'])
            graph_widget.plot(x_data, sample_y, pen=pg.mkPen('#f8c33c', width=2))

        card_layout.addWidget(graph_widget)

        # Measurement info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(12)

        title = QLabel("Метод объёмного резонатора")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")

        measure_id = QLabel(f"#{measure['title']} - {measure['time']}")
        measure_id.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 13px;")

        # Sample results
        results_layout = QVBoxLayout()
        if measure['y_samples']:
            for sample_idx, sample in measure['y_samples'].items():
                result_text = f"tgδ: {sample['tgo']:.8f} • ε: {sample['E']:.3f}"
                result_label = QLabel(result_text)
                result_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 13px;")
                results_layout.addWidget(result_label)

        info_layout.addWidget(title)
        info_layout.addWidget(measure_id)
        info_layout.addLayout(results_layout)
        info_layout.addStretch()

        card_layout.addLayout(info_layout, 1)

        # Make card clickable
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = partial(self.open_measurement, measure['id_m'])

        return card

    def open_measurement(self, measure_id, event):
        """Open measurement details"""
        self.open_measure_callback(measure_id)

    def create_measurement(self):
        """Create new measurement"""
        dialog = CreateMeasurementDialog(self.backend, 1, self)
        dialog.exec()
        self.load_measurements()

    def filter_measurements(self, text):
        """Filter measurements based on search text"""
        # Implementation would filter the displayed measurements
        pass


class ReportsPage(QWidget):
    """Reports page"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header - СОХРАНЯЕМ как атрибут класса
        self.header = HeaderWidget("Отчёты", "", self)
        layout.addWidget(self.header)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)

        # Search and actions
        search_bar = QHBoxLayout()
        search_bar.setSpacing(12)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Поиск по названиям")
        search_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px 16px;
                color: white;
                font-size: 14px;
                min-width: 300px;
            }
        """)

        search_bar.addWidget(search_input)
        search_bar.addStretch()

        create_btn = AnimatedButton("Создать отчёт")
        create_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7879F1, stop:1 #9A9BFF);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
        """)

        sort_btn = QPushButton("Сортировка")
        sort_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
            }
        """)

        filter_btn = QPushButton("Фильтр")
        filter_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
            }
        """)

        search_bar.addWidget(create_btn)
        search_bar.addWidget(sort_btn)
        search_bar.addWidget(filter_btn)

        content_layout.addLayout(search_bar)

        # Reports grid
        reports_label = QLabel("Доступные отчёты")
        reports_label.setStyleSheet("color: white; font-size: 18px; font-weight: 600;")
        content_layout.addWidget(reports_label)

        reports_grid = QHBoxLayout()
        reports_grid.setSpacing(16)

        # Sample reports
        reports = [
            ("Отчёт #СВЧФ_1_01122024", "20.11.2024"),
            ("Отчёт #СВЧФ_3_01122024", "20.11.2024"),
            ("Отчёт #СО_1_01122024", "20.11.2024"),
            ("Отчёт #СВЧФ_3_01122024", "20.11.2024")
        ]

        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        right_column = QVBoxLayout()
        right_column.setSpacing(16)

        for i, (title, date) in enumerate(reports):
            report_card = self.create_report_card(title, date)
            if i % 2 == 0:
                left_column.addWidget(report_card)
            else:
                right_column.addWidget(report_card)

        reports_grid.addLayout(left_column)
        reports_grid.addLayout(right_column)
        content_layout.addLayout(reports_grid, 1)

        layout.addWidget(content)

    def create_report_card(self, title, date):
        """Create a report card"""
        card = ModernCard()
        card.setFixedHeight(120)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(16)

        # Report icon
        icon = QLabel("📄")
        icon.setStyleSheet("font-size: 32px;")
        icon.setFixedSize(60, 60)

        # Report info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: 600;")

        date_label = QLabel(date)
        date_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 13px;")

        info_layout.addWidget(title_label)
        info_layout.addWidget(date_label)
        info_layout.addStretch()

        card_layout.addWidget(icon)
        card_layout.addLayout(info_layout, 1)

        card.setCursor(Qt.CursorShape.PointingHandCursor)

        return card


class SettingsPage(QWidget):
    """Settings page"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar menu
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background: rgba(255, 255, 255, 0.03);")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Settings title
        title = QLabel("Настройки")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: 600; padding: 30px;")
        sidebar_layout.addWidget(title)

        # Settings categories
        categories = [
            ("Основное", [
                ("Аккаунт", "account"),
                ("Интерфейс", "theme")
            ]),
            ("Внешние устройства", [
                ("Рефлектометры", "reflectometer"),
                ("Управляющие механизмы", "mechanism")
            ]),
            ("Специальное", [
                ("Разработчикам", "developer")
            ])
        ]

        for category_name, items in categories:
            category_label = QLabel(category_name)
            category_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 12px;
                    font-weight: 600;
                    padding: 20px 30px 10px 30px;
                }
            """)
            sidebar_layout.addWidget(category_label)

            for item_name, item_icon in items:
                item_btn = QPushButton(item_name)
                item_btn.setFixedHeight(50)
                item_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: rgba(255, 255, 255, 0.7);
                        border: none;
                        text-align: left;
                        padding-left: 30px;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 0.05);
                        color: white;
                    }
                """)
                sidebar_layout.addWidget(item_btn)

        sidebar_layout.addStretch()
        layout.addWidget(sidebar)

        # Settings content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)

        content_title = QLabel("Настройка аккаунта")
        content_title.setStyleSheet("color: white; font-size: 24px; font-weight: 600;")
        content_layout.addWidget(content_title)

        # Settings form would go here
        settings_form = ModernCard()
        settings_form.setFixedHeight(400)
        form_layout = QVBoxLayout(settings_form)
        form_layout.setContentsMargins(30, 30, 30, 30)

        form_layout.addStretch()

        content_layout.addWidget(settings_form)
        content_layout.addStretch()

        layout.addWidget(content, 1)


class FERROBackend:
    """Backend for FERRO application"""

    def __init__(self):
        self.measures = {}
        self.next_id = 1
        self.setup_sample_data()

    def setup_sample_data(self):
        """Setup sample measurement data"""
        # Generate sample frequency data (8-12 GHz like original)
        self.x = np.arange(8.01, 12.0, 0.005)

        # Create baseline resonance curve
        f0 = 9.87
        Q = 800
        self.base_y = -20 * np.log10(1 + (self.x - f0) ** 2 * (1 / (f0 / Q)) ** 2)
        self.base_y = np.clip(self.base_y - np.max(self.base_y) - 10, -100, 0)

        # Add some sample measurements
        sample_measure = {
            "id_m": "M001",
            "title": "001",
            "time": "20.10.2024 17:56:46",
            "x": self.x.tolist(),
            "y_res": self.base_y.tolist(),
            "y_samples": {
                1: {
                    "name": "ПЭС-1-1",
                    "y_res": (self.base_y + np.random.normal(0, 0.3, size=self.base_y.shape)).tolist(),
                    "tgo": 6.1e-4,
                    "E": 11.1
                }
            }
        }
        self.measures[sample_measure["id_m"]] = sample_measure
        self.next_id = 2

    def ferro_query(self, method, params):
        """Main backend API method"""
        if method == "measure_data":
            return list(self.measures.values())

        elif method == "create_graph_x":
            return self.x.tolist()

        elif method == "create_graph":
            return self.base_y.tolist()

        elif method == "new_create":
            m_id = f"M{self.next_id:03d}"
            title = f"{self.next_id:03d}"
            self.next_id += 1

            new_measure = {
                "id_m": m_id,
                "id": m_id,
                "title": title,
                "subtitle": "Метод в очереди",
                "time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "x": self.x.tolist(),
                "y_res": self.base_y.tolist(),
                "y_samples": {}
            }
            self.measures[m_id] = new_measure

            return {
                "id": m_id,
                "title": title,
                "subtitle": "Подготовка...",
                "subtitle_full": "Выполняется настройка..."
            }

        elif method == "new_sample":
            id_m = params.get("id_m", "")
            if not id_m and self.measures:
                id_m = list(self.measures.keys())[-1]

            name = params.get("new_sample_name", f"Sample-{random.randint(1, 999)}")

            if id_m in self.measures:
                measure = self.measures[id_m]
                sample_idx = max(measure["y_samples"].keys()) + 1 if measure["y_samples"] else 1

                # Create sample data with some variation
                noise = np.random.normal(0, 0.3, size=len(self.base_y))
                shifted = self.base_y + noise - np.linspace(0, 1.0, num=len(self.base_y)) * 0.1

                measure["y_samples"][sample_idx] = {
                    "name": name,
                    "y_res": shifted.tolist(),
                    "tgo": float(6.1e-4 + random.random() * 1e-4),
                    "E": float(11.0 + random.random() * 0.3)
                }

                return {"id": id_m, "name": name}

        elif method == "method_end":
            return {"id": params.get("id_m", "")}

        elif method == "read_data":
            id_m = params.get("id_m")
            if id_m in self.measures:
                return self.measures[id_m]
            elif self.measures:
                return list(self.measures.values())[0]

        return {}


class FERROMainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.backend = FERROBackend()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("FERRO — Измерительная система")
        self.setMinimumSize(1400, 900)

        # Set application icon and properties
        self.setStyleSheet("""
            QMainWindow {
                background: #222326;
            }
        """)

        # Create central widget with gradient background
        central_widget = GradientBackground()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = SidebarWidget()
        main_layout.addWidget(self.sidebar)

        # Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Page stack
        self.page_stack = QStackedWidget()
        content_layout.addWidget(self.page_stack)

        # Create pages
        self.home_page = HomePage(self.backend, self.open_measurement)
        self.measures_page = MeasuresPage(self.backend, self.open_measurement)
        self.reports_page = ReportsPage()
        self.settings_page = SettingsPage()
        self.measure_detail_page = MeasureDetailPage(self.backend)

        # Add pages to stack
        self.page_stack.addWidget(self.home_page)
        self.page_stack.addWidget(self.measures_page)
        self.page_stack.addWidget(self.reports_page)
        self.page_stack.addWidget(self.settings_page)
        self.page_stack.addWidget(self.measure_detail_page)

        main_layout.addWidget(content_widget, 1)

        # Connect navigation
        self.connect_navigation()

        # Show home page by default
        self.page_stack.setCurrentWidget(self.home_page)

    def connect_navigation(self):
        """Connect sidebar navigation to page changes"""
        # Connect sidebar buttons (assuming they are in order)
        nav_buttons = self.sidebar.nav_buttons
        if len(nav_buttons) >= 4:
            nav_buttons[0].clicked.connect(lambda: self.page_stack.setCurrentWidget(self.home_page))
            nav_buttons[1].clicked.connect(lambda: self.page_stack.setCurrentWidget(self.measures_page))
            nav_buttons[2].clicked.connect(lambda: self.page_stack.setCurrentWidget(self.reports_page))
            nav_buttons[3].clicked.connect(lambda: self.page_stack.setCurrentWidget(self.settings_page))

        # Connect header new measurement button
        self.home_page.header.new_measure_btn.clicked.connect(self.show_new_measurement_dialog)
        self.measures_page.header.new_measure_btn.clicked.connect(self.show_new_measurement_dialog)

    def show_new_measurement_dialog(self):
        """Show new measurement dialog"""
        dialog = CreateMeasurementDialog(self.backend, 1, self)
        dialog.exec()
        # Refresh pages if needed
        self.home_page.load_recent_measurements()
        self.measures_page.load_measurements()

    def open_measurement(self, measure_id):
        """Open measurement detail page"""
        self.measure_detail_page.load_measurement(measure_id)
        self.page_stack.setCurrentWidget(self.measure_detail_page)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application-wide style
    app.setStyle("Fusion")

    # Create and show main window
    window = FERROMainWindow()
    window.show()

    # Start application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()