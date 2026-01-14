"""
Measurement graph widget - optimized for FERRO JSON data format
"""

import numpy as np
import pyqtgraph as pg
import json
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt, pyqtSignal


class MeasurementGraphWidget(QWidget):
    """Interactive measurement graph widget for FERRO data"""

    # Сигнал при выборе образца
    sample_selected = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None  # Полные данные JSON
        self.current_data = None  # Текущие отображаемые данные
        self.samples = {}  # Данные по образцам
        self.colors = [
            '#7879F1',  # Основной фиолетовый
            '#f8c33c',  # Желтый
            '#4CAF50',  # Зеленый
            '#FF6B6B',  # Красный
            '#2196F3',  # Синий
            '#9C27B0',  # Пурпурный
            '#FF9800',  # Оранжевый
            '#00BCD4'  # Голубой
        ]
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI with clean, readable design"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Панель управления
        self.setup_control_panel(layout)

        # График
        self.setup_graph_widget(layout)

        # Панель информации
        self.setup_info_panel(layout)

    def setup_control_panel(self, parent_layout):
        """Setup control panel for sample selection"""
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # Селектор образцов
        sample_label = QLabel("Образец:")
        sample_label.setStyleSheet("color: white; font-size: 14px; font-weight: 600;")

        self.sample_combo = QComboBox()
        self.sample_combo.setStyleSheet("""
            QComboBox {
                background: rgba(40, 41, 44, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: rgba(40, 41, 44, 0.95);
                color: white;
                selection-background-color: #7879F1;
            }
        """)
        self.sample_combo.currentTextChanged.connect(self.on_sample_changed)

        control_layout.addWidget(sample_label)
        control_layout.addWidget(self.sample_combo)
        control_layout.addStretch()

        parent_layout.addWidget(control_panel)

    def setup_graph_widget(self, parent_layout):
        """Setup the main graph widget with clean styling"""
        self.plot_widget = pg.PlotWidget(background=None)
        self.plot_widget.setAntialiasing(True)

        # Настройка фона и стилей
        self.plot_widget.setBackground('#1a1b1e')

        # Подписи осей - ЧИСТЫЕ И ПОНЯТНЫЕ
        styles = {
            'color': '#ffffff',
            'font-size': '13px',
            'font-family': 'Arial, sans-serif'
        }

        self.plot_widget.setLabel('left', 'Уровень, дБ', **styles)
        self.plot_widget.setLabel('bottom', 'Частота, ГГц', **styles)

        # ОЧЕНЬ ЛЕГКАЯ СЕТКА - минималистичная
        self.plot_widget.showGrid(x=True, y=True, alpha=0.05)

        # Цвета осей - тонкие светлые линии
        self.plot_widget.getPlotItem().getAxis('left').setPen(pg.mkPen(color='#666666', width=0.8))
        self.plot_widget.getPlotItem().getAxis('bottom').setPen(pg.mkPen(color='#666666', width=0.8))

        # Цвет текста на осях
        self.plot_widget.getPlotItem().getAxis('left').setTextPen('#ffffff')
        self.plot_widget.getPlotItem().getAxis('bottom').setTextPen('#ffffff')

        # Убираем рамку
        self.plot_widget.getPlotItem().getViewBox().setBorder(None)

        # Легенда - компактная
        self.plot_widget.addLegend(offset=(10, 10))
        self.legend = self.plot_widget.plotItem.legend
        if self.legend:
            self.legend.setBrush('#1a1b1ec0')
            self.legend.setPen(pg.mkPen(color='#ffffff40', width=1))
            self.legend.setLabelTextSize('10pt')

        parent_layout.addWidget(self.plot_widget, 1)

    def setup_info_panel(self, parent_layout):
        """Setup information panel for measurement details"""
        self.info_panel = QWidget()
        self.info_panel.setMaximumHeight(120)
        self.info_panel.setStyleSheet("""
            QWidget {
                background: rgba(30, 31, 34, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 15px;
            }
        """)

        self.info_layout = QHBoxLayout(self.info_panel)
        self.info_layout.setSpacing(20)

        # Будем заполнять динамически
        self.info_labels = {}

        parent_layout.addWidget(self.info_panel)

    def load_data_from_json(self, json_data):
        """Load data from FERRO JSON format"""
        try:
            if isinstance(json_data, str):
                self.data = json.loads(json_data)
            else:
                self.data = json_data

            # Очищаем предыдущие данные
            self.clear_plot()
            self.sample_combo.clear()
            self.samples.clear()

            # Извлекаем основные данные
            self.extract_main_data()

            # Извлекаем данные по образцам
            self.extract_sample_data()

            # Заполняем комбобокс
            self.populate_sample_combo()

            # Отображаем первый образец или базовую кривую
            if self.samples:
                first_sample = list(self.samples.keys())[0]
                self.display_sample(first_sample)
            else:
                self.display_baseline()

            return True

        except Exception as e:
            print(f"Error loading JSON data: {e}")
            return False

    def extract_main_data(self):
        """Extract main measurement data"""
        if not self.data:
            return

        # Основные данные (без образца)
        if 'x' in self.data and 'y_res' in self.data:
            self.baseline_data = {
                'frequencies': self.parse_frequencies(self.data['x']),
                'amplitudes': self.parse_amplitudes(self.data['y_res']),
                'name': 'Без образца',
                'color': '#7879F1'
            }

    def extract_sample_data(self):
        """Extract sample data from y_samples"""
        if not self.data or 'y_samples' not in self.data:
            return

        for sample_id, sample_data in self.data['y_samples'].items():
            if 'y_res' in sample_data and 'name' in sample_data:
                sample_name = sample_data['name']
                self.samples[sample_name] = {
                    'id': sample_id,
                    'frequencies': self.parse_frequencies(self.data['x']),
                    'amplitudes': self.parse_amplitudes(sample_data['y_res']),
                    'name': sample_name,
                    'color': self.colors[len(self.samples) % len(self.colors)],
                    'params': {
                        'fe': sample_data.get('fe', 'N/A'),
                        'AE': sample_data.get('AE', 'N/A'),
                        'E': sample_data.get('E', 'N/A'),
                        'tgo': sample_data.get('tgo', 'N/A')
                    }
                }

    def parse_frequencies(self, freq_list):
        """Convert frequency strings to GHz"""
        frequencies = []
        for freq_str in freq_list:
            try:
                # Преобразуем строку формата "+8.000000000E+09" в GHz
                freq_val = float(freq_str.replace('+', '').replace('E', 'e'))
                frequencies.append(freq_val / 1e9)  # Convert to GHz
            except:
                frequencies.append(0.0)
        return np.array(frequencies)

    def parse_amplitudes(self, amp_list):
        """Convert amplitude strings to floats"""
        amplitudes = []
        for amp_str in amp_list:
            try:
                amp_val = float(amp_str.replace('E', 'e'))
                amplitudes.append(amp_val)
            except:
                amplitudes.append(0.0)
        return np.array(amplitudes)

    def populate_sample_combo(self):
        """Populate sample selection combo box"""
        self.sample_combo.clear()

        # Добавляем базовое измерение
        if hasattr(self, 'baseline_data'):
            self.sample_combo.addItem("Без образца")

        # Добавляем образцы
        for sample_name in self.samples.keys():
            self.sample_combo.addItem(sample_name)

    def display_baseline(self):
        """Display baseline measurement"""
        if not hasattr(self, 'baseline_data'):
            return

        self.clear_plot()

        x = self.baseline_data['frequencies']
        y = self.baseline_data['amplitudes']

        # Построение графика
        pen = pg.mkPen(color=self.baseline_data['color'], width=2)
        self.plot_widget.plot(x, y, pen=pen, name=self.baseline_data['name'])

        # Находим резонанс (минимум амплитуды)
        if len(y) > 0:
            resonance_idx = np.argmin(y)
            resonance_freq = x[resonance_idx]
            resonance_amp = y[resonance_idx]

            # Добавляем маркер резонанса
            self.add_resonance_marker(resonance_freq, resonance_amp)

        # Обновляем информацию
        self.update_info_panel({
            'name': 'Без образца',
            'f0': f"{self.data.get('f0', 'N/A')}",
            'title': self.data.get('title', 'N/A'),
            'date': self.data.get('date', 'N/A'),
            'time': self.data.get('time', 'N/A')
        })

        # Автомасштабирование
        self.plot_widget.autoRange()

    def display_sample(self, sample_name):
        """Display specific sample data"""
        if sample_name not in self.samples:
            return

        sample = self.samples[sample_name]
        self.clear_plot()

        # Отображаем базовую кривую для сравнения
        if hasattr(self, 'baseline_data'):
            x_base = self.baseline_data['frequencies']
            y_base = self.baseline_data['amplitudes']
            pen_base = pg.mkPen(color=self.baseline_data['color'], width=1.5, style=Qt.PenStyle.DashLine)
            self.plot_widget.plot(x_base, y_base, pen=pen_base, name=self.baseline_data['name'])

        # Отображаем образец
        x = sample['frequencies']
        y = sample['amplitudes']

        pen = pg.mkPen(color=sample['color'], width=2)
        self.plot_widget.plot(x, y, pen=pen, name=sample['name'])

        # Находим резонанс
        if len(y) > 0:
            resonance_idx = np.argmin(y)
            resonance_freq = x[resonance_idx]
            resonance_amp = y[resonance_idx]

            # Добавляем маркер резонанса
            self.add_resonance_marker(resonance_freq, resonance_amp, sample['color'])

        # Обновляем информацию
        info_data = {
            'name': sample['name'],
            'fe': sample['params']['fe'],
            'AE': sample['params']['AE'],
            'E': sample['params']['E'],
            'tgo': sample['params']['tgo']
        }
        self.update_info_panel(info_data)

        # Эмитируем сигнал
        self.sample_selected.emit(sample_name, sample)

        # Автомасштабирование
        self.plot_widget.autoRange()

    def add_resonance_marker(self, freq, amp, color='#FF0000'):
        """Add resonance frequency marker"""
        # Маркер точки
        scatter = pg.ScatterPlotItem(
            x=[freq],
            y=[amp],
            pen=pg.mkPen(color=color, width=2),
            brush=pg.mkBrush(color=color + '80'),
            size=12,
            symbol='o'
        )
        self.plot_widget.addItem(scatter)

        # Текст с частотой резонанса
        freq_text = pg.TextItem(
            text=f'f₀ = {freq:.3f} ГГц',
            color=color,
            anchor=(0.5, 1),
            fill='#1a1b1e80'
        )
        freq_text.setPos(freq, amp)
        self.plot_widget.addItem(freq_text)

    def update_info_panel(self, info_data):
        """Update information panel with measurement details"""
        # Очищаем старые виджеты
        for i in reversed(range(self.info_layout.count())):
            item = self.info_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.info_labels.clear()

        # Создаем информационные блоки
        if 'name' in info_data:
            self.add_info_item("Образец:", info_data['name'], '#7879F1')

        if 'fe' in info_data:
            fe_val = float(info_data['fe'].replace('+', '').replace('E', 'e')) / 1e9
            self.add_info_item("Частота резонанса:", f"{fe_val:.3f} ГГц", '#4CAF50')

        if 'AE' in info_data:
            self.add_info_item("Амплитуда:", f"{float(info_data['AE']):.2f} дБ", '#f8c33c')

        if 'E' in info_data:
            self.add_info_item("Диэл. проницаемость:", f"{float(info_data['E']):.4f}", '#FF6B6B')

        if 'tgo' in info_data:
            self.add_info_item("Тангенс угла потерь:", f"{float(info_data['tgo']):.6f}", '#2196F3')

        if 'title' in info_data:
            self.add_info_item("Измерение:", info_data['title'], '#ffffff')

        if 'date' in info_data and 'time' in info_data:
            self.add_info_item("Дата/время:", f"{info_data['date']} {info_data['time']}", '#9C27B0')

    def add_info_item(self, label, value, color):
        """Add information item to panel"""
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)
        item_layout.setSpacing(2)
        item_layout.setContentsMargins(0, 0, 0, 0)

        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 11px;
                font-weight: 500;
            }}
        """)

        # Value
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 14px;
                font-weight: 600;
            }}
        """)

        item_layout.addWidget(label_widget)
        item_layout.addWidget(value_widget)

        self.info_layout.addWidget(item_widget)

    def clear_plot(self):
        """Clear all plots and markers"""
        self.plot_widget.clear()

        # Восстанавливаем легенду
        self.plot_widget.addLegend(offset=(10, 10))
        self.legend = self.plot_widget.plotItem.legend
        if self.legend:
            self.legend.setBrush('#1a1b1ec0')
            self.legend.setPen(pg.mkPen(color='#ffffff40', width=1))
            self.legend.setLabelTextSize('10pt')

    def on_sample_changed(self, sample_name):
        """Handle sample selection change"""
        if sample_name == "Без образца":
            self.display_baseline()
        elif sample_name in self.samples:
            self.display_sample(sample_name)

    def save_plot_image(self, filename):
        """Save plot as image"""
        try:
            self.plot_widget.grab().save(filename)
            return True
        except:
            return False

    def get_current_data(self):
        """Get currently displayed data"""
        return self.current_data