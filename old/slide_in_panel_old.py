"""
Slide-in panel widget - optimized version
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QSpinBox, QComboBox,
                             QFormLayout, QGroupBox)
from widget_factory import WidgetFactory
from widgets import ModernCard
from styles import Styles


class SlideInPanel(QWidget):
    """Slide-in panel for method selection and parameters - optimized"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        if parent and hasattr(parent, 'backend'):
            self.backend = parent.backend
        else:
            self.backend = None

        self.current_method_id = 1
        self.method_cards = []

        self.setup_ui()
        self.hide()

    def setup_ui(self):
        """Setup panel UI"""
        self.setFixedWidth(800)
        self.setStyleSheet(f"""
            SlideInPanel {{
                background: {Styles.BACKGROUND_DARK};
                border-left: 1px solid {Styles.BORDER_LIGHT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.setup_header(layout)

        # Content area
        self.setup_content_area(layout)

        # Footer
        self.setup_footer(layout)

        # Animation
        self.setup_animation()

    def setup_header(self, parent_layout):
        """Setup panel header"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            background: {Styles.BACKGROUND_LIGHT};
            border-bottom: 1px solid {Styles.BORDER_LIGHT};
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Breadcrumb
        self.breadcrumb = WidgetFactory.create_label("Бином / новое исследование")
        self.breadcrumb.setStyleSheet("font-size: 16px; font-weight: 600;")

        # Close button
        self.close_btn = WidgetFactory.create_button("×", style="secondary")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: bold;
            }
        """)
        self.close_btn.clicked.connect(self.hide_panel)

        header_layout.addWidget(self.breadcrumb)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)

        parent_layout.addWidget(header)

    def setup_content_area(self, parent_layout):
        """Setup scrollable content area"""
        self.scroll_area = WidgetFactory.create_scroll_area()

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)

        self.scroll_area.setWidget(self.content_widget)
        parent_layout.addWidget(self.scroll_area, 1)

    def setup_footer(self, parent_layout):
        """Setup panel footer with action buttons"""
        footer = QWidget()
        footer.setFixedHeight(80)
        footer.setStyleSheet(f"""
            background: {Styles.BACKGROUND_LIGHT};
            border-top: 1px solid {Styles.BORDER_LIGHT};
        """)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)

        footer_layout.addStretch()

        # Action buttons
        self.clear_btn = WidgetFactory.create_button("Очистить всё", style="secondary")
        self.cancel_btn = WidgetFactory.create_button("Отмена", style="secondary")
        self.cancel_btn.clicked.connect(self.hide_panel)

        self.create_btn = WidgetFactory.create_button("Начать исследование", style="primary")
        self.create_btn.clicked.connect(self.create_measurement)

        footer_layout.addWidget(self.clear_btn)
        footer_layout.addWidget(self.cancel_btn)
        footer_layout.addWidget(self.create_btn)

        parent_layout.addWidget(footer)

    def setup_animation(self):
        """Setup slide animation"""
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_panel(self, method_id=1):
        """Show panel with selected method"""
        # Clear content
        self.clear_content()

        # Set method
        self.current_method_id = method_id

        # Add content
        self.add_method_selection()
        self.add_method_parameters(method_id)

        # Position and show
        self.position_panel()
        self.show()
        self.slide_in()

    def clear_content(self):
        """Clear panel content"""
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.method_cards = []

    def add_method_selection(self):
        """Add method selection section"""
        section = self.create_section_card("Метод исследования")

        # Method cards grid
        methods_grid = QHBoxLayout()
        methods_grid.setSpacing(16)

        # Method definitions
        methods = [
            (1, "ФРЧ", "Метод фиксированной частоты"),
            (2, "ФРД", "Метод фиксированной длины"),
            (3, "СО", "Метод для стержневых образцов"),
            (4, "СВЧФ", "Метод для СВЧ ферритов")
        ]

        # Create method cards
        for m_id, m_name, m_desc in methods:
            card = self.create_method_card(m_id, m_name, m_desc)
            methods_grid.addWidget(card)

        section.layout().addLayout(methods_grid)
        self.content_layout.addWidget(section)

    def create_method_card(self, method_id, method_name, description):
        """Create a method selection card"""
        from widgets import MethodCard

        card = MethodCard(method_id, method_name, description)

        # Highlight selected method
        if method_id == self.current_method_id:
            card.setStyleSheet(Styles.create_card_style(
                background="rgba(40, 41, 44, 0.9)",
                border="rgba(120,121,241,0.4)"
            ))

        # Connect click event
        card.mousePressEvent = lambda event, mid=method_id: self.select_method(mid)

        self.method_cards.append(card)
        return card

    def add_method_parameters(self, method_id):
        """Add parameters for selected method"""
        section = self.create_section_card(f"Данные для исследования #{method_id}")

        # Create parameter form based on method
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(20)

        # Store input fields
        self.input_fields = {}

        # Method-specific parameters
        params = self.get_method_parameters(method_id)

        for label_text, widget_config in params:
            label = WidgetFactory.create_label(label_text, color=Styles.TEXT_SECONDARY)
            field = self.create_input_field(widget_config)

            form_layout.addRow(label, field)

            # Store reference
            field_name = label_text.split(",")[0].lower().replace(" ", "_").replace(":", "")
            self.input_fields[field_name] = field

        section.layout().addLayout(form_layout)

        # Add additional parameters if needed
        self.add_additional_parameters(method_id, section)

        self.content_layout.addWidget(section)

    def get_method_parameters(self, method_id):
        """Get parameters for specific method"""
        params_map = {
            1: [
                ("Толщина образца, мм:", {"type": "line_edit", "placeholder": ""}),
                ("Перемещение поршня, мм:", {"type": "line_edit", "placeholder": ""}),
                ("Кол-во измерений:", {"type": "spinbox", "value": 1}),
            ],
            2: [
                ("Толщина образца, мм:", {"type": "line_edit", "placeholder": ""}),
                ("Кол-во измерений:", {"type": "spinbox", "value": 1}),
            ],
            3: [
                ("Радиус образца, мм:", {"type": "line_edit", "placeholder": ""}),
                ("Кол-во измерений:", {"type": "spinbox", "value": 1}),
            ],
            4: [
                ("Форма образца:", {"type": "combo", "items": ["Стержень", "Квадратная"]}),
                ("Поперечная составляющая МП:", {"type": "line_edit", "placeholder": ""}),
                ("Кол-во измерений:", {"type": "spinbox", "value": 1}),
            ]
        }

        return params_map.get(method_id, [])

    def create_input_field(self, config):
        """Create input field based on configuration"""
        field_type = config.get("type", "line_edit")

        if field_type == "line_edit":
            field = WidgetFactory.create_input(config.get("placeholder", ""))
        elif field_type == "spinbox":
            field = QSpinBox()
            field.setValue(config.get("value", 0))
            field.setStyleSheet(Styles.INPUT_FIELD)
        elif field_type == "combo":
            field = QComboBox()
            field.addItems(config.get("items", []))
            field.setStyleSheet(Styles.INPUT_FIELD)
        else:
            field = WidgetFactory.create_input()

        return field

    def add_additional_parameters(self, method_id, section):
        """Add additional parameters group"""
        if method_id in [1, 2, 3]:
            group = self.create_parameters_group("Дополнительные параметры исследования")

            group_layout = QFormLayout()
            group_layout.setVerticalSpacing(10)

            # Common additional parameters
            index_combo = QComboBox()
            index_combo.addItems(["2", "3", "4", "5"])
            index_combo.setCurrentText("2")
            index_combo.setStyleSheet(Styles.INPUT_FIELD)

            d_res_input = WidgetFactory.create_input("50")
            d_res_input.setReadOnly(True)

            h_res_input = WidgetFactory.create_input("90")

            group_layout.addRow("Продольный индекс колебаний:", index_combo)
            group_layout.addRow("Диаметр резонатора, мм:", d_res_input)
            group_layout.addRow("Высота резонатора, мм:", h_res_input)

            # Store references
            self.input_fields["index"] = index_combo
            self.input_fields["d_res"] = d_res_input
            self.input_fields["h_res"] = h_res_input

            group.setLayout(group_layout)
            section.layout().addWidget(group)

    def create_section_card(self, title):
        """Create a section card"""
        card = ModernCard()
        card.setStyleSheet(Styles.create_card_style(
            background="rgba(40, 41, 44, 0.6)"
        ))

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Section title
        title_label = WidgetFactory.create_label(title, level=2)
        layout.addWidget(title_label)

        return card

    def create_parameters_group(self, title):
        """Create a parameters group box"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {Styles.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                background: rgba(30, 31, 34, 0.6);
                border: 1px solid {Styles.BORDER_MEDIUM};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
            }}
        """)

        return group

    def select_method(self, method_id):
        """Select another method"""
        # Update card styles
        for card in self.method_cards:
            if card.method_num == method_id:
                card.setStyleSheet(Styles.create_card_style(
                    background="rgba(40, 41, 44, 0.9)",
                    border="rgba(120,121,241,0.4)"
                ))
            else:
                card.setStyleSheet(Styles.create_card_style())

        # Remove old parameters and add new ones
        for i in reversed(range(self.content_layout.count())):
            if i > 0:  # Keep method selection section
                item = self.content_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()

        self.current_method_id = method_id
        self.add_method_parameters(method_id)

    def position_panel(self):
        """Position panel correctly"""
        parent_width = self.parent_widget.width()
        parent_height = self.parent_widget.height()

        self.setFixedSize(800, parent_height)
        self.move(parent_width, 0)

    def slide_in(self):
        """Animate panel slide in"""
        parent_width = self.parent_widget.width()

        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(
            parent_width - self.width(),
            0
        ))
        self.animation.start()

    def hide_panel(self):
        """Hide panel with animation"""
        parent_width = self.parent_widget.width()

        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(QPoint(parent_width, 0))
        self.animation.finished.connect(lambda: self.hide())
        self.animation.start()

    def create_measurement(self):
        """Create new measurement from panel data"""
        from dialogs.measurement_process import MeasurementProcessDialog

        # Collect data from form
        data_obj = self.collect_form_data()

        # Call backend
        response = self.backend.ferro_query("new_create", data_obj)

        # Hide panel
        self.hide_panel()

        # Start measurement process
        if response and 'id' in response:
            self.measurement_process = MeasurementProcessDialog(
                self.backend,
                response['id'],
                self.parent_widget
            )
            self.measurement_process.show()

    def collect_form_data(self):
        """Collect data from form fields"""
        method_id = self.current_method_id
        data_obj = {
            "method": method_id,
            "data": {
                str(method_id): {}
            }
        }

        # Helper function to safely get values
        def get_value(field_name, default=""):
            field = self.input_fields.get(field_name)
            if not field:
                return default

            if isinstance(field, QLineEdit):
                return field.text()
            elif isinstance(field, QSpinBox):
                return field.value()
            elif isinstance(field, QComboBox):
                return field.currentText()
            return default

        # Method 1: ФРЧ
        if method_id == 1:
            data_obj["data"][str(method_id)] = {
                "t": get_value("толщина_образца"),
                "del_L": get_value("перемещение_поршня"),
                "n": get_value("кол-во_измерений", 1),
                "index": get_value("index", "2"),
                "d_res": get_value("d_res", "50"),
                "h_res": get_value("h_res", "90")
            }

        # Method 2: ФРД
        elif method_id == 2:
            data_obj["data"][str(method_id)] = {
                "t": get_value("толщина_образца"),
                "n": get_value("кол-во_измерений", 1),
                "index": get_value("index", "2"),
                "d_res": get_value("d_res", "45"),
                "h_res": get_value("h_res", "45")
            }

        # Method 3: СО
        elif method_id == 3:
            data_obj["data"][str(method_id)] = {
                "d": get_value("радиус_образца"),
                "n": get_value("кол-во_измерений", 1),
                "index": get_value("index", "1"),
                "d_res": get_value("d_res", "22.5"),
                "h_res": get_value("h_res", "45")
            }

        # Method 4: СВЧФ
        elif method_id == 4:
            form_value = "1" if get_value("форма_образца") == "Стержень" else "0"

            data_obj["data"][str(method_id)] = {
                "form": form_value,
                "mp": get_value("поперечная_составляющая_мп"),
                "ism": get_value("кол-во_измерений", 1),
                "d_res": get_value("d_res", "11"),
                "d_sample": get_value("d_sample", "0.81")
            }

        # Default for unknown methods
        else:
            data_obj["data"][str(method_id)] = {
                "n": get_value("кол-во_измерений", 1)
            }

        return data_obj