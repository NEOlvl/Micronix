import pyvisa
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.core.data_processor import extract_resonance_db


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
        """Нахождение резонансных параметров АЧХ (ТЗ-5, data_processor)."""
        return extract_resonance_db(frequencies, amplitudes)