"""Тесты VNAController и SimulatedVNA (ТЗ-4, ТЗ-10).

Симулятор проходит тот же путь SCPI->разбор->валидация, что и
реальный прибор, поэтому покрывает весь транспортный код.
"""

import numpy as np
import pytest

from backend.core.data_processor import ResonanceError
from backend.core.vna_controller import (SimulatedMode, SimulatedVNA,
                                         SimulatorConfig, VNAController,
                                         VNAError, create_vna)


# --- Симулятор: полный путь без железа ---

def test_simulator_sweep_end_to_end():
    vna = create_vna(simulate=True)
    vna.connect()
    try:
        data = vna.measure_frequency_response()
    finally:
        vna.disconnect()
    f, a = data['frequencies'], data['amplitudes']
    assert len(f) == len(a) == 1601
    assert f[0] == pytest.approx(8e9) and f[-1] == pytest.approx(12e9)
    # основной провал 30 дБ на 10 ГГц должен находиться процессором
    r = vna.find_resonance_parameters(f, a)
    assert abs(r['f0'] - 10e9) < 3 * (f[1] - f[0])
    assert r['Q'] > 0


def test_simulator_honors_freq_range_writes():
    """Запись SENS:FREQ:STAR/STOP меняет выдаваемый диапазон."""
    vna = SimulatedVNA(sim=SimulatorConfig(n_points=201))
    vna.connect()
    vna.write("SENS:FREQ:STAR 9 GHz")
    vna.write("SENS:FREQ:STOP 11 GHz")
    f = vna._freq_axis()
    assert f[0] == pytest.approx(9e9) and f[-1] == pytest.approx(11e9)
    # и числовой формат без единиц тоже принимается
    vna.write("SENS:FREQ:STAR 9500000000")
    assert vna._freq_axis()[0] == pytest.approx(9.5e9)


def test_simulator_fdat_pairs_format():
    """FDAT? отдаёт пары значений, как реальный прибор."""
    vna = SimulatedVNA(sim=SimulatorConfig(n_points=101))
    vna.connect()
    raw = vna.query("CALC1:DATA:FDAT?")
    assert len(raw.split(',')) == 202


def test_simulator_requires_connect():
    vna = SimulatedVNA()
    with pytest.raises(VNAError):
        vna.measure_frequency_response()
    with pytest.raises(VNAError):
        vna.query("*IDN?")


def test_simulator_unknown_command():
    vna = SimulatedVNA()
    vna.connect()
    with pytest.raises(VNAError):
        vna.query("SYST:BOGUS?")


def test_custom_sim_modes_extractable():
    """Пользовательская конфигурация резонансов извлекается."""
    sim = SimulatorConfig(
        n_points=801,
        main_mode=SimulatedMode(9.8e9, 300.0, 35.0),
        extra_modes=())
    vna = SimulatedVNA(sim=sim)
    vna.connect()
    data = vna.measure_frequency_response()
    r = vna.find_resonance_parameters(data['frequencies'],
                                    data['amplitudes'])
    dx = data['frequencies'][1] - data['frequencies'][0]
    assert abs(r['f0'] - 9.8e9) < 3 * dx


# --- Валидация ответов прибора (ТЗ-10) ---

class StubResource:
    """Заглушка pyvisa-ресурса с заранее заданными ответами."""

    def __init__(self, responses):
        self.responses = responses
        self.writes = []

    def write(self, cmd):
        self.writes.append(cmd)

    def query(self, cmd):
        for key, value in self.responses.items():
            if key in cmd:
                if isinstance(value, Exception):
                    raise value
                return value
        return ''

    def close(self):
        pass


def _stub_vna(responses):
    vna = VNAController()
    vna.resource = StubResource(responses)
    return vna


def _freq_csv(n=100, f0=8e9, f1=12e9):
    return ','.join(str(v) for v in np.linspace(f0, f1, n))


def test_measure_parses_and_validates():
    vna = _stub_vna({
        'XAXis': _freq_csv(100),
        'FDAT': ','.join('-5.0,0.0' for _ in range(100)),
    })
    data = vna.measure_frequency_response()
    assert len(data['frequencies']) == len(data['amplitudes']) == 100
    assert vna.resource.writes[0].startswith('SENS:FREQ:STAR')
    assert vna.resource.writes[1].startswith('SENS:FREQ:STOP')


def test_length_mismatch_raises():
    vna = _stub_vna({
        'XAXis': _freq_csv(100),
        'FDAT': ','.join('-5.0,0.0' for _ in range(50)),
    })
    with pytest.raises(VNAError, match='Рассогласование'):
        vna.measure_frequency_response()


def test_empty_response_raises():
    vna = _stub_vna({'XAXis': '', 'FDAT': '-5.0,0.0'})
    with pytest.raises(VNAError, match='Пустой ответ'):
        vna.measure_frequency_response()


def test_nonnumeric_response_raises():
    vna = _stub_vna({'XAXis': 'abc,def', 'FDAT': '-5.0,0.0'})
    with pytest.raises(VNAError, match='Нечисловые'):
        vna.measure_frequency_response()


def test_odd_fdat_pairs_raise():
    vna = _stub_vna({
        'XAXis': _freq_csv(100),
        'FDAT': ','.join('-5.0' for _ in range(199)),
    })
    with pytest.raises(VNAError, match='нечётное число'):
        vna.measure_frequency_response()


def test_too_few_points_raise():
    vna = _stub_vna({
        'XAXis': _freq_csv(10),
        'FDAT': ','.join('-5.0,0.0' for _ in range(10)),
    })
    with pytest.raises(VNAError, match='мало точек'):
        vna.measure_frequency_response()


def test_not_connected_raises():
    with pytest.raises(VNAError):
        VNAController().measure_frequency_response()


def test_connect_failure_raises_vnaerror():
    """Нет прибора/бэкенда -> контролируемая VNAError."""
    vna = VNAController()
    vna._rm = _FailingRM()
    with pytest.raises(VNAError):
        vna.connect()


class _FailingRM:
    def open_resource(self, *a, **kw):
        raise OSError('no device')


def test_disconnect_idempotent():
    vna = _stub_vna({})
    vna.disconnect()
    vna.disconnect()   # повторный вызов не падает
    assert not vna.is_connected
