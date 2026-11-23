"""
Measure detail page - optimized version
"""

import numpy as np
import pyqtgraph as pg
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
            role="subtitle"
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
        self.graph.setMinimumHeight(400)
        self.graph.plot_widget.setBackground(Styles.BACKGROUND_DARK)
        graph_layout.addWidget(self.graph)

        splitter.addWidget(graph_container)

        # Side info panel
        info_container = self.create_info_panel()
        splitter.addWidget(info_container)

        # Set initial sizes
        splitter.setSizes([700, 300])

        # График занимает основную часть высоты (3:1 к таблице)
        parent_layout.addWidget(splitter, 3)

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
        self.results_table.setMaximumHeight(180)
        parent_layout.addWidget(self.results_table, 1)

    def load_measurement(self, measure_id):
        """Load measurement data"""
        self.current_measure_id = measure_id
        data = self.backend.query("read_data", {"id_m": measure_id})

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
        if not self.graph.load_data_from_json(data):
            # fallback: базовая кривая напрямую (x в Гц -> ГГц)
            self.graph.plot_widget.clear()
            x_data = np.array(data['x'], dtype=float) / 1e9
            y_data = np.array(data['y_res'], dtype=float)
            self.graph.plot_widget.plot(
                x_data, y_data, pen=pg.mkPen(color='#7879F1', width=2),
                name='Без образца')
            for sample in (data.get('y_samples') or {}).values():
                self.graph.plot_widget.plot(
                    x_data, np.array(sample['y_res'], dtype=float),
                    pen=pg.mkPen(color='#FF8E53', width=2),
                    name=sample['name'])

    def update_info_panel(self, data):
        """Update the information panel"""
        # Clear existing content
        for i in reversed(range(self.info_layout.count())):
            item = self.info_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Baseline info
        baseline_title = WidgetFactory.create_label("Без образца", font_size=15, bold=True)
        self.info_layout.addWidget(baseline_title)

        # Add sample info
        if data.get('y_samples'):
            for sample_idx, sample in data['y_samples'].items():
                self.info_layout.addSpacing(10)
                sample_title = WidgetFactory.create_label(
                    str(sample.get('name') or sample_idx), role="h3")
                self.info_layout.addWidget(sample_title)

                # Sample details — реальные значения из записи
                fe = sample.get('fe')
                details_text = '\n'.join(filter(None, [
                    f"fE: {float(fe) / 1e9:.4f} ГГц" if fe else None,
                    f"E: {sample['E']:.4g}" if sample.get('E') is not None else None,
                    f"tg\u03b4: {sample['tgo']:.4g}" if sample.get('tgo') is not None else None,
                ])) or 'Нет данных'

                details_label = WidgetFactory.create_label(
                    details_text.strip(),
                    role="subtitle"
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

            tgo = sample.get('tgo')
            e_val = sample.get('E')
            self.results_table.setItem(row, 0, QTableWidgetItem(str(i)))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(sample.get('name') or i)))
            self.results_table.setItem(row, 2, QTableWidgetItem(
                f"{tgo:.8f}" if tgo is not None else '-'))
            self.results_table.setItem(row, 3, QTableWidgetItem(
                f"{e_val:.3f}" if e_val is not None else '-'))
            self.results_table.setItem(row, 4, QTableWidgetItem("1 * 10^-4"))