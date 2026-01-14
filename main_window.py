"""
Main window
"""

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QGraphicsDropShadowEffect, QPushButton)
from backend import FERROBackend
from widgets import GradientBackground
from pages import HomePage, MeasuresPage, MeasureDetailPage, ReportsPage, SettingsPage
from pages.new_measurement_page import NewMeasurementPage
from widgets.sidebar import SidebarWidget
from widgets.measurement_process_widget import MeasurementProcessWidget


class FERROMainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.backend = FERROBackend()
        self.setObjectName("main_window")
        self.showMaximized()

        # Атрибуты для управления страницами
        self.measurement_process_widget = None
        self.is_measurement_active = False  # Флаг активного измерения

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

        # Sidebar - всегда активен
        self.sidebar = SidebarWidget()
        main_layout.addWidget(self.sidebar)

        # Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Page stack - для обычных страниц
        self.page_stack = QStackedWidget()
        content_layout.addWidget(self.page_stack)

        # Container для виджета процесса измерений
        self.process_container = QWidget()
        self.process_container.setVisible(False)
        self.process_layout = QVBoxLayout(self.process_container)
        self.process_layout.setContentsMargins(0, 0, 0, 0)

        content_layout.addWidget(self.process_container)
        main_layout.addWidget(content_widget, 1)

        # Create pages
        self.home_page = HomePage(self.backend, self.open_measurement)
        self.measures_page = MeasuresPage(self.backend, self.open_measurement)
        self.reports_page = ReportsPage(self)
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
                self.show_page(self.home_page)
            ))

            # Новое исследование
            nav_buttons[1].clicked.connect(lambda: (
                self.sidebar.set_active_button(nav_buttons[1]),
                self.open_new_measurement_page()
            ))

            # Измерения
            nav_buttons[2].clicked.connect(lambda: (
                self.sidebar.set_active_button(nav_buttons[2]),
                self.show_page(self.measures_page)
            ))

            # Отчёты
            nav_buttons[3].clicked.connect(lambda: (
                self.sidebar.set_active_button(nav_buttons[3]),
                self.show_page(self.reports_page)
            ))

        # Settings button in footer
        for child in self.sidebar.findChildren(QPushButton):
            if "Настройки" in child.text():
                child.clicked.connect(lambda: (
                    self.show_page(self.settings_page)
                ))
                break

        # На странице измерений кнопка "Новое исследование" в хедере
        if hasattr(self.measures_page, 'header'):
            self.measures_page.header.new_measure_btn.clicked.connect(
                lambda: (
                    self.sidebar.set_active_button(self.sidebar.nav_buttons[1]),
                    self.show_page(self.new_measurement_page)
                )
            )

        # На странице отчётов если есть кнопка
        if hasattr(self.reports_page, 'header'):
            # Ищем кнопку "Новое исследование" в хедере
            pass  # Можно добавить если нужно

        # Подключаем сигнал от страницы создания измерений
        self.new_measurement_page.measurement_started.connect(self.start_measurement_process)

    def show_page(self, page_widget):
        """Show a normal page"""
        # Проверяем специальные случаи
        if page_widget == self.new_measurement_page and self.is_measurement_active:
            # Блокируем переход на страницу создания измерений во время активного измерения
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Внимание",
                                    "Измерение уже выполняется. Завершите текущее измерение перед началом нового.")
            return

        # Показываем запрошенную страницу
        self.page_stack.setCurrentWidget(page_widget)
        self.page_stack.show()

        # Скрываем контейнер процесса если виден
        self.process_container.hide()

    def start_measurement_process(self, measurement_data):
        """Start measurement process - отдельный режим"""
        print(f"Starting measurement process for ID: {measurement_data.get('measurement_id')}")

        measurement_id = measurement_data.get('measurement_id')
        if not measurement_id:
            print("Error: No measurement ID provided")
            return

        # Устанавливаем флаг активного измерения
        self.is_measurement_active = True

        # Создаем виджет процесса измерений если еще не создан
        if not self.measurement_process_widget:
            self.measurement_process_widget = MeasurementProcessWidget(
                self.backend,
                measurement_id,
                self
            )
            self.process_layout.addWidget(self.measurement_process_widget)
        else:
            # Обновляем ID измерения
            self.measurement_process_widget.measure_id = measurement_id

        # Скрываем все обычные страницы
        self.page_stack.hide()

        # Показываем контейнер с процессом измерений
        self.process_container.show()

        # Запускаем процесс
        self.measurement_process_widget.start_measurement_process()

        # Подключаем сигналы завершения
        self.measurement_process_widget.measurement_finished.connect(
            self.finish_measurement_process
        )

        print(f"Measurement process started for ID: {measurement_id}")

    def finish_measurement_process(self):
        """Finish measurement process and return to normal mode"""
        print("Finishing measurement process")

        # Сбрасываем флаг
        self.is_measurement_active = False

        # Скрываем контейнер процесса
        self.process_container.hide()

        # Показываем обычные страницы
        self.page_stack.show()

        # Переходим на страницу измерений (где можно увидеть результат)
        self.page_stack.setCurrentWidget(self.measures_page)
        if hasattr(self.sidebar, 'nav_buttons') and len(self.sidebar.nav_buttons) >= 3:
            self.sidebar.set_active_button(self.sidebar.nav_buttons[2])

        # Обновляем список измерений
        if hasattr(self.measures_page, 'load_measurements'):
            self.measures_page.load_measurements()

        print("Returned to normal mode")

    def open_measurement(self, measure_id):
        """Open measurement detail page"""
        # Если идет процесс измерений, блокируем переход
        if self.is_measurement_active:
            print("Измерение в процессе, просмотр деталей невозможен")
            return

        self.measure_detail_page.load_measurement(measure_id)
        self.show_page(self.measure_detail_page)

    def open_new_measurement_page(self, method_id=None):
        """Open new measurement page with optional method selection"""
        if self.is_measurement_active:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Внимание",
                                    "Измерение уже выполняется. Завершите текущее измерение перед началом нового.")
            return

        print(f"open_new_measurement_page called with method_id: {method_id}")

        if method_id and hasattr(self.new_measurement_page, 'selected_method'):
            self.new_measurement_page.selected_method = method_id
            if hasattr(self.new_measurement_page, 'refresh_parameters'):
                self.new_measurement_page.refresh_parameters()

        # Активируем кнопку "Новое исследование" в сайдбаре
        if hasattr(self, 'sidebar') and hasattr(self.sidebar, 'nav_buttons'):
            if len(self.sidebar.nav_buttons) >= 2:
                self.sidebar.set_active_button(self.sidebar.nav_buttons[1])

        # Показываем страницу создания измерений
        self.page_stack.setCurrentWidget(self.new_measurement_page)
        self.page_stack.show()
        self.process_container.hide()