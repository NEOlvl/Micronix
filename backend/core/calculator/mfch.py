"""Метод фиксированной частоты (МФЧ) — ГОСТ Р 8.623-2015.

Перенос Methot_Vlad из All_Methods_3.py с исправлениями:
- Д-1: результат — MethodResult с errors[], а не всегда "ok"
- Д-2: добротность с образцом QE = fE/(f2E - f1E) — по собственной
  полосе нагруженного резонанса, а не по полосе пустого
- Д-3: корень уравнения — скобочный поиск наименьшего положительного
  корня (устаревший fsolve(..., x0=1) сходился на нефизичные ветви)
- Д-12: параметр eta по ф.(7.8) — в легаси потерян знаменатель
  [E*t*F1 + ksi*(LE-t)*F2] и скобки (v11/(k2*a))^2
- Д-13: знак правой части уравнения (7.2): tgx/x - tg[h2*(delL+t)]/(h2t)=0,
  в легаси решалось tgx/x + drob = 0
"""

import math
from typing import Dict

from .base import (CalculationError, Method, MethodInput, MethodResult,
                   ResonanceChannels)
from .const import C, EB, E_RANGE, F_RANGE, TGO_RANGE, V11
from .res_x import solve_tan_over_x


class FixedFrequencyMethod(Method):
    id = 'mfch'
    name = 'Метод фиксированной частоты (МФЧ)'
    standard = 'ГОСТ Р 8.623-2015'
    description = (
        'Перестройка резонатора H01 перемещением поршня: образец '
        'на подвижном поршне, смещение ΔL подбирается под резонанс '
        'на фиксированной частоте.')
    inputs = (
        MethodInput('t', 'Толщина образца', 'мм', (0.5, 6.0)),
        MethodInput('D', 'Диаметр резонатора', 'мм', (5.0, 200.0)),
        MethodInput('L0', 'Длина резонатора', 'мм', (10.0, 500.0)),
        MethodInput('delL', 'Смещение поршня', 'мм', (0.0, 100.0)),
        MethodInput('p', 'Продольный индекс колебания H01p', '',
                    (2.0, 5.0), default=2.0),
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
        t, D, L0, delL, p = v['t'], v['D'], v['L0'], v['delL'], v['p']
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
            k2 = 2.0 * math.pi * f0 * math.sqrt(EB) / C
            h2 = math.sqrt(k2 ** 2 - (V11 / a) ** 2)
            # Д-13: ур.(7.2) tgx/x - tg[h2*(delL+t)]/(h2*t) = 0
            drob = -math.tan(h2 * (delL + t)) / (h2 * t)
            x = solve_tan_over_x(drob)
            E = (C / (2.0 * math.pi * f0)) ** 2 * \
                ((x / t) ** 2 + (V11 / a) ** 2)

            LE = L0 - delL
            F1 = 1.0 - math.sin(2.0 * x) / (2.0 * x)
            F2 = 1.0 - math.sin(2.0 * h2 * (LE - t)) / (2.0 * h2 * (LE - t))
            ksi = math.sin(x) ** 2 / math.sin(h2 * (LE - t)) ** 2
            K1E = 1.0 / (1.0 + ksi * (LE - t) * F2 / (E * t * F1))
            G = a * L0 / ((2.0 * a - L0) *
                          (p * C / (2.0 * L0 * f0 * math.sqrt(EB))) ** 2
                          + L0)
            # Д-12: ф.(7.8) — числитель целиком делится на
            # [E*t*F1 + ksi*(LE-t)*F2]; (v11/(k2*a))^2
            nu = (G * (V11 / (k2 * a)) ** 2
                  * ((x / V11) ** 2 * (a / t) ** 2 + t * F1 / a
                     + ksi * ((h2 * a / V11) ** 2 + (LE - t) * F2 / a))
                  / (E * t * F1 + ksi * (LE - t) * F2))
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


METHOD = FixedFrequencyMethod()
