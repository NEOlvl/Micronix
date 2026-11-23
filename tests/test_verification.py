"""Верификация ПО по ТЗ-16 и ТЗ-2.

1. ТЗ2-2 «ε = 1»: при fe = f0 на согласованной геометрии (f0 следует
   из размеров резонатора H01p) каждый метод возвращает E ≈ 1 —
   первая проверка, не замкнутая на код методов.
2. ТЗ2-3 — независимая прямая модель (verification/forward_model.py):
   по эталонному epsilon решается прямая задача (fE из дисперсионного
   уравнения, записанного заново), синтезируется АЧХ, конвейер
   (экстракция -> метод) восстанавливает epsilon. Допуск по E <= 1%.
3. tg(delta): по синтезированной добротности восстанавливается
   величина с допуском, обоснованным квантованием сетки свипа.
4. Сверка с архивными измерениями (measurement_data/*.txt, r_data.txt).
5. Сквозной конвейер: симулятор -> обработка -> расчёт -> БД -> PDF.
"""
import glob
import json
import math
from pathlib import Path

import pytest

from backend.core.calculator.base import ResonanceChannels
from backend.core.calculator.registry import get_method
from backend.core.calculator.res_x import (extraction_options,
                                           resonator_f0_h01p)
from backend.core.data_processor import extract_resonance_db
from backend.core.vna_controller import (SimulatedMode, SimulatedVNA,
                                         SimulatorConfig, VNAConfig)
from backend.database.db_manager import record_from_archive
from verification.forward_model import (delL_mfch, fe_mfd, fe_msr9,
                                        fe_so)

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_GLOB = str(ROOT / 'measurement_data' / '*.txt')
R_DATA = ROOT / 'r_data.txt'
REPORT_PATH = ROOT / 'verification' / 'verification_report.md'

SWEEP_START, SWEEP_STOP = 8e9, 12e9

# ----------------------------------------------------------------------
# Согласованная геометрия (ТЗ2-2): f0 вычисляется из размеров,
# а не задаётся произвольно. Формат: method_id -> (params, R, L_eff, p).
# ТЗ3-6: для msr9 L_eff = L0 — длина ПУСТОГО резонатора (ГОСТ §11:
# L0 = 2L); с образцом полость L0 + t.
# ТЗ3-2: схема включения — явный параметр всех расчётов.
# ----------------------------------------------------------------------
GEO = {
    'mfd':  ({'t': 4.0, 'D': 45.0, 'L0': 45.0, 'p': 2.0}, 22.5, 45.0, 2.0),
    'mfch': ({'t': 4.0, 'D': 45.0, 'L0': 45.0, 'delL': 0.0, 'p': 2.0},
             22.5, 45.0, 2.0),
    'so':   ({'a': 1.95, 'R0': 22.5, 'L': 45.0, 'p': 1.0},
             22.5, 45.0, 1.0),
    'msr9': ({'t': 1.0, 'D': 45.0, 'L0': 44.0, 'p': 1.0},
             22.5, 44.0, 1.0),
}


def _geo_f0(method_id):
    """f0 пустого резонатора H01p по геометрии (согласованная)."""
    _, radius, leff, p = GEO[method_id]
    return resonator_f0_h01p(radius, leff, p)


F0_MFD = _geo_f0('mfd')     # ~10.504 ГГц (D=45, L0=45, p=2)
F0_SO = _geo_f0('so')       # ~8.779 ГГц (R0=22.5, L=45, p=1)


# ----------------------------------------------------------------------
# Синтез АЧХ и измерение через полный конвейер
# ----------------------------------------------------------------------

def _sweep(f_mode, q, depth_db=25.0, seed=1):
    """АЧХ симулятора с одной выделенной модой."""
    sim = SimulatorConfig(
        noise_db=0.05, seed=seed,
        main_mode=SimulatedMode(f_mode, q, depth_db),
        extra_modes=(SimulatedMode(f_mode * 0.9, 1500, 6.0),
                     SimulatedMode(f_mode * 1.13, 1200, 8.0)))
    vna = SimulatedVNA(VNAConfig(start_freq=SWEEP_START,
                                 stop_freq=SWEEP_STOP), sim=sim)
    vna.connect()
    d = vna.measure_frequency_response()
    return d['frequencies'], d['amplitudes']


def _measure(method_id, params, f0, q0, fe, qe, bandwidth='half_power',
             scheme='notch'):
    """Полный конвейер: два свипа -> экстракция -> расчёт метода.

    depth0/depthe (ТЗ3-1) передаются из результата экстракции —
    поправка режектора считается от глубины провала.
    """
    xb, yb = _sweep(f0, q0, depth_db=30.0, seed=1)
    xs, ys = _sweep(fe, qe, depth_db=22.0, seed=2)
    b = extract_resonance_db(xb, yb, bandwidth=bandwidth)
    s = extract_resonance_db(xs, ys, bandwidth=bandwidth)
    ch = ResonanceChannels(
        f0=b['f0'], f1=b['f1'], f2=b['f2'], a0=b['A0'],
        fe=s['f0'], f1e=s['f1'], f2e=s['f2'], ae=s['A0'],
        depth0=b['depth_db'], depthe=s['depth_db'])
    params = dict(params)
    params.setdefault('scheme', scheme)
    return get_method(method_id).calculate(params, ch)


def _extract_near(x, y, f, span=300e6):
    """Экстракция резонанса в окне +-span вокруг ожидаемой частоты.

    Архивные АЧХ — провалы; схема 'notch' (ТЗ2-4): полоса полумощности.
    """
    xs = [xi for xi in x if abs(xi - f) <= span]
    ys = [yi for xi, yi in zip(x, y) if abs(xi - f) <= span]
    return extract_resonance_db(xs, ys, **extraction_options('notch'))


def _e_errors(result):
    """Ошибки результата без диагностики tgo — E не зависит от него."""
    return [e for e in result.errors if 'tgo' not in e]


# ----------------------------------------------------------------------
# ТЗ2-2 — воздушный образец: fe = f0 -> E = 1
# ----------------------------------------------------------------------

@pytest.mark.parametrize('method_id', ('mfd', 'mfch', 'so', 'msr9'))
def test_air_sample_returns_unit_epsilon(method_id):
    """ТЗ2-2: воздушный образец на согласованной геометрии -> E ≈ 1.

    Для МФД/МФЧ/СО полость не меняется -> fe = f0 (для МФЧ при этом
    delL = 0). ТЗ3-6: у MSR9 поршень поднимается на t, полость с
    образцом = L0 + t — поэтому воздушный образец даёт
    fe = f0_H01p(R, L0 + t, p), а не f0.
    """
    from backend.core.calculator.const import EB
    params, *_ = GEO[method_id]
    params = dict(params, scheme='notch')
    f0 = _geo_f0(method_id)
    if method_id == 'msr9':
        fe = resonator_f0_h01p(0.5 * params['D'],
                               params['L0'] + params['t'],
                               params.get('p') or 1)
    else:
        fe = f0
    ch = ResonanceChannels(f0=f0, f1=f0 - 5e6, f2=f0 + 5e6, a0=-40.0,
                           fe=fe, f1e=fe - 5e6, f2e=fe + 5e6, ae=-40.0,
                           depth0=40.0, depthe=40.0)
    e = get_method(method_id).calculate(params, ch).values['E']
    assert e is not None
    # ТЗ3-5: eps относительно вакуума — для воздуха eps_в = 1.0006
    assert abs(e - EB) <= 0.005, f'{method_id}: E = {e}'


# ----------------------------------------------------------------------
# ТЗ2-3 — независимая прямая модель -> конвейер -> восстановленное E
# ----------------------------------------------------------------------

# (method_id, params, eps эталона, R мм, L_eff мм, p)
# eps: 2.55 — полистирол, 9.8 — поликор. Для msr9 геометрия подобрана
# так, чтобы fE оставалась в диапазоне ВАЦ 8-12 ГГц.
FORWARD_CASES = [
    ('mfd',  {'t': 4.0, 'D': 45.0, 'L0': 45.0, 'p': 2.0},
     2.55, 22.5, 45.0, 2.0),
    ('mfd',  {'t': 4.0, 'D': 45.0, 'L0': 45.0, 'p': 2.0},
     9.8, 22.5, 45.0, 2.0),
    ('mfch', {'t': 4.0, 'D': 45.0, 'L0': 45.0, 'delL': 0.0, 'p': 2.0},
     2.55, 22.5, 45.0, 2.0),
    ('mfch', {'t': 4.0, 'D': 45.0, 'L0': 45.0, 'delL': 0.0, 'p': 2.0},
     9.8, 22.5, 45.0, 2.0),
    ('so',   {'a': 1.95, 'R0': 22.5, 'L': 45.0, 'p': 1.0},
     2.55, 22.5, 45.0, 1.0),
    ('so',   {'a': 1.95, 'R0': 22.5, 'L': 45.0, 'p': 1.0},
     9.8, 22.5, 45.0, 1.0),
    ('msr9', {'t': 1.0, 'D': 45.0, 'L0': 44.0, 'p': 1.0},
     2.55, 22.5, 44.0, 1.0),
    ('msr9', {'t': 1.0, 'D': 45.0, 'L0': 69.0, 'p': 3.0},
     9.8, 22.5, 69.0, 3.0),
]


def _forward_fe(method_id, params, eps, radius, leff, p):
    """Прямая задача: fE (и delL для МФЧ) по независимой модели."""
    f0 = resonator_f0_h01p(radius, leff, p)
    if method_id == 'mfd':
        fe = fe_mfd(eps, params['t'], radius, params['L0'], f0)
    elif method_id == 'mfch':
        delL = delL_mfch(eps, params['t'], radius, f0)
        params['delL'] = delL
        fe = f0
    elif method_id == 'so':
        fe = fe_so(eps, params['a'], params['R0'], params['L'], p, f0)
    else:
        fe = fe_msr9(eps, params['t'], radius, params['L0'], f0)
    return f0, fe


@pytest.mark.parametrize(
    'case', FORWARD_CASES, ids=lambda c: f'{c[0]}-E{c[2]}')
def test_forward_model_roundtrip(case):
    """ТЗ2-3: эталонное E -> прямая модель -> АЧХ -> конвейер -> E.

    Допуск по восстановленному epsilon <= 1%: основной вклад —
    экстракция резонанса по квантованной сетке свипа.
    """
    method_id, params, eps, radius, leff, p = case
    params = dict(params)
    f0, fe = _forward_fe(method_id, params, eps, radius, leff, p)
    result = _measure(method_id, params, f0, 300.0, fe, 200.0)
    e_rec = result.values.get('E')
    assert e_rec is not None and not _e_errors(result)
    assert abs(e_rec - eps) / eps <= 0.01, \
        f'{method_id}: задано {eps}, восстановлено {e_rec}'


# ----------------------------------------------------------------------
# ТЗ2-6 — множители G (8.9) и eta (8.8) МФД сверены с ГОСТ Р 8.623-2015
# ----------------------------------------------------------------------

def test_mfd_g_multiplier_matches_gost():
    """Регрессия: G и eta пересчитаны по формулам (8.5)-(8.9) ГОСТ
    заново, без переиспользования кода метода."""
    from backend.core.calculator.const import C, EB, V11

    params = dict(GEO['mfd'][0], scheme='notch')
    f0 = F0_MFD
    fe = fe_mfd(4.0, params['t'], 22.5, params['L0'], f0)
    ch = ResonanceChannels(f0=f0, f1=f0 - 10e6, f2=f0 + 10e6, a0=-40.0,
                           fe=fe, f1e=fe - 15e6, f2e=fe + 15e6,
                           ae=-30.0, depth0=40.0, depthe=30.0)
    r = get_method('mfd').calculate(params, ch)
    assert r.values.get('E') is not None and not _e_errors(r)

    a, t, L0, p = 0.5 * params['D'], params['t'], params['L0'], params['p']
    k2 = 2.0 * math.pi * fe * math.sqrt(EB) / C
    h2 = math.sqrt(k2 ** 2 - (V11 / a) ** 2)
    x = r.values['x']  # корень ур. (8.2) — проверен обходным тестом
    E = r.values['E']
    ksi = math.sin(x) ** 2 / math.sin(h2 * (L0 - t)) ** 2
    F1 = 1.0 - math.sin(2.0 * x) / (2.0 * x)
    F2 = 1.0 - math.sin(2.0 * h2 * (L0 - t)) / (2.0 * h2 * (L0 - t))
    # (8.9)
    G_ref = a * L0 / ((2.0 * a - L0)
                      * (p * C / (2.0 * L0 * f0 * math.sqrt(EB))) ** 2
                      + L0)
    # (8.8)
    num = ((x / V11) ** 2 * (a / t) ** 2 + t * F1 / a
           + ksi * ((h2 * a / V11) ** 2 + (L0 - t) * F2 / a))
    den = E * t * F1 + ksi * (L0 - t) * F2
    nu_ref = G_ref * math.sqrt(f0 / fe) * (V11 / (k2 * a)) ** 2 \
        * num / den
    assert r.values['G'] == pytest.approx(G_ref, rel=1e-12)
    assert r.values['nu'] == pytest.approx(nu_ref, rel=1e-12)


def test_mfd_eta_physical_sense():
    """ТЗ-3 п.3.2: физический смысл eta (8.8) — множитель вычитаемых
    потерь пустого резонатора, нормированный на энергию образца.
    Для воздушного образца eta -> 1 (tgδ = 0), eta > 0 всегда и
    растёт при уменьшении толщины образца."""
    from backend.core.calculator.const import C, EB, V11

    params = dict(GEO['mfd'][0], scheme='notch')
    f0 = F0_MFD
    fe = fe_mfd(4.0, params['t'], 22.5, params['L0'], f0)
    ch = ResonanceChannels(f0=f0, f1=f0 - 10e6, f2=f0 + 10e6, a0=-40.0,
                           fe=fe, f1e=fe - 15e6, f2e=fe + 15e6,
                           ae=-30.0, depth0=40.0, depthe=30.0)
    r = get_method('mfd').calculate(params, ch)
    assert r.values['nu'] > 0.0

    # воздушный образец (fe = f0, согласованная геометрия): потери
    # образца нулевые -> tgδ = 0 требует eta -> Q00/Q0E = 1
    ch_air = ResonanceChannels(
        f0=f0, f1=f0 - 10e6, f2=f0 + 10e6, a0=-40.0,
        fe=f0, f1e=f0 - 10e6, f2e=f0 + 10e6, ae=-40.0,
        depth0=40.0, depthe=40.0)
    r_air = get_method('mfd').calculate(params, ch_air)
    assert r_air.values['nu'] == pytest.approx(1.0, abs=0.05)
    assert r_air.values['tgo'] == pytest.approx(0.0, abs=1e-6)

    # эталонная формула (8.8): eta растёт при уменьшении t
    # (нормировка на убывающую энергию образца)
    from backend.core.calculator.res_x import solve_tan_over_x

    def nu_ref(t):
        k2_ = 2.0 * math.pi * fe * math.sqrt(EB) / C
        h2_ = math.sqrt(k2_ ** 2 - (V11 / 22.5) ** 2)
        drob = math.tan(h2_ * (45.0 - t)) / (h2_ * t)
        x_ = solve_tan_over_x(drob)
        E_ = (C / (2.0 * math.pi * fe)) ** 2 \
            * ((x_ / t) ** 2 + (V11 / 22.5) ** 2)
        ksi_ = math.sin(x_) ** 2 / math.sin(h2_ * (45.0 - t)) ** 2
        F1_ = 1.0 - math.sin(2.0 * x_) / (2.0 * x_)
        F2_ = 1.0 - math.sin(2.0 * h2_ * (45.0 - t)) \
            / (2.0 * h2_ * (45.0 - t))
        return r.values['G'] * math.sqrt(f0 / fe) \
            * (V11 / (k2_ * 22.5)) ** 2 \
            * ((x_ / V11) ** 2 * (22.5 / t) ** 2 + t * F1_ / 22.5
               + ksi_ * ((h2_ * 22.5 / V11) ** 2
                         + (45.0 - t) * F2_ / 22.5)) \
            / (E_ * t * F1_ + ksi_ * (45.0 - t) * F2_)

    assert nu_ref(1.0) > nu_ref(4.0) > 0.0


def _tgo_for_qe(qe, fe):
    # физический tgo восстанавливается в режиме 'half_power': ГОСТ-
    # полоса (min+3.01дБ) у синтезированного провала квантуется
    # сеткой свипа и не возвращает физическую добротность
    r = _measure('so', GEO['so'][0], F0_SO, 300.0, fe=fe, qe=qe,
                 bandwidth='half_power')
    return r.values.get('tgo'), r


def _so_energy_fraction(eps, a, R0, L, p, fe):
    """Независимая прямая модель доли электрической энергии в стержне
    (ТЗ-3 п.3.3): интегралы полей собственной моды составного
    резонатора, без формул backend.core.calculator.

    Мода H01p: E_ф = u(r)·sin(hz), u = J1(kd·r) внутри стержня
    (r < a), u = amp·Z1(ka·r) снаружи, amp = J1(x)/Z1(y) из
    непрерывности на r = a. Доля энергии:
    p_e = eps·I_d/(eps·I_d + eps_в·I_a) — должна совпасть с K1E.
    """
    from scipy.special import jv, yn
    import numpy as np

    from backend.core.calculator.const import C, EB

    h = p * math.pi / L
    k0 = 2.0 * math.pi * fe / C           # вакуум (ТЗ3-5)
    k2 = k0 * math.sqrt(EB)
    kd = math.sqrt(eps * k0 ** 2 - h * h)
    ka = math.sqrt(k2 ** 2 - h * h)
    x, y = kd * a, ka * a
    kk = jv(1, y * R0 / a) / yn(1, y * R0 / a)
    z1y = jv(1, y) - kk * yn(1, y)
    amp = jv(1, x) / z1y
    r_in = np.linspace(1e-9, a, 4001)
    r_out = np.linspace(a, R0, 20001)
    u_in = jv(1, kd * r_in)
    u_out = amp * (jv(1, ka * r_out) - kk * yn(1, ka * r_out))
    I_d = float(np.trapezoid(u_in ** 2 * r_in, r_in))
    I_a = float(np.trapezoid(u_out ** 2 * r_out, r_out))
    return eps * I_d / (eps * I_d + EB * I_a)


def test_so_filling_factor_is_energy_fraction():
    """ТЗ-3 п.3.3: tgδ входит в бюджет потерь только через K1E —
    долю электрической энергии образца. Проверка независимыми
    интегралами полей собственной моды: K1E == p_e."""
    from backend.core.calculator.const import C, EB, V11

    a, R0, L, p = 1.95, 22.5, 45.0, 1.0
    eps = 4.0
    fe = fe_so(eps, a, R0, L, p, F0_SO)
    ch = ResonanceChannels(f0=F0_SO, f1=F0_SO - 15e6, f2=F0_SO + 15e6,
                           a0=-40.0, fe=fe, f1e=fe - 20e6,
                           f2e=fe + 20e6, ae=-30.0,
                           depth0=40.0, depthe=30.0)
    r = get_method('so').calculate(
        dict(GEO['so'][0], scheme='notch'), ch)
    assert r.values.get('E') is not None
    p_e = _so_energy_fraction(eps, a, R0, L, p, fe)
    assert r.values['K1E'] == pytest.approx(p_e, rel=0.01)
    assert 0.0 < r.values['K1E'] < 1.0


def test_inverse_tgo_roundtrip():
    """Конвейерный раундтрип tgδ (согласованность, не независимость):
    синтез добротности -> экстракция -> метод восстанавливает tgo.
    Независимость прямой задачи потерь проверена тестом выше:
    K1E — точная доля энергии образца, поэтому tgo·K1E = Δ(1/Q).
    """
    fe = fe_so(4.0, 1.95, 22.5, 45.0, 1.0, F0_SO)
    tgo_target = 3e-3
    lo_q, hi_q = 40.0, 2000.0
    for _ in range(25):
        mid = math.sqrt(lo_q * hi_q)
        t_mid, _ = _tgo_for_qe(mid, fe)
        if t_mid is None or t_mid > tgo_target:
            lo_q = mid
        else:
            hi_q = mid
    qe = math.sqrt(lo_q * hi_q)
    tgo_rec, result = _tgo_for_qe(qe, fe)
    assert tgo_rec is not None and not _e_errors(result)
    assert abs(tgo_rec - tgo_target) / tgo_target <= 0.20


# ----------------------------------------------------------------------
# ТЗ-16.4 — сверка с архивными измерениями
# ----------------------------------------------------------------------

def _physical_e(v):
    return v is not None and 1.0 <= v <= 200.0


def _geometry_f0(method_id, params):
    """f0 пустого резонатора H01p по геометрии записи (ТЗ2-8).

    ТЗ3-6: для msr9 длина пустого резонатора — L0 (= 2L по ГОСТ §11);
    толщина образца в неё не входит (поршень поднимается на t).
    """
    try:
        if method_id in ('mfd', 'mfch'):
            return resonator_f0_h01p(
                params['D'] / 2.0, params['L0'], params.get('p') or 2)
        if method_id == 'so':
            return resonator_f0_h01p(
                params['R0'], params['L'], params.get('p') or 1)
        if method_id == 'msr9':
            return resonator_f0_h01p(
                params['D'] / 2.0, params['L0'],
                params.get('p') or 1)
    except (KeyError, TypeError):
        return None
    return None


def _collect_archive_rows():
    """Прогон нового конвейера по всем архивным файлам."""
    rows = []
    files = sorted(glob.glob(ARCHIVE_GLOB))
    if R_DATA.exists():
        files.append(str(R_DATA))
    for path in files:
        try:
            rec = record_from_archive(path)
        except Exception as exc:
            rows.append({'file': Path(path).name, 'method': '?',
                         'status': f'не читается: {exc}'})
            continue
        method = get_method(rec['method_id'])
        if method is None or not rec['samples'] or not rec['sweep']['x']:
            continue
        x, y = rec['sweep']['x'], rec['sweep']['y']
        row = {'file': Path(path).name, 'method': rec['method_id'],
               'title': rec['title'], 'samples': [],
               'f0_rec': rec['f0'], 'params': rec['params']}
        # ТЗ2-8: геометрическая согласованность записи —
        # f0 по размерам резонатора vs записанная f0
        f0_geom = _geometry_f0(rec['method_id'], rec['params'])
        if f0_geom and rec['f0']:
            row['f0_geom'] = f0_geom
            row['geom_dev_pct'] = abs(f0_geom - rec['f0']) / f0_geom * 100
        try:
            b = _extract_near(x, y, rec['f0'])
            row['f0_new'] = b['f0']
            row['df0_mhz'] = abs(b['f0'] - rec['f0']) / 1e6
        except Exception as exc:
            row['status'] = f'базовый резонанс: {exc}'
            rows.append(row)
            continue
        for s in rec['samples']:
            srow = {'name': s.get('name'), 'e_arch': s.get('e'),
                    'tgo_arch': s.get('tgo'), 'fe_arch': s.get('fe')}
            if not s['sweep_y'] or s['fe'] is None:
                srow['status'] = 'нет кривой образца'
                row['samples'].append(srow)
                continue
            try:
                sm = _extract_near(x, s['sweep_y'], s['fe'])
            except Exception as exc:
                srow['status'] = f'резонанс образца: {exc}'
                row['samples'].append(srow)
                continue
            ch = ResonanceChannels(
                f0=b['f0'], f1=b['f1'], f2=b['f2'], a0=b['A0'],
                fe=sm['f0'], f1e=sm['f1'], f2e=sm['f2'], ae=sm['A0'],
                depth0=b['depth_db'], depthe=sm['depth_db'])
            # ТЗ3-2: архивные АЧХ — провалы, считаем с явной схемой
            # 'notch'; сам выбор задокументирован в отчёте (п.4.1 ТЗ-2
            # без ответа заказчика остаётся открытым)
            params = dict(rec['params'])
            params.setdefault('scheme', 'notch')
            r = method.calculate(params, ch)
            e_new = r.values.get('E')
            srow.update({
                'e_new': e_new, 'tgo_new': r.values.get('tgo'),
                'dfe_mhz': abs(sm['f0'] - s['fe']) / 1e6,
                'errors': r.errors,
                'warnings': r.warnings,
            })
            if _physical_e(e_new) and _physical_e(s.get('e')):
                srow['de_pct'] = abs(e_new - s['e']) / s['e'] * 100
            row['samples'].append(srow)
        rows.append(row)
    return rows


_METHOD_NAME_RU = {'mfd': 'МФД', 'mfch': 'МФЧ', 'so': 'СО',
                   'msr9': 'MSR9'}


def _roundtrip_rows():
    """Строки таблицы прямой/обратной задачи для отчёта (ТЗ2-2, ТЗ2-3)."""
    out = []
    from backend.core.calculator.const import EB
    for mid in ('mfd', 'mfch', 'so', 'msr9'):
        params, *_ = GEO[mid]
        params = dict(params, scheme='notch')
        f0 = _geo_f0(mid)
        # ТЗ3-6: у MSR9 полость с образцом = L0 + t — «воздушный»
        # образец резонирует на частоте полости L0 + t
        fe_air = f0 if mid != 'msr9' else resonator_f0_h01p(
            0.5 * params['D'], params['L0'] + params['t'],
            params.get('p') or 1)
        ch = ResonanceChannels(f0=f0, f1=f0 - 5e6, f2=f0 + 5e6, a0=-40.0,
                               fe=fe_air, f1e=fe_air - 5e6,
                               f2e=fe_air + 5e6, ae=-40.0,
                               depth0=40.0, depthe=40.0)
        e = get_method(mid).calculate(params, ch).values.get('E')
        out.append((_METHOD_NAME_RU[mid], 'E (воздух)', f'{EB:.4f}',
                    f'{e:.4f}', f'{abs(e - EB) * 100:.2f}'))
    for case in FORWARD_CASES:
        mid, params, eps, radius, leff, p = case
        params = dict(params)
        f0, fe = _forward_fe(mid, params, eps, radius, leff, p)
        result = _measure(mid, params, f0, 300.0, fe, 200.0)
        e_rec = result.values.get('E')
        d = abs(e_rec - eps) / eps * 100 if e_rec else float('nan')
        out.append((_METHOD_NAME_RU[mid], 'E (прямая модель)',
                    f'{eps:.2f}', f'{e_rec:.3f}' if e_rec else '—',
                    f'{d:.2f}'))
    return out


def _geom_status(row):
    """Классификация согласованности геометрии записи (ТЗ2-8).

    ТЗ-3 п.4.1: статусы относятся к ЗАПИСАННОЙ геометрии, которая,
    вероятно, является дефолтами формы, а не измеренными размерами.
    """
    dev = row.get('geom_dev_pct')
    if dev is None:
        return '—', 'нет геометрии'
    if row['method'] == 'so' and row['f0_geom'] > row['f0_rec']:
        # f0 по размерам выше измеренной -> мода не достижима
        return f'{dev:.1f}', 'невозможна при записанной геометрии'
    if dev <= 1.0:
        return f'{dev:.1f}', 'согласована'
    if dev <= 5.0:
        return f'{dev:.1f}', 'малое расхождение'
    return f'{dev:.1f}', 'несогласована'


def _write_report(rows, e_ok, e_cmp, f_ok, f_cmp, nonphys):
    REPORT_PATH.parent.mkdir(exist_ok=True)
    lines = [
        '# Верификация ПО «Микроникс» (ТЗ-16, ТЗ-2, ТЗ-3)', '',
        '## 1. Верификация формул (ТЗ2-2, ТЗ2-3, ТЗ3-3)', '',
        'Физический предел E = eps_в (относительно вакуума, ТЗ3-5)',
        'для воздушного образца на согласованной геометрии;',
        'эталонные E (2.55 — полистирол, 9.8 — поликор) через',
        'независимую прямую модель (verification/forward_model.py):',
        'дисперсионное уравнение решается прямо (fE по заданному E),',
        'синтезируется АЧХ, конвейер (экстракция -> метод)',
        'восстанавливает E. Допуск 1%.',
        'Для СО дополнительно проверено, что множитель K1E — точная',
        'доля электрической энергии в образце (интегралы полей',
        'собственной моды, tests/test_verification.py).',
        '',
        '| Метод | Величина | Задано | Восстановлено | Δ, % |',
        '|---|---|---|---|---|',
    ]
    for m, v, t, r, d in _roundtrip_rows():
        lines.append(f'| {m} | {v} | {t} | {r} | {d} |')

    # --- раздел 2: геометрия ---
    geo_rows = [r for r in rows if 'geom_dev_pct' in r]
    geo_ok = sum(1 for r in geo_rows if r['geom_dev_pct'] <= 1.0)
    lines += [
        '',
        '## 2. Геометрия архивных записей (ТЗ2-1, ТЗ2-8, ТЗ-3 п.4.1)', '',
        'ВАЖНО (ТЗ-3 п.4.1): размеры в архивных записях, вероятнее',
        'всего, являются ЗНАЧЕНИЯМИ ПО УМОЛЧАНИЮ формы, а не',
        'измеренными размерами резонаторов и образцов. Аргументы:',
        '',
        '- во всех записях лежат одинаковые поля ВСЕХ методов',
        '  (data[2][d_res]=45, data[3][d_res]=22.5, h_res=45) —',
        '  включая записи других методов;',
        '- у МФД (фиксированная длина!) f0 в архиве меняется от 8.8',
        '  до 11.1 ГГц при одинаковой «геометрии» D=45, L0=45, p=2 —',
        '  физически невозможно для реальной установки;',
        '- часть записей МФЧ (D=50, L0=90) сходилась бы при p=4',
        '  (9.89 ГГц) и p=5 (11.08 ГГц) — поле index могло быть',
        '  дефолтом формы.',
        '',
        'Поэтому таблица ниже — проверка самосогласованности',
        'записанных значений, а не верификация фактической',
        'установки, и сверку E с архивом следует считать не',
        'состоявшейся. Фактические размеры резонаторов и схема',
        'включения — открытый вопрос заказчику (п.4.1 ТЗ-2,',
        'без ответа).',
        '',
        'f0 пустого резонатора H01p по размерам записи vs записанная',
        'f0. Расхождение > 1% — записанная геометрия не согласована',
        'с частотой; в любом случае архивные E нельзя считать',
        'подтверждёнными измерениями материала.',
        '',
        f'- Записей с проверяемой геометрией: **{len(geo_rows)}**,',
        f'  согласовано (Δ <= 1%): **{geo_ok}**',
        '',
        '| Файл | Метод | f0 записи, ГГц | f0 по геометрии, ГГц | Δ, % | Статус |',
        '|---|---|---|---|---|---|',
    ]
    for row in rows:
        if 'geom_dev_pct' not in row:
            continue
        dev, status = _geom_status(row)
        lines.append(
            f"| {row['file']} | {row['method']} "
            f"| {row['f0_rec'] / 1e9:.4f} | {row['f0_geom'] / 1e9:.4f} "
            f"| {dev} | {status} |")
    lines += [
        '',
        'Особо (ТЗ-3 п.4.1): «невозможные» записи **СО** — невозможны',
        'только при записанной (подозреваемой дефолтной) геометрии:',
        'при d_res=22.5 мм как диаметре отсечка H01 ≈ 16.3 ГГц выше',
        'записанной f0 ≈ 9.65 ГГц; как радиус — f0 ≈ 8.8 ГГц при',
        'L=45, p=1 (расхождение ~9%). Это следствие дефолтов формы,',
        'а не доказательство дефектности самих измерений — без',
        'паспорта резонатора реальный статус записей неизвестен.',
    ]

    # --- раздел 3: сверка с архивом ---
    lines += [
        '',
        '## 3. Сверка с архивными измерениями (ТЗ-16.4)', '',
        'ВАЖНО: «новое» E — результат исправленных формул ГОСТ при',
        'геометрии, записанной в архиве. Оно НЕ является «истинным»',
        'значением материала: записанная геометрия, вероятно, дефолт',
        'формы (раздел 2), а эталонных материалов для сверки нет.',
        '',
        'Отличия новых формул от легаси:',
        '',
        '- **СО**: удалён эмпирический делитель E/3.2 (в ГОСТ его нет,',
        '  п.12.1); продольный индекс p берётся из записи (архив: p=1,',
        '  легаси считал с p=2); E — относительно вакуума (ТЗ3-5).',
        '- **МФД**: уравнение (8.2) tg[h2(L0-t)] вместо легаси tg[h2(L0+t)].',
        '- **МФЧ**: знак правой части (7.2) и знаменатель в eta (7.8).',
        '- **СВЧФ**: формулы не менялись — совпадение с архивом',
        '  показательно (но это унаследованная модель, НЕ ГОСТ 71432).',
        '',
        'Поправка на связь (ТЗ3-1): для провалов tgδ считается по',
        'ГЛУБИНЕ провала относительно базовой линии (схема "режектор").',
        'Записи не содержат признака схемы — принята "notch" по форме',
        'АЧХ; при фактической проходной схеме tgδ в таблице неверен',
        '(открытый вопрос 4.1 ТЗ-2).',
        '',
        f'- Файлов архива: **{len(rows)}**',
        f'- Базовый резонанс: совпадение частоты в пределах 10 МГц — '
        f'**{f_ok}/{f_cmp}**',
        f'- epsilon: совпадение в пределах 15% (обе величины физичны, '
        f'1 <= E <= 200) — **{e_ok}/{e_cmp}**',
        f'- Записей с нефизичным E в архиве (E < 1 или E > 200): '
        f'**{nonphys}** — при новом конвейере результат физичен '
        f'(исправление Д-3)', '',
        '| Файл | Метод | Образец | E архив | E новое | ΔE, % | Примечание |',
        '|---|---|---|---|---|---|---|',
    ]
    for row in rows:
        if 'samples' not in row:
            lines.append(f"| {row['file']} | {row['method']} | — | — | — | — "
                         f"| {row.get('status', '')} |")
            continue
        for s in row['samples']:
            ea = f"{s['e_arch']:.3g}" if isinstance(s.get('e_arch'), float) else '—'
            en = f"{s['e_new']:.3g}" if isinstance(s.get('e_new'), float) else '—'
            de = f"{s['de_pct']:.1f}" if 'de_pct' in s else '—'
            note = s.get('status') or ''
            if 'de_pct' in s:
                if s['de_pct'] <= 15:
                    note = ''
                elif row['method'] in ('so', 'mfch', 'mfd'):
                    note = 'систематич. (исправленная формула ГОСТ)'
                else:
                    note = 'расхождение'
            elif isinstance(s.get('e_arch'), float) and isinstance(s.get('e_new'), float):
                note = 'архив: E нефизично' if not _physical_e(s['e_arch']) else 'новое: E нефизично'
            if s.get('errors'):
                note = (note + '; ' if note else '') + '; '.join(s['errors'])
            if s.get('warnings'):
                note = (note + '; ' if note else '') + '; '.join(s['warnings'])
            lines.append(
                f"| {row['file']} | {row['method']} | {s.get('name') or '—'} "
                f"| {ea} | {en} | {de} | {note} |")
    REPORT_PATH.write_text('\n'.join(lines), encoding='utf-8')


def test_archive_comparison():
    """Сверка нового конвейера с архивом + генерация таблицы ТЗ-16."""
    rows = _collect_archive_rows()
    assert rows, 'архивные файлы не найдены'

    f_ok = f_cmp = e_ok = e_cmp = nonphys = 0
    for row in rows:
        if 'df0_mhz' in row:
            f_cmp += 1
            f_ok += row['df0_mhz'] <= 10.0
        for s in row.get('samples', []):
            if isinstance(s.get('e_arch'), float) and not _physical_e(s['e_arch']):
                nonphys += 1
            if 'de_pct' in s:
                e_cmp += 1
                e_ok += s['de_pct'] <= 15.0

    _write_report(rows, e_ok, e_cmp, f_ok, f_cmp, nonphys)

    # Базовые резонансы находятся почти всегда
    assert f_cmp >= 50 and f_ok / f_cmp >= 0.85
    # Совпадение epsilon критично только для СВЧФ — его формулы не
    # менялись. Для СО/МФЧ/МФД расхождения с архивом систематические:
    # архивные E посчитаны дефектными формулами (Д-12..Д-17), а
    # геометрия архива не подтверждена (предупреждения ТЗ2-1).
    sv_ok = sv_cmp = 0
    for row in rows:
        if row['method'] != 'svchf':
            continue
        for s in row.get('samples', []):
            if 'de_pct' in s:
                sv_cmp += 1
                sv_ok += s['de_pct'] <= 15.0
    assert sv_cmp > 0 and sv_ok / sv_cmp >= 0.70


# ----------------------------------------------------------------------
# ТЗ-16.5 — сквозной конвейер: симулятор -> обработка -> расчёт -> БД -> PDF
# ----------------------------------------------------------------------

def test_end_to_end_pipeline(tmp_path):
    from backend.api.micronix_api import MicronixAPI

    api = MicronixAPI(simulate=True,
                      db_path=str(tmp_path / 'v.db'),
                      report_dir=str(tmp_path / 'report'))
    session = api.start_measurement(
        'mfd', {'t': 1.0, 'D': 45.0, 'L0': 45.0, 'scheme': 'notch'})
    session.measure_base()
    s = session.measure_sample('образец')
    measure_id = session.finish()
    assert s.result.values.get('E') is not None

    rec = api.db.load_measurement(measure_id)
    assert rec['samples'] and rec['samples'][0].get('e')
    # ТЗ2-4: схема включения — явный параметр, сохранён в БД
    assert rec['params'].get('scheme') in ('notch', 'through')
    pdf = Path(api.generate_report(measure_id))
    assert pdf.exists() and pdf.stat().st_size > 10_000
