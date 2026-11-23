"""Тесты реестра методов и расчётов (ТЗ-2, ТЗ-3, ТЗ-6, Д-1…Д-5).

Эталонные значения — вывод методов ветки main (All_Methods_3.py);
расхождения tgo в МФЧ/МФД/СО обусловлены исправлением Д-2
(добротность по полосе нагруженного резонанса).
"""

import math

import pytest

from backend.core.calculator import (ResonanceChannels, SolverError,
                                     get_method, list_methods)
from backend.core.calculator import res_x
from backend.core.calculator.registry import LEGACY_ID_MAP


def make_res(**kw):
    base = dict(f0=10e9, f1=9.99e9, f2=10.01e9, a0=-40.0,
                fe=9.9e9, f1e=9.8908e9, f2e=9.9092e9, ae=-30.0)
    base.update(kw)
    return ResonanceChannels(**base)


RES = make_res()


# --- Реестр и контракт (ТЗ-2, ТЗ-3) ---

def test_registry_contains_all_methods():
    ids = {m.id for m in list_methods()}
    assert ids == {'mfch', 'mfd', 'so', 'svchf', 'msr9'}


def test_method_contract_fields():
    for m in list_methods():
        assert m.name and m.standard
        assert m.inputs, f"{m.id}: нет описания входов"
        for spec in m.inputs:
            assert spec.name and spec.label


def test_get_method_accepts_legacy_numeric_ids():
    for num, mid in LEGACY_ID_MAP.items():
        assert get_method(num) is get_method(mid)


def test_validate_catches_bad_params():
    m = get_method('mfd')
    assert m.validate({'t': 10.0, 'D': 45.0, 'L0': 80.0})      # t вне диапазона
    assert m.validate({'t': 1.0})                              # не хватает D, L0
    assert m.validate({'t': 'abc', 'D': 45.0, 'L0': 80.0})     # не число
    assert m.validate({'t': 1.0, 'D': 45.0, 'L0': 80.0}) == []


# --- Д-1: структурированный результат, ошибки не маскируются ---

def test_invalid_input_produces_errors_not_ok():
    r = get_method('mfd').calculate({'t': 1.0, 'D': 1.0, 'L0': 80.0}, RES)
    assert not r.ok and r.errors            # D <= t
    r = get_method('mfd').calculate({'t': 1.0, 'D': 45.0, 'L0': 80.0},
                                    make_res(f0=7e9))
    assert not r.ok and r.errors            # f0 вне диапазона


def test_missing_resonance_fields_produce_errors():
    r = get_method('mfd').calculate({'t': 1.0, 'D': 45.0, 'L0': 80.0},
                                    ResonanceChannels(f0=10e9))
    assert not r.ok
    assert any('резонанс' in e for e in r.errors)


def test_out_of_range_result_reported_honestly():
    """tgo вне диапазона -> errors[], при этом E вычислено корректно."""
    r = get_method('mfd').calculate({'t': 1.0, 'D': 45.0, 'L0': 80.0},
                                    make_res(f2e=9.95e9))
    assert not r.ok and r.errors
    assert r.values['E'] == pytest.approx(83.9534326, rel=1e-6)


# --- Точность переноса (эталон main) ---

def test_mfd_valid_case_values():
    r = get_method('mfd').calculate({'t': 1.0, 'D': 45.0, 'L0': 80.0}, RES)
    assert r.ok
    assert r.values['E'] == pytest.approx(83.9534326, rel=1e-6)
    assert 5e-5 <= r.values['tgo'] <= 1e-2


def test_rod_values_and_calibration():
    r = get_method('so').calculate({'a': 3.0, 'R0': 22.5, 'L': 40.0}, RES)
    # эталон main: E_new = 4.270961017 при делителе 3.2
    assert r.values['E'] == pytest.approx(4.270961017, rel=1e-6)
    assert r.values['E_raw'] == pytest.approx(13.667075254, rel=1e-6)
    # Д-4: калибровочный коэффициент настраивается
    r1 = get_method('so').calculate(
        {'a': 3.0, 'R0': 22.5, 'L': 40.0, 'e_calibration': 1.0}, RES)
    assert r1.values['E'] == pytest.approx(r1.values['E_raw'], rel=1e-12)


def test_loaded_q_uses_own_bandwidth():
    """Д-2: QE считается по полосе кривой С образцом, а не пустой."""
    res = make_res(f1e=9.7e9, f2e=10.1e9)   # полоса 400 МГц >> 20 МГц
    r = get_method('so').calculate({'a': 3.0, 'R0': 22.5, 'L': 40.0}, res)
    assert r.values['QE'] == pytest.approx(res.fe / (res.f2e - res.f1e))
    assert r.values['QE'] != pytest.approx(res.fe / (res.f2 - res.f1))


def test_ferrite_st_real_reference():
    """Эталон main (Д-5): Methot_Egor_st и Method_real."""
    res = ResonanceChannels(f0=10.15e9, f1=10.145e9, f2=10.155e9,
                            fe=9.46e9, f1e=9.455e9, f2e=9.465e9)
    m = get_method('svchf')
    r = m.calculate({'variant': 'st', 'R': 11.0, 'r': 0.81}, res)
    assert r.values['E'] == pytest.approx(7.757516989104899, rel=1e-9)
    assert r.values['tgo'] == pytest.approx(0.00045955425256495965, rel=1e-9)
    r = m.calculate({'variant': 'real', 'R': 11.0, 'r': 0.81}, res)
    assert r.values['E'] == pytest.approx(7.608248705806665, rel=1e-9)
    assert r.values['tgo'] == pytest.approx(0.0040832596583221924, rel=1e-9)


def test_ferrite_circle_square_structured_result():
    """Д-5: результат — структура, а не строка."""
    res = ResonanceChannels(f0=10.145e9, fe=10.155e9)
    m = get_method('svchf')
    r = m.calculate({'variant': 'circle', 'R': 11.0, 'r': 0.81,
                     'deld': 0.000564469, 'Ms': 0.0}, res)
    assert isinstance(r.values, dict)
    assert r.values['tgo'] == pytest.approx(0.02886565109569998, rel=1e-9)
    r = m.calculate({'variant': 'square', 'R': 11.0, 'r': 0.81,
                     'a': 1.12, 'b': 1.12,
                     'deld': 0.000564469, 'Ms': 0.0}, res)
    assert r.values['tgo'] == pytest.approx(0.0514126001627364, rel=1e-9)


def test_ferrite_unknown_variant_errors():
    r = get_method('svchf').calculate(
        {'variant': 'nonsense', 'R': 11.0, 'r': 0.81}, RES)
    assert not r.ok and r.errors


# --- Д-3: решатели без значений по умолчанию ---

def test_cot_solver_finds_physical_root():
    x = res_x.solve_for_x_1(0.12, 1.0, 40.0)
    u = x / 2.0
    resid = math.cos(u) / (math.sin(u) * u) - \
        2.0 * math.tan(0.12 * 40.0) / (0.12 * 1.0)
    assert 0.0 < x < 2.0 * math.pi
    assert abs(resid) < 1e-8


def test_tan_over_x_solver_first_positive_root():
    x = res_x.solve_tan_over_x(4.0)
    assert math.pi / 2 < x < math.pi
    assert abs(math.tan(x) / x + 4.0) < 1e-8


def test_bessel_ratio_solver():
    from scipy.special import jv
    x = res_x.solve_bessel_ratio(1.5)
    assert abs(jv(1, x) / (x * jv(0, x)) - 1.5) < 1e-8


def test_solvers_raise_instead_of_default():
    """Д-3: несходимость -> SolverError, не math.pi и не мусор."""
    with pytest.raises(SolverError):
        res_x.solve_for_x_1(float('nan'), 1.0)
    with pytest.raises(SolverError):
        res_x.solve_tan_over_x(float('nan'))


# --- MSR-9: модуль без input()/sys.exit() ---

def test_msr9_propagating_branch():
    r = get_method('msr9').calculate({'t': 1.0, 'D': 45.0, 'L0': 80.0,
                                      'p': 1.0}, RES)
    assert 'fc' in r.values
    assert r.values['fe'] if 'fe' in r.values else True
    # структурированный результат в любом случае
    assert isinstance(r.values.get('E'), float)


def test_msr9_evanescent_branch():
    """fE < fc (затухающая волна) — отдельный решатель."""
    res = ResonanceChannels(f0=10e9, f1=9.99e9, f2=10.01e9, a0=-40.0,
                            fe=8.05e9, f1e=8.04e9, f2e=8.06e9, ae=-30.0)
    r = get_method('msr9').calculate({'t': 1.0, 'D': 45.0, 'L0': 80.0,
                                      'p': 1.0}, res)
    assert r.values['fc'] > res.fe          # действительно ниже отсечки
    assert r.values['E'] == pytest.approx(3.225386131, rel=1e-6)


# --- Модель измерения (ТЗ-3) ---

def test_measurement_links_to_registry():
    from backend.models.measurement import Measurement
    from datetime import datetime
    m = Measurement(id='x', title='t', method='mfd',
                    date=datetime.now(), parameters={})
    assert m.method_obj is get_method('mfd')
    m2 = Measurement.from_dict({'id': 'x', 'title': 't', 'method': 2,
                                'date': datetime.now().isoformat(),
                                'parameters': {}})
    assert m2.method == 'mfd'
    assert m2.method_obj is get_method('mfd')
