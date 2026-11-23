"""Численные решатели трансцендентных уравнений резонаторных методов.

Д-3: при невозможности найти корень выбрасывается контролируемая
SolverError — никаких «значений по умолчанию» (устаревший код
возвращал math.pi при любой неудаче, что маскировало ошибку).
"""

import math
from typing import Optional

import scipy.optimize
from scipy.special import jv, jn_zeros

from .base import CalculationError, SolverError
from .const import C, EB, V11


# Схемы включения резонатора в измерительной схеме (ТЗ2-4):
# 'through' — проходной резонатор, резонанс — пик |S21|;
# 'notch'   — резонатор-режектор, резонанс — провал.
# Фактическая схема установки не подтверждена заказчиком (вопрос 4.1
# ТЗ-2). ТЗ3-2: значения по умолчанию нет — неподтверждённый дефолт
# 'notch' менял tgδ измерений в десятки раз; схема обязана быть
# выбрана оператором явно (MicronixAPI.start_measurement).
SCHEMES = ('notch', 'through')

SCHEME_UNCONFIRMED = (
    'фактическая схема включения резонатора установки не '
    'подтверждена заказчиком (вопрос 4.1 ТЗ-2)')


def scheme_error(scheme) -> Optional[str]:
    """ТЗ3-2/ТЗ3-4: текст ошибки по scheme, либо None если допустимо.

    Неизвестное значение — контролируемая ошибка (устаревший код
    молча трактовал любое значение кроме 'through' как режектор).
    """
    s = str(scheme or '')
    if s in SCHEMES:
        return None
    return (
        'Схема включения резонатора не выбрана или неизвестна: '
        f'{scheme!r} — требуется явный выбор одной из {SCHEMES} '
        f'({SCHEME_UNCONFIRMED})')


def extraction_options(scheme: str) -> dict:
    """Параметры extract_resonance под схему включения резонатора.

    'through' — пик, полоса по ГОСТ прил. Г.3.1 ('gost');
    'notch' — провал, полоса половинной мощности от базовой линии
    ('half_power' — для глубокого провала уровень «min + 3.01 дБ»
    занижает полосу и завышает Q).
    """
    if scheme == 'through':
        return {'peak': 'peak', 'bandwidth': 'gost'}
    if scheme == 'notch':
        return {'peak': 'dip', 'bandwidth': 'half_power'}
    raise CalculationError(
        f'Неизвестная схема включения резонатора: {scheme!r} '
        f'(допустимы: {", ".join(SCHEMES)})')


def unloaded_q(q_loaded: float, a0_db: float, scheme: str,
               depth_db: Optional[float] = None) -> float:
    """Собственная добротность с поправкой на связь (ТЗ2-4, ТЗ3-1).

    'through' — Q0 = QL / (1 - |S21(f0)|), прил. Г.2 ГОСТ Р 8.623-2015
        (для пика передачи |S21(f0)| = 10^(A0/20), A0 < 0 — уровень
        относительно 0 дБ).
    'notch' — Q0 = QL / |S21min|; для режектора |S21min| = 1/(1+β)
        отсчитывается от базовой линии вне резонанса, поэтому
        поправка — по глубине провала: |S21min| = 10^(-depth_db/20)
        -> Q0 = QL * 10^(0.05*depth_db). ТЗ3-1: раньше использовался
        абсолютный уровень A0 — при базовой линии, отличной от 0 дБ,
        поправка (а значит Q00 и tgδ) завышалась.

    ТЗ3-4: неизвестное значение scheme — CalculationError.
    """
    if scheme == 'through':
        return q_loaded / (1.0 - 10.0 ** (0.05 * a0_db))
    if scheme == 'notch':
        if depth_db is None:
            raise CalculationError(
                'Поправка на связь режектора требует глубину провала '
                'относительно базовой линии (depth_db)')
        return q_loaded * 10.0 ** (0.05 * depth_db)
    raise CalculationError(
        f'Неизвестная схема включения резонатора: {scheme!r} '
        f'(допустимы: {", ".join(SCHEMES)})')


def resonator_f0_h01p(radius_mm: float, length_mm: float,
                      p: float) -> float:
    """Резонансная частота пустого цилиндрического резонатора H01p, Гц.

    k0^2 = (v11/R)^2 + (p*pi/L)^2,  f0 = k0*c / (2*pi*sqrt(EB)).
    Проверка геометрической согласованности (ТЗ2-1): метод корректен,
    только если пустой резонатор действительно резонирует на f0.
    """
    k0 = math.sqrt((V11 / radius_mm) ** 2
                   + (p * math.pi / length_mm) ** 2)
    return C * k0 / (2.0 * math.pi * math.sqrt(EB))


def geometry_consistency_warning(f0: float, radius_mm: float,
                                 length_mm: float, p: float,
                                 tolerance: float = 0.01) -> str:
    """Текст предупреждения о несогласованности геометрии (ТЗ2-1).

    Возвращает '', если расчётная f0 пустого резонатора H01p отличается
    от измеренной не более чем на tolerance.
    """
    f0_exp = resonator_f0_h01p(radius_mm, length_mm, p)
    dev = abs(f0_exp - f0) / f0
    if dev <= tolerance:
        return ''
    return (
        "Геометрия резонатора не согласована с измеренной частотой: "
        f"для моды H01{p:g} при R = {radius_mm:g} мм, "
        f"L = {length_mm:g} мм расчётная f0 = {f0_exp / 1e9:.4f} ГГц, "
        f"измеренная {f0 / 1e9:.4f} ГГц (расхождение {dev * 100:.1f} %)")


def _solve_cot_over(a_const: float) -> float:
    """Наименьший положительный корень cot(x/2)/(x/2) = a_const.

    На интервале (0, 2π) функция монотонно убывает от +∞ к -∞,
    корень существует и единствен для любого конечного A.
    """
    if not math.isfinite(a_const):
        raise SolverError(
            f"Некорректная правая часть уравнения: A={a_const}")

    def g(x):
        u = x / 2.0
        return math.cos(u) / (math.sin(u) * u) - a_const

    try:
        return scipy.optimize.brentq(g, 1e-9, 2.0 * math.pi - 1e-9,
                                     xtol=1e-14, rtol=1e-12)
    except (ValueError, RuntimeError) as exc:
        raise SolverError(
            f"Решение уравнения cot(x/2)/(x/2) = {a_const:.6g} "
            "не найдено") from exc


def solve_for_x_1(h2: float, t: float, L: float) -> float:
    """Решение уравнения cot(x/2)/(x/2) - 2*tan(h2*L)/(h2*t) = 0.

    Args:
        h2: продольное волновое число заполненной части, 1/мм.
        t: толщина образца, мм.
        L: длина заполненной части резонатора, мм.

    Returns:
        Наименьший положительный корень x, рад.
    """
    return _solve_cot_over(2.0 * math.tan(h2 * L) / (h2 * t))


def solve_for_x_2(beta2: float, t: float, L: float) -> float:
    """Решение уравнения cot(x/2)/(x/2) - 2*tanh(beta2*L)/(beta2*t) = 0.

    Ветвь для случая fE ниже частоты отсечки (затухающая волна).
    """
    return _solve_cot_over(2.0 * math.tanh(beta2 * L) / (beta2 * t))


def solve_tan_over_x(drob: float) -> float:
    """Наименьший положительный корень tan(x)/x + drob = 0.

    Уравнение методов МФЧ/МФД. tan(x)/x монотонна на каждой ветви
    между полюсами pi/2 + k*pi, поэтому сканируем ветви по возрастанию x.
    """
    if not math.isfinite(drob):
        raise SolverError(
            f"Некорректная правая часть уравнения: drob={drob}")

    def g(x):
        return math.tan(x) / x + drob

    delta = 1e-9
    # Ветвь (0, pi/2): tan/x >= 1, корень возможен при drob < -1
    if drob < -1.0:
        try:
            return scipy.optimize.brentq(g, delta, math.pi / 2 - delta)
        except ValueError:
            pass
    # Ветви (pi/2 + k*pi, 3pi/2 + k*pi): tan/x покрывает (-inf, +inf)
    for k in range(32):
        lo = math.pi / 2 + k * math.pi + delta
        hi = lo + math.pi - 2 * delta
        try:
            return scipy.optimize.brentq(g, lo, hi, xtol=1e-14, rtol=1e-12)
        except ValueError:
            continue
    raise SolverError(
        f"Решение уравнения tan(x)/x + {drob:.6g} = 0 не найдено")


def solve_bessel_ratio(target: float) -> float:
    """Наименьший положительный корень J1(x)/(x*J0(x)) = target.

    Уравнение метода стержневых образцов. Полюса функции — нули J0;
    сканируем ветви между ними по возрастанию x.
    """
    if not math.isfinite(target):
        raise SolverError(
            f"Некорректная правая часть уравнения: target={target}")

    def g(x):
        return jv(1, x) / (x * jv(0, x)) - target

    poles = jn_zeros(0, 16)
    eps = 1e-6
    segments = [(eps, poles[0] - eps)]
    segments += [(p + eps, pn - eps) for p, pn in zip(poles, poles[1:])]
    for lo, hi in segments:
        try:
            return scipy.optimize.brentq(g, lo, hi, xtol=1e-14, rtol=1e-12)
        except ValueError:
            continue
    raise SolverError(
        f"Решение уравнения J1(x)/(x*J0(x)) = {target:.6g} не найдено")
