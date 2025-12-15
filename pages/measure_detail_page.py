"""
Measure detail page - optimized version
"""

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QSplitter, QTableWidgetItem)
from pages.base_page import BasePage
from widget_factory import WidgetFactory
from widgets import HeaderWidget, MeasurementGraphWidget, ResultsTableWidget
from styles import Styles


class MeasureDetailPage(BasePage):
    """Detailed measurement view page - optimized"""

    def __init__(self, backend, parent=None):
        super().__init__("", "", parent)
        self.backend = backend
        self.current_measure_id = None

        # Clear default layout
        self.clear_layout()

        # Setup UI
        self.setup_custom_header()
        self.setup_content_area()

    def clear_layout(self):
        """Clear the default layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def setup_custom_header(self):
        """Setup custom header"""
        self.header = HeaderWidget("Измерения", "", self)
        self.header.new_measure_btn.setText("Настройки")
        self.layout.addWidget(self.header)

    def setup_content_area(self):
        """Setup content area with graph and table"""
        # Create main content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)

        # Title and info section
        self.setup_title_section(content_layout)

        # Graph and info splitter
        self.setup_graph_section(content_layout)

        # Results table
        self.setup_results_table(content_layout)

        self.layout.addWidget(content)

    def setup_title_section(self, parent_layout):
        """Setup title and measurement info"""
        title_section = QVBoxLayout()
        title_section.setSpacing(8)

        self.measure_title = WidgetFactory.create_title("Вычисление #...", level=1)
        self.measure_info = WidgetFactory.create_label(
            "CABAN R180 • RESONATOR 1 • 20.10.2024 17:56:46",
            color=Styles.TEXT_SECONDARY,
            font_size=14
        )

        title_section.addWidget(self.measure_title)
        title_section.addWidget(self.measure_info)

        parent_layout.addLayout(title_section)

    def setup_graph_section(self, parent_layout):
        """Setup graph and side info splitter"""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Graph area
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)

        self.graph = MeasurementGraphWidget()
        self.graph.plot_widget.setBackground(Styles.BACKGROUND_DARK)
        graph_layout.addWidget(self.graph)

        splitter.addWidget(graph_container)

        # Side info panel
        info_container = self.create_info_panel()
        splitter.addWidget(info_container)

        # Set initial sizes
        splitter.setSizes([700, 300])

        parent_layout.addWidget(splitter, 1)

    def create_info_panel(self):
        """Create side info panel"""
        from widgets import ModernCard

        panel = ModernCard()
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(400)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)

        # Title
        info_title = WidgetFactory.create_title("Информация об измерении", level=2)
        panel_layout.addWidget(info_title)

        # Scrollable info content
        scroll_area = WidgetFactory.create_scroll_area()
        self.info_content = QWidget()
        self.info_layout = QVBoxLayout(self.info_content)
        self.info_layout.setSpacing(15)
        self.info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.info_content)
        panel_layout.addWidget(scroll_area, 1)

        return panel

    def setup_results_table(self, parent_layout):
        """Setup results table section"""
        # Section title
        results_label = WidgetFactory.create_title("Результаты вычислений", level=2)
        parent_layout.addWidget(results_label)

        # Create table
        self.results_table = ResultsTableWidget()
        parent_layout.addWidget(self.results_table, 1)

    def load_measurement(self, measure_id):
        """Load measurement data"""
        self.current_measure_id = measure_id
        data = self.backend.ferro_query("read_data", {"id_m": measure_id})

        if not data:
            return

        # Update title and info
        self.update_measurement_info(data)

        # Update graph
        self.update_graph(data)

        # Update info panel
        self.update_info_panel(data)

        # Update results table
        self.update_results_table(data)

    def update_measurement_info(self, data):
        """Update measurement title and info"""
        self.measure_title.setText(f"Вычисление #{data.get('title', 'Unknown')}")

        time_info = data.get('time', 'Unknown')
        self.measure_info.setText(f"CABAN R180 • RESONATOR 1 • {time_info}")

    def update_graph(self, data):
        """Update graph with measurement data"""
        self.graph.plot_widget.clear()

        # Plot baseline data
        x_data = np.array(data['x'])
        y_data = np.array(data['y_res'])
        self.graph.plot_data(x_data, y_data, Styles.PRIMARY, 2, "Без образца")

        # Plot samples
        if data.get('y_samples'):
            for sample_idx, sample in data['y_samples'].items():
                sample_y = np.array(sample['y_res'])
                self.graph.plot_data(x_data, sample_y, Styles.SECONDARY, 2, sample['name'])

    def update_info_panel(self, data):
        """Update the information panel"""
        # Clear existing content
        for i in reversed(range(self.info_layout.count())):
            item = self.info_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Baseline info
        baseline_title = WidgetFactory.create_label("Без образца", level=3)
        self.info_layout.addWidget(baseline_title)

        # Add sample info
        if data.get('y_samples'):
            for sample_idx, sample in data['y_samples'].items():
                sample_title = WidgetFactory.create_label(sample['name'], level=3)
                sample_title.setStyleSheet("margin-top: 15px;")
                self.info_layout.addWidget(sample_title)

                # Sample details
                details_text = f"""
                F₀: 9.87 ГГц
                Q: 789
                Толщина: 2.5 мм
                """

                details_label = WidgetFactory.create_label(
                    details_text.strip(),
                    color=Styles.TEXT_SECONDARY,
                    font_size=13
                )
                self.info_layout.addWidget(details_label)

        self.info_layout.addStretch()

    def update_results_table(self, data):
        """Update the results table"""
        self.results_table.setRowCount(0)

        if not data.get('y_samples'):
            return

        for i, (sample_idx, sample) in enumerate(data['y_samples'].items(), 1):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            self.results_table.setItem(row, 0, QTableWidgetItem(str(i)))
            self.results_table.setItem(row, 1, QTableWidgetItem(sample['name']))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{sample['tgo']:.8f}"))
            self.results_table.setItem(row, 3, QTableWidgetItem(f"{sample['E']:.3f}"))
            self.results_table.setItem(row, 4, QTableWidgetItem("1 * 10^-4"))