"""Численные решатели трансцендентных уравнений резонаторных методов.

Д-3: при невозможности найти корень выбрасывается контролируемая
SolverError — никаких «значений по умолчанию» (устаревший код
возвращал math.pi при любой неудаче, что маскировало ошибку).
"""

import math

import scipy.optimize
from scipy.special import jv, jn_zeros

from .base import SolverError


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


def solve_for_x_1(h2: float, t: float, L: float = 40.0) -> float:
    """Решение уравнения cot(x/2)/(x/2) - 2*tan(h2*L)/(h2*t) = 0.

    Args:
        h2: продольное волновое число заполненной части, 1/мм.
        t: толщина образца, мм.
        L: длина заполненной части резонатора, мм.

    Returns:
        Наименьший положительный корень x, рад.
    """
    return _solve_cot_over(2.0 * math.tan(h2 * L) / (h2 * t))


def solve_for_x_2(beta2: float, t: float, L: float = 40.0) -> float:
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
