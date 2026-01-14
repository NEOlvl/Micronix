import pyvisa
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class VNAConfig:
    address: str = "TCPIP0::localhost::5025::SOCKET"
    timeout: int = 500
    start_freq: float = 8e9  # Гц
    stop_freq: float = 12e9  # Гц


class VNAController:
    """Контроллер для работы с векторным анализатором"""

    def __init__(self, config: Optional[VNAConfig] = None):
        self.config = config or VNAConfig()
        self.rm = pyvisa.ResourceManager()
        self.resource = None

    def connect(self) -> bool:
        """Подключение к VNA"""
        try:
            self.resource = self.rm.open_resource(
                self.config.address,
                timeout=self.config.timeout
            )
            self.resource.read_termination = '\n'
            self.resource.write_termination = '\n'
            return True
        except Exception as e:
            print(f"Ошибка подключения к VNA: {e}")
            return False

    def disconnect(self):
        """Отключение от VNA"""
        if self.resource:
            self.resource.close()

    def measure_frequency_response(self) -> Dict[str, List[float]]:
        """Измерение АЧХ"""
        if not self.resource:
            raise ConnectionError("VNA не подключен")

        # Установка диапазона частот
        self.resource.write(f"SENS:FREQ:STAR {self.config.start_freq}")
        self.resource.write(f"SENS:FREQ:STOP {self.config.stop_freq}")

        # Чтение данных
        freq_data = self.resource.query("CALC1:DATA:XAXis?")
        amp_data = self.resource.query("CALC1:DATA:FDAT?")

        # Парсинг данных
        frequencies = list(map(float, freq_data.split(',')))
        amplitudes = self._parse_amplitude_data(amp_data)

        return {
            'frequencies': frequencies,
            'amplitudes': amplitudes
        }

    def _parse_amplitude_data(self, raw_data: str) -> List[float]:
        """Парсинг амплитудных данных"""
        all_values = list(map(float, raw_data.split(',')))
        # Берем только каждое второе значение (амплитуды)
        return all_values[::2]

    def find_resonance_parameters(self, frequencies, amplitudes):
        """Нахождение резонансных параметров"""
        float_amps = np.array(amplitudes)
        idx_min = np.argmin(float_amps)
        f0 = frequencies[idx_min]
        A0 = float_amps[idx_min]

        # Поиск f1 и f2 на уровне -3 дБ
        target_level = A0 + 3
        idx_left = self._find_crossing(float_amps[:idx_min], target_level, from_right=True)
        idx_right = self._find_crossing(float_amps[idx_min:], target_level, from_right=False) + idx_min

        f1 = frequencies[idx_left]
        f2 = frequencies[idx_right]
        Q = f0 / (f2 - f1)

        return {
            'f0': f0, 'f1': f1, 'f2': f2,
            'A0': A0, 'Q': Q,
            'idx_min': idx_min
        }

    def _find_crossing(self, data, threshold, from_right=False):
        """Нахождение пересечения с порогом"""
        if from_right:
            data = data[::-1]

        for i, val in enumerate(data):
            if val >= threshold:
                return len(data) - i - 1 if from_right else i

        return len(data) - 1 if from_right else 0