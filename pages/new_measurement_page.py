"""
New measurement page
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QScrollArea, QFormLayout,
                             QLineEdit, QSpinBox, QComboBox, QGroupBox)
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import ModernCard, HeaderWidget
from styles import Styles


class NewMeasurementPage(BasePage):
    """Page for creating new measurements"""
    measurement_started = pyqtSignal(dict)
    start_measurement_process = pyqtSignal(dict)

    def __init__(self, backend, parent=None):
        # Сначала устанавливаем атрибуты
        self.backend = backend
        self.selected_method = 1

        # Потом вызываем родительский конструктор
        super().__init__("", "", parent)  # Пустые заголовки, т.к. используем кастомный header

        # Удаляем стандартный layout от BasePage
        if self.layout:
            # Очищаем layout, но не удаляем его
            while self.layout.count():
                item = self.layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self.setup_ui()

    def setup_ui(self):
        """Setup page UI"""
        # Создаем новый главный layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Setup custom header
        self.setup_custom_header(main_layout)

        # Setup content
        self.setup_content(main_layout)

    def setup_custom_header(self, parent_layout):
        """Setup custom header - ПРАВИЛЬНОЕ ПРОДОЛЖЕНИЕ САЙДБАРА"""
        self.header = QWidget()
        self.header.setFixedHeight(100)
        self.header.setContentsMargins(0, 0, 0, 0)
        self.header.setStyleSheet(f"""
            QWidget {{
                background: #7879F1;
                border: none;
                margin: 0;
                padding: 0;
            }}
        """)

        parent_layout.addWidget(self.header)
        parent_layout.setContentsMargins(0, 0, 0, 0)

    def setup_content(self, parent_layout):
        """Setup page content"""
        # Create main content widget with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
                margin: 0;
                padding: 0;
            }
        """)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(30, 20, 30, 20)  # Восстанавливаем отступы только для контента
        self.content_layout.setSpacing(25)

        # Method selection
        self.setup_method_selection(self.content_layout)

        # Method parameters
        self.setup_method_parameters(self.content_layout)

        # Action buttons
        self.setup_action_buttons(self.content_layout)

        self.content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        parent_layout.addWidget(scroll_area, 1)

    def setup_method_selection(self, parent_layout):
        """Setup method selection section - БЕЗ ЗАГОЛОВКОВ"""

        # Method cards grid - теперь 3 карточки в 2 ряда = 6 карточки
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Method cards - всего 6 методов
        methods = [
            (1, "ФРЧ", "Метод измерения при фиксированной частоте"),
            (2, "ФРД", "Метод измерения при фиксированной длинне"),
            (3, "СО", "Метод измерения для стержневых образцов"),
            (4, "СВЧФ1", "Метод первый для измерения СВЧ ферритов"),
            (5, "ЩР", "Метод измерения щелевыйм резонатором"),
            (6, "СВЧФ2", "Метод второй для измерения СВЧ ферритов")
        ]

        for i, (method_id, name, description) in enumerate(methods):
            row = i // 3
            col = i % 3
            card = self.create_method_card(method_id, name, description, "#7879F1")
            card.method_id = method_id
            grid_layout.addWidget(card, row, col)

        parent_layout.addWidget(grid_widget)

    def create_method_card(self, method_id, name, description, color="#7879F1"):
        """Create a method selection card"""
        card = ModernCard()
        card.setMinimumHeight(140)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        # Сохраняем ID метода в объекте карточки
        card.method_id = method_id

        # ВСЕГДА используем один цвет для обводки и текста - фиолетовый как у первого метода
        primary_color = "#7879F1"  # Фиксированный цвет для всего

        # Highlight if selected
        if method_id == self.selected_method:
            card.setStyleSheet(f"""
                ModernCard {{
                    background: rgba(40, 41, 44, 0.9);
                    border: 2px solid {primary_color};
                    border-radius: 12px;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                ModernCard {{
                    background: rgba(30, 31, 34, 0.8);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                }}
            """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)

        # Method header - БЕЗ бейджа в правом углу
        header_layout = QHBoxLayout()

        # Все названия методов одним цветом - фиолетовым
        method_name = QLabel(name)
        method_name.setStyleSheet(f"""
            QLabel {{
                color: {primary_color};
                font-size: 18px;
                font-weight: 600;
            }}
        """)

        header_layout.addWidget(method_name)
        header_layout.addStretch()  # Добавляем растяжку чтобы название было слева

        # Description
        method_desc = QLabel(description)
        method_desc.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 14px;
                line-height: 1.4;
            }}
        """)
        method_desc.setWordWrap(True)

        card_layout.addLayout(header_layout)
        card_layout.addWidget(method_desc)
        card_layout.addStretch()

        # Connect click
        card.mousePressEvent = lambda e, mid=method_id: self.select_method(mid)

        return card

    def setup_method_parameters(self, parent_layout):
        """Setup method parameters section"""
        # Section title
        method_names = {
            1: "ФРЧ - Метод измерения при фиксированной частоте",
            2: "ФРД - Метод измерения при фиксированной длинне",
            3: "СО - Метод измерения для стержневых образцов",
            4: "СВЧФ1 - Метод первый для измерения СВЧ ферритов",
            5: "ЩР - Метод измерения щелевыйм резонатором",
            6: "СВЧФ2 - Метод второй для измерения СВЧ ферритов"
        }

        title = WidgetFactory.create_label(
            f"Параметры исследования: {method_names.get(self.selected_method, 'Метод')}",
            font_size=18,
            bold=True
        )
        parent_layout.addWidget(title)

        # Parameters container
        params_container = QWidget()
        params_layout = QVBoxLayout(params_container)
        params_layout.setSpacing(20)

        # Оставляем только Дополнительные параметры, переименовываем в "Настройка резонатора"
        additional_group = self.create_resonator_settings_group()  # Переименованный метод
        params_layout.addWidget(additional_group)

        parent_layout.addWidget(params_container)

    def create_resonator_settings_group(self):
        """Create resonator settings group - бывшие Дополнительные параметры"""
        group = QGroupBox("Предварительная настройка перед началом измерения")  # Переименовали
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 12px;
                background: rgba(40, 41, 44, 0.6);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
            }}
        """)

        layout = QFormLayout(group)
        layout.setVerticalSpacing(12)
        layout.setHorizontalSpacing(20)

        # Общие для всех методы параметры резонатора
        if self.selected_method in [1, 2, 3, 5]:
            self.index_combo = QComboBox()
            self.index_combo.addItems(["2", "3", "4", "5"])
            self.index_combo.setCurrentText("2")
            self.index_combo.setStyleSheet(Styles.INPUT_FIELD)

            self.d_res_input = WidgetFactory.create_input("50.0")
            self.h_res_input = WidgetFactory.create_input("90.0")

            layout.addRow("Продольный индекс колебаний:", self.index_combo)
            layout.addRow("Диаметр резонатора (мм):", self.d_res_input)
            layout.addRow("Высота резонатора (мм):", self.h_res_input)

        elif self.selected_method in [4, 6]:
            self.d_res_input = WidgetFactory.create_input("11.0")
            self.d_sample_input = WidgetFactory.create_input("0.81")

            layout.addRow("Радиус резонатора (мм):", self.d_res_input)
            layout.addRow("Радиус образца (мм):", self.d_sample_input)

        # Параметры окружающей среды (общие для всех)
        self.temp_input = WidgetFactory.create_input("25.0")
        self.humidity_input = WidgetFactory.create_input("50.0")

        layout.addRow("Температура (°C):", self.temp_input)
        layout.addRow("Влажность (%):", self.humidity_input)

        return group

    def setup_action_buttons(self, parent_layout):
        """Setup action buttons section"""
        # Container for buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 20, 0, 0)

        buttons_layout.addStretch()

        # Clear button
        clear_btn = WidgetFactory.create_button("Очистить форму", style="secondary")
        clear_btn.setFixedWidth(150)
        clear_btn.clicked.connect(self.clear_form)

        # Start measurement button
        start_btn = WidgetFactory.create_button("Начать исследование", style="primary")
        start_btn.setFixedWidth(200)
        start_btn.clicked.connect(self.start_measurement)

        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(start_btn)

        parent_layout.addWidget(buttons_container)

    def select_method(self, method_id):
        """Select a different method"""
        self.selected_method = method_id

        # Обновляем выделение карточек
        self.update_method_cards_selection()

        # Clear and rebuild parameters section
        self.refresh_parameters()

    def update_method_cards_selection(self):
        """Update visual selection of method cards"""
        # Находим все карточки методов
        grid_widget = self.findChild(QWidget)  # Ищем grid widget
        if grid_widget:
            for child in grid_widget.findChildren(QWidget):
                if child.__class__.__name__ == "ModernCard" and hasattr(child, 'method_id'):
                    # Всегда используем один цвет для выделения
                    border_color = "#7879F1"

                    # Проверяем, это ли метод выбран
                    if child.method_id == self.selected_method:
                        # Выделяем выбранную карточку фиолетовым
                        child.setStyleSheet(f"""
                            ModernCard {{
                                background: rgba(40, 41, 44, 0.9);
                                border: 2px solid {border_color};
                                border-radius: 12px;
                            }}
                        """)
                    else:
                        # Сбрасываем стиль для остальных
                        child.setStyleSheet(f"""
                            ModernCard {{
                                background: rgba(30, 31, 34, 0.8);
                                border: 1px solid rgba(255, 255, 255, 0.1);
                                border-radius: 12px;
                            }}
                        """)

    def refresh_parameters(self):
        """Refresh parameters section when method changes"""
        # Находим родительский scroll area
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            # Создаем новый контент
            content_widget = QWidget()
            self.content_layout = QVBoxLayout(content_widget)
            self.content_layout.setContentsMargins(30, 20, 30, 20)
            self.content_layout.setSpacing(25)

            # Method selection
            self.setup_method_selection(self.content_layout)

            # Method parameters (обновляем)
            self.setup_method_parameters(self.content_layout)

            # Action buttons
            self.setup_action_buttons(self.content_layout)

            self.content_layout.addStretch()

            # Устанавливаем новый виджет
            scroll_area.setWidget(content_widget)

    def clear_form(self):
        """Clear all form fields"""
        # Очищаем поля в зависимости от метода
        if self.selected_method in [1, 2, 3, 5]:
            if hasattr(self, 'index_combo'):
                self.index_combo.setCurrentIndex(0)
            if hasattr(self, 'd_res_input'):
                self.d_res_input.clear()
            if hasattr(self, 'h_res_input'):
                self.h_res_input.clear()

        elif self.selected_method in [4, 6]:
            if hasattr(self, 'd_res_input'):
                self.d_res_input.clear()
            if hasattr(self, 'd_sample_input'):
                self.d_sample_input.clear()

        self.temp_input.clear()
        self.humidity_input.clear()

    def start_measurement(self):
        """Start the measurement process"""
        # Проверка на уже идущее измерение
        if hasattr(self, '_measurement_in_progress') and self._measurement_in_progress:
            print("Measurement already in progress")
            return

        # Устанавливаем флаг
        self._measurement_in_progress = True

        # Collect data from form
        measurement_data = self.collect_measurement_data()

        # Call backend to create measurement
        response = self.backend.ferro_query("new_create", measurement_data)

        if response and 'id' in response:
            # Добавляем ID измерения в данные
            measurement_data['measurement_id'] = response['id']
            measurement_data['measurement_response'] = response

            # Эмитируем сигнал вместо открытия диалога
            self.measurement_started.emit(measurement_data)
        else:
            # Сбрасываем флаг если ошибка
            self._measurement_in_progress = False

    def collect_measurement_data(self):
        """Collect measurement data from form"""
        data = {
            "method": self.selected_method,
            "temperature": float(self.temp_input.text() or "25.0"),
            "humidity": float(self.humidity_input.text() or "50.0"),
            "data": {
                str(self.selected_method): {}
            }
        }

        # Method-specific data - только параметры резонатора
        if self.selected_method == 1:  # ФРЧ
            data["data"][str(self.selected_method)] = {
                "index": self.index_combo.currentText() if hasattr(self, 'index_combo') else "2",
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "50.0",
                "h_res": self.h_res_input.text() if hasattr(self, 'h_res_input') else "90.0"
            }
        elif self.selected_method == 2:  # ФРД
            data["data"][str(self.selected_method)] = {
                "index": self.index_combo.currentText() if hasattr(self, 'index_combo') else "2",
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "45.0",
                "h_res": self.h_res_input.text() if hasattr(self, 'h_res_input') else "45.0"
            }
        elif self.selected_method == 3:  # СО
            data["data"][str(self.selected_method)] = {
                "index": self.index_combo.currentText() if hasattr(self, 'index_combo') else "1",
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "22.5",
                "h_res": self.h_res_input.text() if hasattr(self, 'h_res_input') else "45.0"
            }
        elif self.selected_method == 4:  # СВЧФ
            data["data"][str(self.selected_method)] = {
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "11.0",
                "d_sample": self.d_sample_input.text() if hasattr(self, 'd_sample_input') else "0.81"
            }
        elif self.selected_method == 5:
            data["data"][str(self.selected_method)] = {
                "index": self.index_combo.currentText() if hasattr(self, 'index_combo') else "2",
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "50.0",
                "h_res": self.h_res_input.text() if hasattr(self, 'h_res_input') else "90.0"
            }
        elif self.selected_method == 6:
            data["data"][str(self.selected_method)] = {
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "11.0",
                "d_sample": self.d_sample_input.text() if hasattr(self, 'd_sample_input') else "0.81"
            }

        return data

    def show_selected_method_notification(self, method_id):
        """Show notification about selected method"""
        method_names = {
            1: "ФРЧ - Метод фиксированной частоты",
            2: "ФРД - Метод фиксированной длины",
            3: "СО - Метод для стержневых образцов",
            4: "СВЧФ - Метод для СВЧ ферритов",
            5: "Метод 5",
            6: "Метод 6"
        }

        method_name = method_names.get(method_id, f"Метод {method_id}")

        # Можно добавить временное уведомление в интерфейсе
        notification = QLabel(f"Выбран метод: {method_name}")
        notification.setStyleSheet(f"""
            QLabel {{
                color: #7879F1;
                font-size: 14px;
                font-weight: 600;
                background: rgba(120, 121, 241, 0.1);
                border: 1px solid #7879F1;
                border-radius: 6px;
                padding: 8px 16px;
                margin: 10px 0;
            }}
        """)
        notification.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Добавляем уведомление в начало контента
        self.content_layout.insertWidget(0, notification)

        # Убираем уведомление через 3 секунды
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: notification.deleteLater())