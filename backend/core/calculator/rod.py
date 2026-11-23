"""Метод стержневых образцов (СО) — ГОСТ Р 8.623-2015.

Перенос Methot_Marina из All_Methods_3.py с исправлениями:
- Д-1: результат — MethodResult с errors[], а не всегда "ok"
- Д-2: добротности выводятся из резонансных кривых: QE по собственной
  полосе нагруженного резонанса (в легаси передавались снаружи)
- Д-3: корень уравнения J1(x)/(x*J0(x)) — скобочный поиск по ветвям
  между нулями J0 (устаревший fsolve(..., x0=2) мог уйти на другую ветвь)
- Д-4: необъяснённый делитель E/3.2 вынесен в калибровочный параметр
  e_calibration (по умолчанию 1.0 — строго по ГОСТ; значение 3.2
  было эмпирической поправкой легаси без нормативного основания)
- Д-15: Z0(yb) = J0(yb) - [J1(yb)/N1(yb)]*N0(yb) — в легаси вместо
  J1(yb)/N1(yb) вычислялись J0(y*b^2)/N0(y*b^2)
- Д-17: продольный индекс p (h = p*pi/L) — входной параметр (1..3),
  в легаси был глобально зашит p=2
"""

import math
from typing import Dict

from scipy.special import jv, yn

from .base import (CalculationError, Method, MethodInput, MethodResult,
                   ResonanceChannels)
from .const import (C, EB, F_RANGE, SO_E_RANGE, SO_TGO_RANGE)
from .res_x import solve_bessel_ratio


class RodSampleMethod(Method):
    id = 'so'
    name = 'Метод стержневых образцов (СО)'
    standard = 'ГОСТ Р 8.623-2015'
    description = (
        'Цилиндрический резонатор H01 со стержневым образцом '
        'малого диаметра на оси резонатора.')
    inputs = (
        MethodInput('a', 'Радиус образца', 'мм', (1.5, 6.5)),
        MethodInput('R0', 'Радиус резонатора', 'мм', (5.0, 100.0)),
        MethodInput('L', 'Длина резонатора', 'мм', (10.0, 200.0)),
        MethodInput('p', 'Продольный индекс колебания H01p', '',
                    (1.0, 3.0), default=1.0),
        MethodInput('e_calibration', 'Калибровочный коэффициент ε '
                    '(в ГОСТ отсутствует)', '', (0.1, 10.0), default=1.0),
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
        a, R0, L = v['a'], v['R0'], v['L']
        p, e_cal = v['p'], v['e_calibration']
        f0, f1, f2, A0 = resonance.f0, resonance.f1, resonance.f2, resonance.a0
        fE, f1E, f2E, AE = resonance.fe, resonance.f1e, resonance.f2e, resonance.ae
        if not (F_RANGE[0] <= f0 <= F_RANGE[1]):
            res.errors.append(
                f"Неподходящая частота без образца f0 = {f0:.6g} Гц")
            return res

        try:
            D = 2.0 * R0
            d = 2.0 * a
            k2 = 2.0 * math.pi * fE * math.sqrt(EB) / C
            h = p * math.pi / L
            y = math.sqrt((k2 * a) ** 2 - (h * a) ** 2)
            b = D / d

            J1_yb = jv(1, y * b)
            N1_yb = yn(1, y * b)
            Z0_y = jv(0, y) - (J1_yb / N1_yb) * yn(0, y)
            Z1_y = jv(1, y) - (J1_yb / N1_yb) * yn(1, y)
            drobZ = Z1_y / (y * Z0_y)
            x = solve_bessel_ratio(drobZ)

            E_raw = (x ** 2 + (h * a) ** 2) / (k2 * a) ** 2
            E = E_raw / e_cal  # Д-4: калибровочный параметр вместо const 3.2

            k1 = 2.0 * math.pi * fE * math.sqrt(E_raw) / C
            Q0 = f0 / (f2 - f1)
            QE = fE / (f2E - f1E)
            Q00 = Q0 / (1.0 - 10.0 ** (0.05 * A0))
            Q0E = QE / (1.0 - 10.0 ** (0.05 * AE))

            J0_x, J1_x, J2_x = jv(0, x), jv(1, x), jv(2, x)
            J0_yb = jv(0, y * b)
            N0_yb = yn(0, y * b)
            # Д-15: Z0(yb) по ГОСТ — с тем же коэффициентом J1(yb)/N1(yb)
            Z0_yb = J0_yb - (J1_yb / N1_yb) * N0_yb
            Z2_y = jv(2, y) - (J1_yb / N1_yb) * yn(2, y)

            chisl_K1E = ((k2 * a) / y) ** 2 * (J0_x / Z0_y) ** 2 * \
                (b ** 2 * Z0_yb ** 2 - Z1_y ** 2 + Z0_y * Z2_y)
            znam_K1E = ((k1 * a) / x) ** 2 * (J1_x ** 2 - J0_x * J2_x)
            K1E = 1.0 / (1.0 + chisl_K1E / znam_K1E)

            Jx = J1_x ** 2 - J0_x * J2_x
            Zy = Z1_y ** 2 - Z0_y * Z2_y
            chisl_n = (f0 / fE) ** 1.5 * (D ** 2 * L / a ** 2) * \
                (J0_x / Z0_y) ** 2 * Z0_yb ** 2 \
                + ((h * a) / x) ** 2 * Jx \
                + ((h * a) / y) ** 2 * (J0_x / Z0_y) ** 2 * \
                (b ** 2 * Z0_yb ** 2 - Zy)
            znam_n = 4.0 * ((D - L) *
                            (p * C / (2.0 * L * f0 * math.sqrt(EB))) ** 2
                            + L) * (
                ((k1 * a) / x) ** 2 * Jx
                + ((k2 * a) / y) ** 2 * (J0_x / Z0_y) ** 2 *
                (b ** 2 * Z0_yb ** 2 - Zy))
            n = chisl_n / znam_n
            tgo = (1.0 / K1E) * (1.0 / Q0E - n / Q00)
        except (CalculationError, ValueError, ZeroDivisionError,
                OverflowError) as exc:
            res.errors.append(f"Ошибка расчёта: {exc}")
            return res

        if not (SO_E_RANGE[0] <= E <= SO_E_RANGE[1]):
            res.errors.append(f"Неподходящее значение E = {E:.6g}")
        if not (SO_TGO_RANGE[0] <= tgo <= SO_TGO_RANGE[1]):
            res.errors.append(
                f"Неподходящее значение tgo = {tgo:.6g}")

        res.values = {'E': E, 'E_raw': E_raw, 'tgo': tgo,
                      'Q0': Q0, 'QE': QE, 'x': x, 'K1E': K1E}
        return res


METHOD = RodSampleMethod()
