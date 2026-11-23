"""Оффскрин-скриншоты страниц приложения для проверки дизайна."""
import os
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from styles import apply_theme

app = QApplication(sys.argv)
app.setStyle("Fusion")
apply_theme(app)

from main_window import MicronixMainWindow

win = MicronixMainWindow()
win.resize(1440, 900)
win.show()
app.processEvents()

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ui_shots')
os.makedirs(out, exist_ok=True)

pages = {
    'home': win.home_page,
    'new_measurement': win.new_measurement_page,
    'measures': win.measures_page,
    'reports': win.reports_page,
    'settings': win.settings_page,
}

for name, page in pages.items():
    win.page_stack.setCurrentWidget(page)
    app.processEvents()
    win.grab().save(os.path.join(out, f'{name}.png'))
    print('saved', name)

# Детальная страница с реальным измерением
measures = win.backend.query("measure_data", 0)
if measures:
    win.measure_detail_page.load_measurement(measures[-1]['id_m'])
    win.page_stack.setCurrentWidget(win.measure_detail_page)
    app.processEvents()
    win.grab().save(os.path.join(out, 'detail.png'))
    print('saved detail')

win.deleteLater()
