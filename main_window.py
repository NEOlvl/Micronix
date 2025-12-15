"""
Main window
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QGraphicsDropShadowEffect, QPushButton)
from backend import FERROBackend
from widgets import GradientBackground, SidebarWidget
from pages import HomePage, MeasuresPage, MeasureDetailPage, ReportsPage, SettingsPage
from pages.new_measurement_page import NewMeasurementPage


class FERROMainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.backend = FERROBackend()
        self.setObjectName("main_window")
        self.showMaximized()
        self.setup_ui()

    def setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle("FERRO — Измерительная система")
        self.setMinimumSize(1400, 900)

        # Create central widget with gradient background
        central_widget = GradientBackground()

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        central_widget.setGraphicsEffect(shadow)

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
        self.new_measurement_page = NewMeasurementPage(self.backend)

        # Add pages to stack
        self.page_stack.addWidget(self.home_page)
        self.page_stack.addWidget(self.measures_page)
        self.page_stack.addWidget(self.reports_page)
        self.page_stack.addWidget(self.settings_page)
        self.page_stack.addWidget(self.measure_detail_page)
        self.page_stack.addWidget(self.new_measurement_page)

        main_layout.addWidget(content_widget, 1)

        # Connect navigation
        self.connect_navigation()

        # Show home page by default
        self.page_stack.setCurrentWidget(self.home_page)

    def connect_navigation(self):
        """Connect sidebar navigation to page changes"""
        # Connect sidebar buttons
        nav_buttons = self.sidebar.nav_buttons

        if len(nav_buttons) >= 4:
            # Главная
            nav_buttons[0].clicked.connect(lambda: (
                self.sidebar.set_active_button(nav_buttons[0]),
                self.page_stack.setCurrentWidget(self.home_page)
            ))

            # Новое исследование
            nav_buttons[1].clicked.connect(lambda: (
                self.sidebar.set_active_button(nav_buttons[1]),
                self.page_stack.setCurrentWidget(self.new_measurement_page)
            ))

            # Измерения
            nav_buttons[2].clicked.connect(lambda: (
                self.sidebar.set_active_button(nav_buttons[2]),
                self.page_stack.setCurrentWidget(self.measures_page)
            ))

            # Отчёты
            nav_buttons[3].clicked.connect(lambda: (
                self.sidebar.set_active_button(nav_buttons[3]),
                self.page_stack.setCurrentWidget(self.reports_page)
            ))

        # Settings button in footer
        settings_btn = self.sidebar.findChild(QPushButton, "settings_button")
        if not settings_btn:
            # Ищем кнопку настроек по тексту
            for child in self.sidebar.findChildren(QPushButton):
                if "Настройки" in child.text():
                    child.clicked.connect(lambda: (
                        self.page_stack.setCurrentWidget(self.settings_page)
                    ))
                    break

        # На странице измерений кнопка "Новое исследование" переходит на новую страницу
        if hasattr(self.measures_page, 'header'):
            self.measures_page.header.new_measure_btn.clicked.connect(
                lambda: (
                    self.sidebar.set_active_button(self.sidebar.nav_buttons[1]),
                    self.page_stack.setCurrentWidget(self.new_measurement_page)
                )
            )

        # НА ГЛАВНОЙ СТРАНИЦЕ ЕСТЬ HEADER - подключаем кнопку если нужно
        # (В текущем коде кнопка скрыта, но можно показать если нужно)
        if hasattr(self.home_page, 'header'):
            # Можно подключить что-то к кнопке в header главной страницы
            pass

    def open_measurement(self, measure_id):
        """Open measurement detail page"""
        self.measure_detail_page.load_measurement(measure_id)
        self.page_stack.setCurrentWidget(self.measure_detail_page)

    def open_new_measurement_page(self, method_id=None):
        """Open new measurement page with optional method selection"""
        if method_id:
            self.new_measurement_page.selected_method = method_id
            self.new_measurement_page.refresh_parameters()

        # Активируем кнопку "Новое исследование" в сайдбаре
        if len(self.sidebar.nav_buttons) >= 2:
            self.sidebar.set_active_button(self.sidebar.nav_buttons[1])

        self.page_stack.setCurrentWidget(self.new_measurement_page)