"""
New measurement page
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QScrollArea, QFormLayout,
                             QLineEdit, QSpinBox, QComboBox, QGroupBox)
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import ModernCard, HeaderWidget
from styles import Styles


class NewMeasurementPage(BasePage):
    """Page for creating new measurements"""

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
        """Setup custom header"""
        self.header = HeaderWidget("Новое исследование", "Создание нового измерения", self)

        # Hide new measure button (we're already on measurement page)
        self.header.new_measure_btn.hide()

        parent_layout.addWidget(self.header)

    def setup_content(self, parent_layout):
        """Setup page content"""
        # Create main content widget with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(30, 20, 30, 20)
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
        """Setup method selection section"""
        # Section title
        section_title = WidgetFactory.create_label("Выберите метод исследования:", font_size=18, bold=True)
        parent_layout.addWidget(section_title)

        # Добавляем информацию о выбранном методе
        if self.selected_method:
            method_names = {
                1: "ФРЧ - Метод фиксированной частоты",
                2: "ФРД - Метод фиксированной длины",
                3: "СО - Метод для стержневых образцов",
                4: "СВЧФ - Метод для СВЧ ферритов",
                5: "Метод 5",  # НОВЫЙ МЕТОД
                6: "Метод 6"  # НОВЫЙ МЕТОД
            }

            selected_text = WidgetFactory.create_label(
                f"Выбран метод: {method_names.get(self.selected_method, f'Метод {self.selected_method}')}",
                color="#7879F1",
                font_size=14,
                bold=True
            )
            selected_text.setStyleSheet("margin-bottom: 10px;")
            parent_layout.addWidget(selected_text)

        # Method cards grid - теперь 3 карточки в 2 ряда = 6 карточки
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Method cards - всего 6 методов (теперь только 3 значения)
        methods = [
            (1, "ФРЧ", "Метод фиксированной частоты"),
            (2, "ФРД", "Метод фиксированной длины"),
            (3, "СО", "Метод для стержневых образцов"),
            (4, "СВЧФ", "Метод для СВЧ ферритов"),
            (5, "Метод 5", "Описание метода 5"),
            (6, "Метод 6", "Описание метода 6")
        ]

        for i, (method_id, name, description) in enumerate(methods):  # Только 3 значения
            row = i // 3  # 3 карточки в ряд
            col = i % 3
            # Всегда передаем фиолетовый цвет (#7879F1)
            card = self.create_method_card(method_id, name, description, "#7879F1")
            # Сохраняем ID метода в карточке
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
                color: {primary_color};  # ВСЕГДА фиолетовый цвет
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
            1: "ФРЧ - Метод фиксированной частоты",
            2: "ФРД - Метод фиксированной длины",
            3: "СО - Метод для стержневых образцов",
            4: "СВЧФ - Метод для СВЧ ферритов",
            5: "Метод 5",  # НОВЫЙ
            6: "Метод 6"   # НОВЫЙ
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

        # Basic parameters
        basic_group = self.create_basic_parameters_group()
        params_layout.addWidget(basic_group)

        # Method-specific parameters
        method_group = self.create_method_specific_group()
        params_layout.addWidget(method_group)

        # Additional parameters
        additional_group = self.create_additional_parameters_group()
        params_layout.addWidget(additional_group)

        parent_layout.addWidget(params_container)

    def create_basic_parameters_group(self):
        """Create basic parameters group"""
        group = QGroupBox("Основные параметры")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 8px;
                margin-top: 12px;
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

        # Sample name
        self.sample_name_input = WidgetFactory.create_input("Образец 1")
        layout.addRow("Название образца:", self.sample_name_input)

        # Measurements count
        self.measurements_count = QSpinBox()
        self.measurements_count.setRange(1, 100)
        self.measurements_count.setValue(1)
        self.measurements_count.setStyleSheet(Styles.INPUT_FIELD)
        layout.addRow("Количество измерений:", self.measurements_count)

        # Operator name
        self.operator_input = WidgetFactory.create_input("Оператор")
        layout.addRow("Оператор:", self.operator_input)

        # Comments
        self.comments_input = QLineEdit()
        self.comments_input.setPlaceholderText("Дополнительные комментарии...")
        self.comments_input.setStyleSheet(Styles.INPUT_FIELD)
        layout.addRow("Комментарии:", self.comments_input)

        return group

    def create_method_specific_group(self):
        """Create method-specific parameters group"""
        group = QGroupBox("Параметры метода")
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

        # Method-specific parameters based on selected method
        if self.selected_method == 1:  # ФРЧ
            self.thickness_input = WidgetFactory.create_input("2.5")
            self.piston_move_input = WidgetFactory.create_input("10.0")

            layout.addRow("Толщина образца (мм):", self.thickness_input)
            layout.addRow("Перемещение поршня (мм):", self.piston_move_input)

        elif self.selected_method == 2:  # ФРД
            self.thickness_input = WidgetFactory.create_input("2.5")
            layout.addRow("Толщина образца (мм):", self.thickness_input)

        elif self.selected_method == 3:  # СО
            self.radius_input = WidgetFactory.create_input("5.0")
            layout.addRow("Радиус образца (мм):", self.radius_input)

        elif self.selected_method == 4:  # СВЧФ
            self.form_combo = QComboBox()
            self.form_combo.addItems(["Стержень", "Квадратная"])
            self.form_combo.setStyleSheet(Styles.INPUT_FIELD)
            self.mp_input = WidgetFactory.create_input("0.5")
            layout.addRow("Форма образца:", self.form_combo)
            layout.addRow("Поперечная составляющая МП:", self.mp_input)

        elif self.selected_method == 5:  # НОВЫЙ МЕТОД 5
            # TODO: Добавить параметры для метода 5
            self.param1_input = WidgetFactory.create_input("Значение 1")
            self.param2_input = WidgetFactory.create_input("Значение 2")
            layout.addRow("Параметр 1:", self.param1_input)
            layout.addRow("Параметр 2:", self.param2_input)

        elif self.selected_method == 6:  # НОВЫЙ МЕТОД 6
            # TODO: Добавить параметры для метода 6
            self.paramA_input = WidgetFactory.create_input("Значение A")
            self.paramB_input = WidgetFactory.create_input("Значение B")
            layout.addRow("Параметр A:", self.paramA_input)
            layout.addRow("Параметр B:", self.paramB_input)

        return group

    def create_additional_parameters_group(self):
        """Create additional parameters group"""
        group = QGroupBox("Дополнительные параметры")
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

        # Common additional parameters
        if self.selected_method in [1, 2, 3]:
            self.index_combo = QComboBox()
            self.index_combo.addItems(["2", "3", "4", "5"])
            self.index_combo.setCurrentText("2")
            self.index_combo.setStyleSheet(Styles.INPUT_FIELD)
            self.d_res_input = WidgetFactory.create_input("50.0")
            self.h_res_input = WidgetFactory.create_input("90.0")
            layout.addRow("Продольный индекс колебаний:", self.index_combo)
            layout.addRow("Диаметр резонатора (мм):", self.d_res_input)
            layout.addRow("Высота резонатора (мм):", self.h_res_input)

        elif self.selected_method == 4:
            self.d_res_input = WidgetFactory.create_input("11.0")
            self.d_sample_input = WidgetFactory.create_input("0.81")
            layout.addRow("Радиус резонатора (мм):", self.d_res_input)
            layout.addRow("Радиус образца (мм):", self.d_sample_input)

        elif self.selected_method == 5:  # НОВЫЙ МЕТОД 5
            # TODO: Добавить дополнительные параметры для метода 5
            self.special_param = WidgetFactory.create_input("Специальный параметр")
            layout.addRow("Специальный параметр:", self.special_param)

        elif self.selected_method == 6:  # НОВЫЙ МЕТОД 6
            # TODO: Добавить дополнительные параметры для метода 6
            self.advanced_param = WidgetFactory.create_input("Продвинутый параметр")
            layout.addRow("Продвинутый параметр:", self.advanced_param)

        # Environmental parameters (общие для всех)
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
        # Clear inputs based on selected method
        self.sample_name_input.clear()
        self.measurements_count.setValue(1)
        self.operator_input.clear()
        self.comments_input.clear()

        if hasattr(self, 'thickness_input'):
            self.thickness_input.clear()
        if hasattr(self, 'piston_move_input'):
            self.piston_move_input.clear()
        if hasattr(self, 'radius_input'):
            self.radius_input.clear()
        if hasattr(self, 'mp_input'):
            self.mp_input.clear()

        # Clear additional parameters
        if hasattr(self, 'd_res_input'):
            self.d_res_input.clear()
        if hasattr(self, 'h_res_input'):
            self.h_res_input.clear()
        if hasattr(self, 'd_sample_input'):
            self.d_sample_input.clear()

        self.temp_input.clear()
        self.humidity_input.clear()

    def start_measurement(self):
        """Start the measurement process"""
        # Collect data from form
        measurement_data = self.collect_measurement_data()

        # Call backend to create measurement
        response = self.backend.ferro_query("new_create", measurement_data)

        if response and 'id' in response:
            # Show measurement process dialog
            from dialogs.measurement_process import MeasurementProcessDialog
            process_dialog = MeasurementProcessDialog(self.backend, response['id'], self)
            process_dialog.exec()

            # После завершения измерения можно вернуться на главную страницу
            # или оставить пользователя на этой странице для создания нового измерения
            self.clear_form()

    def collect_measurement_data(self):
        """Collect measurement data from form"""
        data = {
            "method": self.selected_method,
            "sample_name": self.sample_name_input.text() or "Образец 1",
            "measurements_count": self.measurements_count.value(),
            "operator": self.operator_input.text() or "Оператор",
            "temperature": float(self.temp_input.text() or "25.0"),
            "humidity": float(self.humidity_input.text() or "50.0"),
            "comments": self.comments_input.text(),
            "data": {
                str(self.selected_method): {}
            }
        }

        # Method-specific data
        if self.selected_method == 1:  # ФРЧ
            data["data"][str(self.selected_method)] = {
                "t": self.thickness_input.text() or "2.5",
                "del_L": self.piston_move_input.text() or "10.0",
                "index": self.index_combo.currentText() if hasattr(self, 'index_combo') else "2",
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "50.0",
                "h_res": self.h_res_input.text() if hasattr(self, 'h_res_input') else "90.0"
            }
        elif self.selected_method == 2:  # ФРД
            data["data"][str(self.selected_method)] = {
                "t": self.thickness_input.text() or "2.5",
                "index": self.index_combo.currentText() if hasattr(self, 'index_combo') else "2",
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "45.0",
                "h_res": self.h_res_input.text() if hasattr(self, 'h_res_input') else "45.0"
            }
        elif self.selected_method == 3:  # СО
            data["data"][str(self.selected_method)] = {
                "d": self.radius_input.text() or "5.0",
                "index": self.index_combo.currentText() if hasattr(self, 'index_combo') else "1",
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "22.5",
                "h_res": self.h_res_input.text() if hasattr(self, 'h_res_input') else "45.0"
            }
        elif self.selected_method == 4:  # СВЧФ
            form_value = "1"
            if hasattr(self, 'form_combo'):
                form_value = "1" if self.form_combo.currentText() == "Стержень" else "0"

            data["data"][str(self.selected_method)] = {
                "form": form_value,
                "mp": self.mp_input.text() if hasattr(self, 'mp_input') else "0.5",
                "d_res": self.d_res_input.text() if hasattr(self, 'd_res_input') else "11.0",
                "d_sample": self.d_sample_input.text() if hasattr(self, 'd_sample_input') else "0.81"
            }
        elif self.selected_method == 5:  # НОВЫЙ МЕТОД 5
            data["data"][str(self.selected_method)] = {
                "param1": self.param1_input.text() if hasattr(self, 'param1_input') else "",
                "param2": self.param2_input.text() if hasattr(self, 'param2_input') else "",
                "special_param": self.special_param.text() if hasattr(self, 'special_param') else ""
            }
        elif self.selected_method == 6:  # НОВЫЙ МЕТОД 6
            data["data"][str(self.selected_method)] = {
                "paramA": self.paramA_input.text() if hasattr(self, 'paramA_input') else "",
                "paramB": self.paramB_input.text() if hasattr(self, 'paramB_input') else "",
                "advanced_param": self.advanced_param.text() if hasattr(self, 'advanced_param') else ""
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