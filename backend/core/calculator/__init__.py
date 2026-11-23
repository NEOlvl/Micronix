"""Расчётные методы: контракт, решатели, реестр (ТЗ-2, ТЗ-3, ТЗ-6)."""

from .base import (CalculationError, Method, MethodInput, MethodResult,
                   ResonanceChannels, SolverError)
from .registry import get_method, list_methods

__all__ = [
    'CalculationError', 'SolverError', 'Method', 'MethodInput',
    'MethodResult', 'ResonanceChannels', 'get_method', 'list_methods',
]
