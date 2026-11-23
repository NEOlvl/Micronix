"""Метод фиксированной длины (МФД) — ГОСТ Р 8.623-2015.

Перенос Methot_Nikita из All_Methods_3.py с исправлениями:
- Д-1: результат — MethodResult с errors[], а не всегда "ok"
- Д-2: добротность с образцом QE = fE/(f2E - f1E) — по собственной
  полосе нагруженного резонанса, а не по полосе пустого
- Д-3: корень уравнения — скобочный поиск наименьшего положительного
  корня (устаревший fsolve(..., x0=1) сходился на нефизичные ветви)
"""

import math
from typing import Dict

from .base import (CalculationError, Method, MethodInput, MethodResult,
                   ResonanceChannels)
from .const import C, EB, E_RANGE, F_RANGE, P_WAVE, TGO_RANGE, V11
from .res_x import solve_tan_over_x


class FixedLengthMethod(Method):
    id = 'mfd'
    name = 'Метод фиксированной длины (МФД)'
    standard = 'ГОСТ Р 8.623-2015'
    description = (
        'Резонатор H01 фиксированной длины: резонансные частоты '
        'измеряются без и с образцом внутри резонатора.')
    inputs = (
        MethodInput('t', 'Толщина образца', 'мм', (0.5, 6.0)),
        MethodInput('D', 'Диаметр резонатора', 'мм', (5.0, 200.0)),
        MethodInput('L0', 'Длина резонатора', 'мм', (10.0, 500.0)),
    )
    resonance_fields = ('f0', 'f1', 'f2', 'a0', 'fe', 'f1e', 'f2e', 'ae')

    def calculate(self, params: Dict,
                  resonance: ResonanceChannels) -> MethodResult:
        res = MethodResult()
        res.errors.extend(self.validate(params))
        res.errors.extend(resonance.require(*self.resonance_fields))
        if res.errors:
            return res

        v = self.get_values(params)
        t, D, L0 = v['t'], v['D'], v['L0']
        if not D > t:
            res.errors.append(
                f"Неподходящее значение D = {D:g} или t = {t:g}")
            return res
        f0, f1, f2, A0 = resonance.f0, resonance.f1, resonance.f2, resonance.a0
        fE, f1E, f2E, AE = resonance.fe, resonance.f1e, resonance.f2e, resonance.ae
        if not (F_RANGE[0] <= f0 <= F_RANGE[1]):
            res.errors.append(
                f"Неподходящая частота без образца f0 = {f0:.6g} Гц")
            return res

        try:
            a = 0.5 * D
            k2 = 2.0 * math.pi * fE * math.sqrt(EB) / C
            h2 = math.sqrt(k2 ** 2 - (V11 / a) ** 2)
            drob = math.tan(h2 * (L0 + t)) / (h2 * t)
            x = solve_tan_over_x(drob)
            E = (C / (2.0 * math.pi * fE)) ** 2 * \
                ((x / t) ** 2 + (V11 / a) ** 2)

            ksi = math.sin(x) ** 2 / math.sin(h2 * (L0 - t)) ** 2
            F1 = 1.0 - math.sin(2.0 * x) / (2.0 * x)
            F2 = 1.0 - math.sin(2.0 * h2 * (L0 - t)) / (2.0 * h2 * (L0 - t))
            K1E = 1.0 / (1.0 + ksi * (L0 - t) * F2 / (E * t * F1))
            G = a * L0 / ((2.0 * a - L0) *
                          (P_WAVE * C / (2.0 * L0 * f0 * math.sqrt(EB))) ** 2
                          + L0)
            nu1 = G * math.sqrt(f0 / fE) * (V11 / (k2 * a)) ** 2
            nu2 = ((x / V11) ** 2 * (a / t) ** 2 + t * F1 / a
                   + ksi * ((h2 * a / V11) ** 2 + (L0 - t) * F2 / a))
            nu3 = E * t * F1 + ksi * (L0 - t) * F2
            nu = nu1 * nu2 / nu3
        except (CalculationError, ValueError, ZeroDivisionError,
                OverflowError) as exc:
            res.errors.append(f"Ошибка расчёта: {exc}")
            return res

        # Д-2: нагруженная добротность — по полосе кривой с образцом
        Q0 = f0 / (f2 - f1)
        QE = fE / (f2E - f1E)
        Q00 = Q0 / (1.0 - 10.0 ** (0.05 * A0))
        Q0E = QE / (1.0 - 10.0 ** (0.05 * AE))
        tgo = (1.0 / K1E) * (1.0 / Q0E - nu / Q00)

        if not (E_RANGE[0] <= E <= E_RANGE[1]):
            res.errors.append(
                f"Неподходящая диэлектрическая проницаемость E = {E:.6g}")
        if not (TGO_RANGE[0] <= tgo <= TGO_RANGE[1]):
            res.errors.append(
                "Неподходящий тангенс угла диэлектрических потерь "
                f"tgo = {tgo:.6g}")

        res.values = {'E': E, 'tgo': tgo, 'Q0': Q0, 'QE': QE,
                      'x': x, 'K1E': K1E}
        return res


METHOD = FixedLengthMethod()
