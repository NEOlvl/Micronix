import sys
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QListWidget, QListWidgetItem,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QToolBar, QStatusBar, QSplitter, QTextEdit, QDialog, QDialogButtonBox,
    QLineEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox,
    QFormLayout, QMessageBox, QFileDialog, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QDateTime
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QPainter, QAction, QPixmap
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import csv
import os


@dataclass
class MeasurementData:
    name: str
    device: str
    date: str
    frequency_min: float
    db_level: float
    quality: float
    with_sample: bool


class CustomChartView(QChartView):
    def __init__(self, chart):
        super().__init__(chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)


class SidebarWidget(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(220)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)

        logo_btn = QPushButton("FERRO")
        logo_btn.setObjectName("logoBtn")
        logo_btn.setFixedHeight(60)
        header_layout.addWidget(logo_btn)

        layout.addWidget(header_frame)

        # Navigation
        nav_widget = QListWidget()
        nav_widget.setObjectName("navWidget")
        nav_widget.setFrameShape(QFrame.Shape.NoFrame)

        pages = [
            ("Главная", "home"),
            ("Измерения", "measurement"),
            ("Вычисления", "calculation"),
            ("Отчёты", "documents")
        ]

        for text, icon in pages:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, icon)
            nav_widget.addItem(item)

        nav_widget.currentRowChanged.connect(self.page_changed.emit)
        nav_widget.setCurrentRow(0)

        layout.addWidget(nav_widget)

        # Footer
        footer_frame = QFrame()
        footer_layout = QVBoxLayout(footer_frame)

        footer_buttons = [
            ("Синхронизация", "cloud"),
            ("Настройки", "setting"),
            ("Гость", "account")
        ]

        for text, icon in footer_buttons:
            btn = QPushButton(text)
            btn.setObjectName("footerBtn")
            btn.setFixedHeight(40)
            footer_layout.addWidget(btn)

        layout.addWidget(footer_frame)

        self.setLayout(layout)


class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.series1 = None
        self.series2 = None
        self.chart = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Graph container
        graph_container = QWidget()
        graph_layout = QHBoxLayout(graph_container)

        # Chart
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        graph_layout.addWidget(self.chart_view, 3)

        # Info panel
        info_widget = QWidget()
        info_widget.setFixedWidth(300)
        info_layout = QVBoxLayout(info_widget)

        # Measurement info
        info_data = [
            ("Без образца", "#7879F1"),
            ("Точка min (F₀)", "76 ГГц\n-30 ДцБ"),
            ("Добротность (Q)", "789"),
            ("С образцом", "#f8c33c"),
            ("Точка min (F₀)", "76 ГГц\n-30 ДцБ"),
            ("Добротность (Q)", "789")
        ]

        for i, (title, value) in enumerate(info_data):
            if i in [0, 3]:  # Headers
                color = "#7879F1" if i == 0 else "#f8c33c"
                header = self.create_header(title, color)
                info_layout.addWidget(header)
            else:
                info_item = self.create_info_item(title, value)
                info_layout.addWidget(info_item)

        info_layout.addStretch()

        calc_label = QLabel("Привязанное вычисление")
        calc_label.setObjectName("calcLabel")
        info_layout.addWidget(calc_label)

        graph_layout.addWidget(info_widget)
        layout.addWidget(graph_container)

        self.setLayout(layout)

    def create_header(self, text, color):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        color_indicator = QLabel()
        color_indicator.setFixedSize(12, 12)
        color_indicator.setStyleSheet(f"background-color: {color}; border-radius: 6px;")

        label = QLabel(text)
        label.setStyleSheet("font-weight: bold;")

        layout.addWidget(color_indicator)
        layout.addWidget(label)
        layout.addStretch()

        return widget

    def create_info_item(self, title, value):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #888;")

        value_label = QLabel(value)
        value_label.setStyleSheet("font-weight: bold;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return widget

    def setup_chart(self, x_data, y1_data, y2_data):
        if self.chart:
            self.chart_view.setChart(None)
            self.chart.deleteLater()

        self.chart = QChart()
        self.chart.setTitle("Измерение частотной характеристики")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        # Create series
        self.series1 = QLineSeries()
        self.series1.setName("Без образца")
        self.series1.setColor(QColor("#7879F1"))

        self.series2 = QLineSeries()
        self.series2.setName("С образцом")
        self.series2.setColor(QColor("#f8c33c"))

        # Add data to series
        for x, y in zip(x_data, y1_data):
            self.series1.append(x, y)

        for x, y in zip(x_data, y2_data):
            self.series2.append(x, y)

        self.chart.addSeries(self.series1)
        self.chart.addSeries(self.series2)

        # Create axes
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Частота, ГГц")
        self.axis_x.setRange(min(x_data), max(x_data))

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("ДцБ")
        self.axis_y.setRange(min(min(y1_data), min(y2_data)) - 5,
                             max(max(y1_data), max(y2_data)) + 5)

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.series1.attachAxis(self.axis_x)
        self.series1.attachAxis(self.axis_y)
        self.series2.attachAxis(self.axis_x)
        self.series2.attachAxis(self.axis_y)

        self.chart_view.setChart(self.chart)


class MeasurementsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_measurement = None
        self.setup_ui()
        self.load_sample_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Header
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)

        title = QLabel("Измерение #t7UWN")
        title.setObjectName("pageTitle")

        subtitle_widget = QWidget()
        subtitle_layout = QHBoxLayout(subtitle_widget)

        # Measurement info
        self.info_widget = QWidget()
        self.info_layout = QHBoxLayout(self.info_widget)

        self.info_items = []
        info_texts = ["CABAN R180", "RESONATOR 4", "19.11.2024 17:56:46"]
        for text in info_texts:
            label = QLabel(text)
            label.setObjectName("infoLabel")
            self.info_layout.addWidget(label)
            self.info_items.append(label)

        self.info_layout.addStretch()

        # Action buttons
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)

        settings_btn = QPushButton("Настройки")
        self.download_btn = QPushButton("Скачать")

        settings_btn.setObjectName("actionBtn")
        self.download_btn.setObjectName("actionBtn")

        settings_btn.clicked.connect(self.show_settings)
        self.download_btn.clicked.connect(self.show_download_options)

        action_layout.addWidget(settings_btn)
        action_layout.addWidget(self.download_btn)
        action_layout.addStretch()

        subtitle_layout.addWidget(self.info_widget)
        subtitle_layout.addWidget(action_widget)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle_widget)

        layout.addWidget(header_widget)

        # Graph
        self.graph_widget = GraphWidget()
        layout.addWidget(self.graph_widget)

        self.setLayout(layout)

    def load_sample_data(self):
        # Generate sample resonance data
        x_data = np.linspace(70, 82, 200)

        # Resonance curve without sample
        f0_1, q1 = 76.0, 789
        y1_data = -30 * (1 + ((x_data - f0_1) / (f0_1 / (2 * q1))) ** 2)

        # Resonance curve with sample (shifted)
        f0_2, q2 = 76.5, 650
        y2_data = -28 * (1 + ((x_data - f0_2) / (f0_2 / (2 * q2))) ** 2)

        self.graph_widget.setup_chart(x_data, y1_data, y2_data)
        self.current_measurement = (x_data, y1_data, y2_data)

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_download_options(self):
        menu = QDialog(self)
        menu.setWindowTitle("Скачать")
        menu.setFixedSize(200, 100)

        layout = QVBoxLayout()

        png_btn = QPushButton("Изображение (PNG)")
        csv_btn = QPushButton("Данные (CSV)")

        png_btn.clicked.connect(lambda: self.export_png(menu))
        csv_btn.clicked.connect(lambda: self.export_csv(menu))

        layout.addWidget(png_btn)
        layout.addWidget(csv_btn)

        menu.setLayout(layout)
        menu.exec()

    def export_png(self, parent):
        if self.current_measurement:
            filename, _ = QFileDialog.getSaveFileName(
                parent, "Сохранить как PNG", "measurement.png", "PNG Files (*.png)"
            )
            if filename:
                pixmap = self.graph_widget.chart_view.grab()
                pixmap.save(filename, "PNG")
                QMessageBox.information(parent, "Успех", f"График сохранен как {filename}")

    def export_csv(self, parent):
        if self.current_measurement:
            filename, _ = QFileDialog.getSaveFileName(
                parent, "Сохранить как CSV", "measurement.csv", "CSV Files (*.csv)"
            )
            if filename:
                x_data, y1_data, y2_data = self.current_measurement
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Frequency', 'Without Sample', 'With Sample'])
                    for x, y1, y2 in zip(x_data, y1_data, y2_data):
                        writer.writerow([x, y1, y2])
                QMessageBox.information(parent, "Успех", f"Данные сохранены как {filename}")


class MeasurementsListPage(QWidget):
    def __init__(self):
        super().__init__()
        self.measurements = []
        self.setup_ui()
        self.load_sample_measurements()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Header
        header = QLabel("Все измерения")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Название", "Устройство", "Дата", "F₀ (ГГц)", "ДцБ", "Добротность"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_sample_measurements(self):
        self.measurements = [
            MeasurementData("Измерение #t7UWN", "CABAN R180", "19.11.2024 17:56", 76.0, -30, 789, False),
            MeasurementData("Измерение #a5B2X", "CABAN R180", "19.11.2024 18:30", 76.5, -28, 650, True),
            MeasurementData("Измерение #k9P4M", "RESONATOR 4", "20.11.2024 09:15", 75.8, -32, 820, False),
        ]

        self.table.setRowCount(len(self.measurements))

        for row, measurement in enumerate(self.measurements):
            self.table.setItem(row, 0, QTableWidgetItem(measurement.name))
            self.table.setItem(row, 1, QTableWidgetItem(measurement.device))
            self.table.setItem(row, 2, QTableWidgetItem(measurement.date))
            self.table.setItem(row, 3, QTableWidgetItem(f"{measurement.frequency_min:.1f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{measurement.db_level:.0f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{measurement.quality:.0f}"))


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Главная - Бином")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Welcome card
        welcome_card = QFrame()
        welcome_card.setObjectName("welcomeCard")
        welcome_layout = QVBoxLayout(welcome_card)

        welcome_text = QLabel("Добро пожаловать в FERRO")
        welcome_text.setObjectName("welcomeText")

        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)

        stats = [
            ("Всего измерений", "156"),
            ("Активные устройства", "3"),
            ("Последнее измерение", "Сегодня 14:30")
        ]

        for stat_name, stat_value in stats:
            stat_frame = QFrame()
            stat_frame.setObjectName("statFrame")
            stat_layout = QVBoxLayout(stat_frame)

            name_label = QLabel(stat_name)
            value_label = QLabel(stat_value)
            value_label.setObjectName("statValue")

            stat_layout.addWidget(name_label)
            stat_layout.addWidget(value_label)
            stats_layout.addWidget(stat_frame)

        welcome_layout.addWidget(welcome_text)
        welcome_layout.addWidget(stats_widget)

        layout.addWidget(welcome_card)
        layout.addStretch()

        self.setLayout(layout)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки измерения")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Device settings
        device_group = QGroupBox("Настройки устройства")
        device_layout = QFormLayout()

        self.device_combo = QComboBox()
        self.device_combo.addItems(["CABAN R180", "RESONATOR 4", "CABAN R54"])

        self.frequency_start = QDoubleSpinBox()
        self.frequency_start.setRange(1, 100)
        self.frequency_start.setValue(70)
        self.frequency_start.setSuffix(" ГГц")

        self.frequency_end = QDoubleSpinBox()
        self.frequency_end.setRange(1, 100)
        self.frequency_end.setValue(82)
        self.frequency_end.setSuffix(" ГГц")

        device_layout.addRow("Устройство:", self.device_combo)
        device_layout.addRow("Начальная частота:", self.frequency_start)
        device_layout.addRow("Конечная частота:", self.frequency_end)

        device_group.setLayout(device_layout)

        # Measurement settings
        measure_group = QGroupBox("Параметры измерения")
        measure_layout = QFormLayout()

        self.samples_spin = QSpinBox()
        self.samples_spin.setRange(10, 1000)
        self.samples_spin.setValue(200)

        self.auto_save = QCheckBox()
        self.auto_save.setChecked(True)

        measure_layout.addRow("Количество точек:", self.samples_spin)
        measure_layout.addRow("Автосохранение:", self.auto_save)

        measure_group.setLayout(measure_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(device_group)
        layout.addWidget(measure_group)
        layout.addWidget(button_box)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FERRO / Бином")
        self.setGeometry(100, 100, 1400, 900)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = SidebarWidget()
        layout.addWidget(self.sidebar)

        # Main content area
        self.stacked_widget = QStackedWidget()

        # Create pages
        self.home_page = HomePage()
        self.measurements_page = MeasurementsPage()
        self.measurements_list_page = MeasurementsListPage()

        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.measurements_list_page)
        self.stacked_widget.addWidget(self.measurements_page)

        layout.addWidget(self.stacked_widget)

        # Connect signals
        self.sidebar.page_changed.connect(self.on_page_changed)

        # Setup toolbar
        self.setup_toolbar()

    def setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Organization info
        org_label = QLabel("Бином")
        org_label.setObjectName("orgLabel")
        toolbar.addWidget(org_label)

        toolbar.addSeparator()

        # Page title
        self.page_title = QLabel("Главная")
        self.page_title.setObjectName("pageTitleLabel")
        toolbar.addWidget(self.page_title)

        # Вместо addStretch() создаем растягивающийся виджет
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)

        # Sync status
        sync_label = QLabel("Синхронизировано")
        sync_label.setObjectName("syncLabel")
        toolbar.addWidget(sync_label)

    def on_page_changed(self, index):
        page_titles = ["Главная", "Измерения", "Вычисления", "Отчёты"]
        if index < len(page_titles):
            self.page_title.setText(page_titles[index])
            self.stacked_widget.setCurrentIndex(min(index, self.stacked_widget.count() - 1))

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2c33;
                color: #e0e0e1;
            }
            #headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(75, 113, 214, 0.14), stop:0.33 rgba(75, 113, 214, 0.14),
                    stop:0.88 transparent);
                border-bottom: 1px solid #ffffff26;
            }
            #logoBtn, #footerBtn {
                background: transparent;
                color: #e0e0e1;
                border: none;
                text-align: left;
                padding-left: 15px;
            }
            #logoBtn:hover, #footerBtn:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            #navWidget {
                background: transparent;
                color: #e0e0e1;
                border: none;
                outline: none;
            }
            #navWidget::item {
                padding: 10px 15px;
                border: none;
                background: transparent;
                color: #8586f5;
            }
            #navWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.1);
            }
            #navWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
            #pageTitle {
                font-size: 24px;
                font-weight: bold;
                color: #e0e0e1;
                margin-bottom: 10px;
            }
            #infoLabel {
                background-color: #424147;
                padding: 8px 12px;
                border-radius: 5px;
                margin-right: 10px;
                font-size: 14px;
            }
            #actionBtn {
                background-color: #424147;
                color: #e0e0e1;
                padding: 8px 16px;
                border-radius: 5px;
                border: none;
                margin-left: 10px;
            }
            #actionBtn:hover {
                background-color: #4a4a50;
            }
            #calcLabel {
                background-color: #424147;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
                margin-top: 20px;
            }
            QChartView {
                background-color: white;
                border-radius: 5px;
            }
            #welcomeCard {
                background-color: #424147;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
            }
            #welcomeText {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
            }
            #statFrame {
                background-color: #2d2c33;
                padding: 15px;
                border-radius: 8px;
                margin-right: 10px;
            }
            #statValue {
                font-size: 20px;
                font-weight: bold;
                color: #7879F1;
            }
            QToolBar {
                background-color: #2d2c33;
                border: none;
                padding: 5px 10px;
            }
            #orgLabel {
                font-weight: bold;
                color: #7879F1;
                padding: 5px 10px;
            }
            #pageTitleLabel {
                font-size: 14px;
                padding: 5px 10px;
            }
            #syncLabel {
                color: #55aa68;
                font-size: 12px;
                padding: 5px 10px;
            }
            QTableWidget {
                background-color: #424147;
                color: #e0e0e1;
                gridline-color: #555555;
                border: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555555;
            }
            QHeaderView::section {
                background-color: #2d2c33;
                color: #e0e0e1;
                padding: 8px;
                border: none;
            }
            QGroupBox {
                color: #e0e0e1;
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)


def main():
    app = QApplication(sys.argv)

    # Set application font
    font = QFont("Arial", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()