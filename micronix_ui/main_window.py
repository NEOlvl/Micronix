import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class SidePanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Устанавливаем градиентный фон для всей боковой панели
        self.setStyleSheet("""
            SidePanel {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0.0 #31364a,
                    stop: 0.2 #30303c,
                    stop: 0.4 #2f2f39,
                    stop: 0.6 #2e2e37,
                    stop: 0.8 #2d2d34,
                    stop: 1.0 #2d2c32     
                );
                border: none;
            }
        """)

        # Верхняя часть с логотипом MICRONIX
        header_widget = QWidget()
        header_widget.setFixedHeight(120)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Логотип MICRONIX
        logo_label = QLabel("MICRONIX")
        logo_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
                background-color: transparent;
            }
        """)
        header_layout.addWidget(logo_label)

        layout.addWidget(header_widget)

        # Основное меню
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)

        # Пункты меню (текстовые кнопки)
        menu_items = [
            ("Главная", True),
            ("Измерения", False),
            ("Отчёты", False)
        ]

        for text, is_active in menu_items:
            menu_item = self.create_menu_item(text, is_active)
            menu_layout.addWidget(menu_item)

        layout.addWidget(menu_widget)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.3); height: 1px; margin: 10px 20px;")
        layout.addWidget(separator)

        # Секция синхронизации
        sync_widget = QWidget()
        sync_layout = QVBoxLayout(sync_widget)
        sync_layout.setContentsMargins(20, 15, 20, 15)
        sync_layout.setSpacing(8)

        # Заголовок синхронизации
        sync_title = QLabel("Синхронизация")
        sync_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        sync_layout.addWidget(sync_title)

        # Подзаголовок настроек
        settings_label = QLabel("Настройки")
        settings_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                background-color: transparent;
            }
        """)
        sync_layout.addWidget(settings_label)

        # Пункт "Гость"
        guest_item = self.create_menu_item("Гость", False, 10)
        sync_layout.addWidget(guest_item)

        sync_layout.addStretch()
        layout.addWidget(sync_widget)

        # Растягивающийся элемент в конце
        layout.addStretch()

    def create_menu_item(self, text, is_active=False, indent=0):
        widget = QWidget()
        widget.setFixedHeight(45)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20 + indent, 0, 20, 0)

        label = QLabel(text)

        if is_active:
            # Активный пункт меню
            widget.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.2); 
                border-left: 3px solid white;
            """)
            label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    background-color: transparent;
                }
            """)
        else:
            # Неактивный пункт меню
            widget.setStyleSheet("background-color: transparent;")
            label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 14px;
                    background-color: transparent;
                }
            """)

        layout.addWidget(label)
        layout.addStretch()

        return widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Micronix app")
        self.setGeometry(360, 140, 1200, 800)


        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной горизонтальный layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Боковая панель
        self.side_panel = SidePanel()
        main_layout.addWidget(self.side_panel)

        # Основная область
        self.main_area = QFrame()
        self.main_area.setStyleSheet("background-color: #2d2c32;")

        # Добавим содержимое в основную область
        main_area_layout = QVBoxLayout(self.main_area)
        main_area_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content_label = QLabel("Основная рабочая область")
        content_label.setStyleSheet("font-size: 18px; color: #ffffff;")
        main_area_layout.addWidget(content_label)

        main_layout.addWidget(self.main_area)
