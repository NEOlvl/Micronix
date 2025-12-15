"""
Pages package
"""

from .home_page import HomePage
from .measures_page import MeasuresPage
from .measure_detail_page import MeasureDetailPage
from .reports_page import ReportsPage
from .settings_page import SettingsPage
from .new_measurement_page import NewMeasurementPage  # Добавляем

__all__ = [
    'HomePage',
    'MeasuresPage',
    'MeasureDetailPage',
    'ReportsPage',
    'SettingsPage',
    'NewMeasurementPage'  # Добавляем
]