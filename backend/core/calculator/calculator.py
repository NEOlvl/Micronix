import numpy as np
import math
from scipy.special import jv, yn
from scipy.optimize import fsolve


class DielectricCalculator:
    """Калькулятор диэлектрических параметров - все методы"""

    def __init__(self):
        self.c = 299.792458e9  # мм/с
        self.EB = 1.0006
        self.v11 = 3.831706
        self.p = 2

    def validate_params(self, method_name, params):
        """Валидация входных параметров"""
        validators = {
            'frequency_range': lambda f: 8e9 <= f <= 12e9,
            'thickness_check': lambda t, D: D > t,
            'epsilon_range': lambda E: 1.2 <= E <= 200,
            'tgo_range': lambda tgo: 5e-5 <= tgo <= 1e-2
        }
        # ... логика валидации ...
        return True

    def method_fixed_frequency(self, t, D, f0, f1, f2, fE, L0, delL, A0, AE):
        """Метод фиксированной частоты (бывший Methot_Vlad)"""
        # ... оптимизированный код ...
        return {'E': E, 'tgo': tgo}

    def method_fixed_length(self, t, D, L0, f0, f1, f2, fE, A0, AE):
        """Метод фиксированной длины (бывший Methot_Nikita)"""
        # ... оптимизированный код ...
        return {'E': E, 'tgo': tgo}

    def method_rod_samples(self, a, f0, f1, f2, fE, R0, L, A0, AE, Q0, QE):
        """Метод стержневых образцов (бывший Methot_Marina)"""
        # ... оптимизированный код ...
        return {'E': E_new, 'tgo': tgo_new}

    def method_ferrite_circular(self, a, b, r, R, f1, f1sh, deld, Ms):
        """Метод для ферритов (круглый образец)"""
        # ... оптимизированный код ...
        return {'E': Esh, 'tgo': Esh2 / Esh}

    def method_ferrite_general(self, fe, f0, f10, f20, f1e, f2e, R, r):
        """Общий метод для ферритов (бывший Method_real)"""
        # ... оптимизированный код ...
        return {'E': e_real, 'tgo': tgo}