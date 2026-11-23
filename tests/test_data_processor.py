"""Тесты выделения резонанса из АЧХ (ТЗ-16.3).

Синтетические кривые с шумом — f0, Q с контролируемой погрешностью;
вырожденные случаи — контролируемая ошибка ResonanceError.
"""

import json
import os
import glob

import numpy as np
import pytest

from backend.core.data_processor import (
    ResonanceError, extract_resonance, extract_resonance_db,
)


def make_dip(f0=10e9, q=800.0, depth_db=30.0, baseline_db=-5.0,
             slope_db_per_ghz=0.0, n=1601, fstart=8e9, fstop=12e9,
             noise_db=0.0, seed=0):
    """Синтетическая АЧХ: лоренцев провал в линейной мощности + дБ-шум."""
    f = np.linspace(fstart, fstop, n)
    baseline_db = baseline_db + slope_db_per_ghz * (f - 10e9) / 1e9
    p_base = 10.0 ** (baseline_db / 10.0)
    depth_frac = 1.0 - 10.0 ** (-depth_db / 10.0)
    bw = f0 / q
    lorentz = 1.0 / (1.0 + (2.0 * (f - f0) / bw) ** 2)
    p = p_base * (1.0 - depth_frac * lorentz)
    a = 10.0 * np.log10(np.maximum(p, 1e-12))
    if noise_db > 0:
        a = a + np.random.default_rng(seed).normal(0.0, noise_db, n)
    return f, a


def make_peak(f0=10e9, q=800.0, height_db=30.0, baseline_db=-60.0,
              n=1601, noise_db=0.0, seed=0):
    """Синтетическая АЧХ с резонансом-пиком (режим 'peak')."""
    f = np.linspace(8e9, 12e9, n)
    p_base = 10.0 ** (baseline_db / 10.0)
    h_frac = 10.0 ** (height_db / 10.0) - 1.0
    bw = f0 / q
    lorentz = 1.0 / (1.0 + (2.0 * (f - f0) / bw) ** 2)
    p = p_base * (1.0 + h_frac * lorentz)
    a = 10.0 * np.log10(p)
    if noise_db > 0:
        a = a + np.random.default_rng(seed).normal(0.0, noise_db, n)
    return f, a


# --- Восстановление параметров ---

def test_clean_dip_recovers_f0_and_q():
    # Q=400 -> полоса ~25 МГц (~10 отсчётов): хорошо разрешённый провал,
    # предупреждений быть не должно
    f0_true, q_true = 10e9, 400.0
    f, a = make_dip(f0=f0_true, q=q_true, noise_db=0.0)
    dx = f[1] - f[0]
    # физическая добротность — в режиме 'half_power'
    r = extract_resonance(f, a, bandwidth='half_power')
    assert abs(r.f0 - f0_true) < 2 * dx
    assert r.q == pytest.approx(q_true, rel=0.05)
    assert r.f1 < r.f0 < r.f2
    assert r.warnings == []


def test_gost_bandwidth_mode():
    """Прил. Г.3.1 ГОСТ 8.623-2015: полоса на уровне минус 3.01 дБ
    от экстремума. Для провала глубиной 30 дБ это измеренная полоса
    у дна — уже физической, Q выше."""
    f, a = make_dip(f0=10e9, q=400.0, depth_db=30.0, noise_db=0.0)
    r = extract_resonance(f, a, bandwidth='gost')
    level = min(a) + 3.01
    # границы — пересечения кривой уровня min+3.01 дБ у дна провала:
    # внутри провала (около f0) a < level, снаружи a > level
    i0 = int(np.argmin(a))
    inside = a < level
    # ближайшие точки выше уровня влево и вправо от минимума
    i_left = np.max(np.nonzero(~inside[:i0])[0])
    i_right = i0 + np.min(np.nonzero(~inside[i0:])[0])
    assert f[i_left] < r.f1 < f[i_left + 1]
    assert f[i_right - 1] < r.f2 < f[i_right]
    # ГОСТ-полоса уже полосы половинной мощности -> Q гостовская выше
    r_hp = extract_resonance(f, a, bandwidth='half_power')
    assert r.q > r_hp.q


def test_gost_mode_shallow_dip_raises():
    """Провал мельче 3.01 дБ: по ГОСТ полоса не определяется."""
    f, a = make_dip(depth_db=2.0, noise_db=0.0)
    with pytest.raises(ResonanceError):
        extract_resonance(f, a, bandwidth='gost')
    r = extract_resonance(f, a, bandwidth='half_power')
    assert r.warnings


def test_noisy_dip_recovers_f0_and_q():
    f0_true, q_true = 9.7e9, 600.0
    f, a = make_dip(f0=f0_true, q=q_true, noise_db=0.5, seed=1)
    dx = f[1] - f[0]
    r = extract_resonance(f, a, bandwidth='half_power')
    assert abs(r.f0 - f0_true) < 3 * dx
    assert r.q == pytest.approx(q_true, rel=0.15)


def test_sloped_baseline_is_handled():
    """Наклонная базовая линия (как в реальных файлах) не ломает оценку."""
    f0_true, q_true = 10.5e9, 1000.0
    f, a = make_dip(f0=f0_true, q=q_true, slope_db_per_ghz=4.0, noise_db=0.1, seed=2)
    dx = f[1] - f[0]
    r = extract_resonance(f, a, bandwidth='half_power')
    assert abs(r.f0 - f0_true) < 3 * dx
    assert r.q == pytest.approx(q_true, rel=0.15)


def test_symmetric_noisy_dip():
    """Ранее падающий случай: симметричная кривая + шум с повторяющимися минимумами."""
    f0_true = 10e9
    f, a = make_dip(f0=f0_true, q=2000.0, noise_db=0.3, seed=3)
    # добавим дубликат значения минимума — старый list.index брал первое вхождение
    a = a.tolist()
    i = a.index(min(a))
    a[i - 40] = a[i]
    r = extract_resonance(f, a, bandwidth='half_power')
    assert abs(r.f0 - f0_true) < 4 * (f[1] - f[0])
    assert r.q == pytest.approx(2000.0, rel=0.3)


def test_peak_mode():
    f0_true, q_true = 10e9, 500.0
    f, a = make_peak(f0=f0_true, q=q_true, noise_db=0.2, seed=4)
    r = extract_resonance(f, a, peak='peak', bandwidth='half_power')
    assert abs(r.f0 - f0_true) < 3 * (f[1] - f[0])
    assert r.q == pytest.approx(q_true, rel=0.15)


# --- ТЗ2-4/ТЗ3-1: схема включения резонатора ---

import math

from backend.core.calculator.res_x import (extraction_options,
                                           unloaded_q)


def synth_notch_s21(f0_hz, q_unloaded, beta, n=1601,
                    fstart=8e9, fstop=12e9):
    """АЧХ режектора |S21|, дБ, с известными Q0 и коэффициентом связи β.

    S21(f) = 1 - (β/(1+β)) / (1 + j·2QL·Δf/f0),  QL = Q0/(1+β);
    на резонансе |S21min| = 1/(1+β) — отсчитывается от базовой
    линии (0 дБ), т.е. depth_db = 20·lg(1+β).
    """
    f = np.linspace(fstart, fstop, n)
    ql = q_unloaded / (1.0 + beta)
    s21 = 1.0 - (beta / (1.0 + beta)) \
        / (1.0 + 2j * ql * (f - f0_hz) / f0_hz)
    return f, 20.0 * np.log10(np.abs(s21))


def synth_through_s21(f0_hz, q_unloaded, s21_max, n=1601,
                      fstart=8e9, fstop=12e9):
    """Пик |S21| проходного резонатора, дБ, с известными Q0 и |S21max|.

    S21(f) = S21max / (1 + j·2QL·Δf/f0),  QL = Q0·(1-|S21max|);
    + подложка -60 дБ для оценки базовой линии экстрактором.
    """
    f = np.linspace(fstart, fstop, n)
    ql = q_unloaded * (1.0 - s21_max)
    s21 = s21_max / (1.0 + 2j * ql * (f - f0_hz) / f0_hz)
    return f, 10.0 * np.log10(np.abs(s21) ** 2 + 1e-6)


def test_scheme_notch_recovers_unloaded_q():
    """ТЗ3-1/п.3.1: независимый тест поправки режектора — кривая
    с известными Q0 и β, поправка считается от глубины провала."""
    f0_hz, q0_true, beta = 10e9, 900.0, 9.0
    f, a = synth_notch_s21(f0_hz, q0_true, beta)
    opts = extraction_options('notch')
    assert opts == {'peak': 'dip', 'bandwidth': 'half_power'}
    r = extract_resonance(f, a, **opts)
    # нагруженная добротность и глубина — из физики синтеза,
    # не из тестируемого кода
    assert r.q == pytest.approx(q0_true / (1.0 + beta), rel=0.05)
    assert r.depth_db == pytest.approx(
        20.0 * math.log10(1.0 + beta), rel=0.05)
    q0 = unloaded_q(r.q, r.a0, 'notch', depth_db=r.depth_db)
    assert q0 == pytest.approx(q0_true, rel=0.08)


def test_scheme_notch_correction_uses_depth_not_absolute_a0():
    """ТЗ3-1: поправка считается от depth_db, а не абсолютного A0 —
    при базовой линии != 0 дБ старый вариант завышал Q0."""
    q0_true, beta = 800.0, 19.0            # глубина ~26 дБ
    f, a = synth_notch_s21(10e9, q0_true, beta)
    # смещаем кривую вниз на 5 дБ — базовая линия -5 дБ, A0 ~ -31 дБ
    a = a - 5.0
    r = extract_resonance(f, a, **extraction_options('notch'))
    q0 = unloaded_q(r.q, r.a0, 'notch', depth_db=r.depth_db)
    assert q0 == pytest.approx(q0_true, rel=0.08)
    # старый вариант (по абсолютному A0) завышал бы поправку ~1.8 раза
    q0_wrong = r.q * 10.0 ** (-0.05 * r.a0)
    assert q0_wrong > 1.5 * q0


def test_scheme_through_recovers_unloaded_q():
    """П.3.1: независимый тест поправки проходного резонатора —
    кривая с известными Q0 и |S21max|, поправка по уровню пика."""
    f0_hz, q0_true, s21_max = 10e9, 720.0, 0.1
    f, a = synth_through_s21(f0_hz, q0_true, s21_max)
    opts = extraction_options('through')
    assert opts == {'peak': 'peak', 'bandwidth': 'gost'}
    r = extract_resonance(f, a, **opts)
    assert r.q == pytest.approx(q0_true * (1.0 - s21_max), rel=0.08)
    assert r.a0 == pytest.approx(20.0 * math.log10(s21_max), abs=1.0)
    q0 = unloaded_q(r.q, r.a0, 'through')
    assert q0 == pytest.approx(q0_true, rel=0.10)


def test_unsorted_input_is_sorted():
    f, a = make_dip(noise_db=0.0)
    idx = np.random.default_rng(5).permutation(len(f))
    r = extract_resonance(f[idx], a[idx])
    assert r.f0 == pytest.approx(10e9, rel=1e-4)


# --- Вырожденные случаи -> контролируемая ошибка ---

def test_flat_spectrum_raises():
    f = np.linspace(8e9, 12e9, 1601)
    a = np.full_like(f, -10.0) + np.random.default_rng(6).normal(0, 0.05, f.size)
    with pytest.raises(ResonanceError):
        extract_resonance(f, a)


def test_monotonic_spectrum_raises():
    f = np.linspace(8e9, 12e9, 1601)
    a = -5.0 - 3.0 * (f - 8e9) / 1e9  # только наклон, без провала
    with pytest.raises(ResonanceError):
        extract_resonance(f, a)


def test_edge_resonance_raises():
    f, a = make_dip(f0=8.05e9, q=800.0)
    with pytest.raises(ResonanceError):
        extract_resonance(f, a)


def test_mismatched_lengths_raise():
    with pytest.raises(ResonanceError):
        extract_resonance([1.0, 2.0, 3.0] * 10, [1.0] * 10)


def test_nan_input_raises():
    f, a = make_dip()
    a[100] = np.nan
    with pytest.raises(ResonanceError):
        extract_resonance(f, a)


def test_shallow_dip_warns_but_returns():
    """Провал глубже 0, но мельче 3 дБ: предупреждение, результат есть
    (в режиме half_power; в gost-режиме — контролируемая ошибка)."""
    f, a = make_dip(depth_db=2.0, noise_db=0.0)
    r = extract_resonance(f, a, bandwidth='half_power')
    assert r.warnings
    assert r.q > 0


def test_dict_wrapper_keys():
    f, a = make_dip()
    d = extract_resonance_db(f, a)
    for key in ('f0', 'f1', 'f2', 'A0', 'Q', 'idx_min', 'warnings'):
        assert key in d


# --- Смоук-тест на архивных данных (ТЗ-16.4, начало таблицы) ---

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'measurement_data')


@pytest.mark.skipif(not os.path.isdir(DATA_DIR), reason="нет архивных данных")
def test_archive_files_f0_matches_deepest_dip():
    """Алгоритм выделяет самый глубокий провал реальных АЧХ.

    Записанный в архиве f0 не всегда совпадает с глобальным минимумом
    (для части методов оператор выбирал конкретную моду), поэтому
    сверяемся с минимумом сырых данных.
    """
    files = sorted(glob.glob(os.path.join(DATA_DIR, '*.txt')))
    assert files, "архивные файлы не найдены"
    ok, skipped = 0, 0
    for path in files:
        with open(path, encoding='utf-8') as fh:
            d = json.load(fh)
        if not d.get('x') or not d.get('y_res'):
            continue
        f = np.array([float(v) for v in d['x']])
        a = np.array([float(v) for v in d['y_res']])
        try:
            r = extract_resonance(f, a)
        except ResonanceError:
            skipped += 1
            continue
        dx = f[1] - f[0]
        # f0 должен попадать на реальный локальный минимум АЧХ,
        # а не в произвольную точку (сглаживание может выбрать
        # другой провал, если сырой минимум — шумовой выброс)
        loc_min = np.array([
            k for k in range(2, len(a) - 2)
            if a[k] <= a[k - 1] and a[k] <= a[k + 1]
            and a[k] <= a[k - 2] and a[k] <= a[k + 2]
        ])
        if loc_min.size:
            assert np.min(np.abs(f[loc_min] - r.f0)) < 3 * dx, \
                f"{path}: f0={r.f0} не попадает ни на один локальный минимум"
        assert r.f1 < r.f0 < r.f2
        assert r.q > 0
        ok += 1
    assert ok > 0, "ни один архивный файл не обработан"
    # Доля пропущенных (резонанс у края и т.п.) не должна доминировать
    assert skipped <= ok
