# widgets/__init__.py
from .modern_card import ModernCard
from .header import HeaderWidget
from .animated_button import AnimatedButton
from .gradient_background import GradientBackground
from .measurement_graph import MeasurementGraphWidget
from .results_table import ResultsTableWidget
from .loading_spinner import LoadingSpinner
from .method_card import MethodCard  # Добавляем новый импорт

__all__ = [
    'ModernCard',
    'HeaderWidget',
    'AnimatedButton',
    'GradientBackground',
    'MeasurementGraphWidget',
    'ResultsTableWidget',
    'LoadingSpinner',
    'MethodCard',  # Добавляем в список
]