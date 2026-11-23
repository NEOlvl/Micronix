"""
Demo backend for Micronix application (sample data, no hardware)
"""
import json
import os
import random
import numpy as np
from datetime import datetime


class DemoBackend:
    """Demo backend for Micronix application"""

    def __init__(self):
        self.measures = {}
        self.next_id = 1
        self.setup_sample_data()

    def setup_sample_data(self):
        """Setup sample measurement data"""
        # Generate sample frequency data (8-12 GHz like original)
        self.x = np.arange(8.01, 12.0, 0.005)

        # Create baseline resonance curve
        f0 = 9.87
        Q = 800
        self.base_y = -20 * np.log10(1 + (self.x - f0) ** 2 * (1 / (f0 / Q)) ** 2)
        self.base_y = np.clip(self.base_y - np.max(self.base_y) - 10, -100, 0)

        # Add some sample measurements
        sample_measure = {
            "id_m": "M001",
            "title": "001",
            "time": "20.10.2024 17:56:46",
            "x": self.x.tolist(),
            "y_res": self.base_y.tolist(),
            "y_samples": {
                1: {
                    "name": "ПЭС-1-1",
                    "y_res": (self.base_y + np.random.normal(0, 0.3, size=self.base_y.shape)).tolist(),
                    "tgo": 6.1e-4,
                    "E": 11.1
                }
            }
        }
        self.measures[sample_measure["id_m"]] = sample_measure
        self.next_id = 2

    def query(self, method, params):
        """Main backend API method"""
        if method == "measure_data":
            return list(self.measures.values())

        elif method == "create_graph_x":
            return self.x.tolist()

        elif method == "create_graph":
            return self.base_y.tolist()

        elif method == "new_create":
            m_id = f"M{self.next_id:03d}"
            title = f"{self.next_id:03d}"
            self.next_id += 1

            new_measure = {
                "id_m": m_id,
                "id": m_id,
                "title": title,
                "subtitle": "Метод в очереди",
                "time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "x": self.x.tolist(),
                "y_res": self.base_y.tolist(),
                "y_samples": {}
            }
            self.measures[m_id] = new_measure

            return {
                "id": m_id,
                "title": title,
                "subtitle": "Подготовка...",
                "subtitle_full": "Выполняется настройка..."
            }

        elif method == "new_sample":
            id_m = params.get("id_m", "")
            if not id_m and self.measures:
                id_m = list(self.measures.keys())[-1]

            name = params.get("new_sample_name", f"Sample-{random.randint(1, 999)}")

            if id_m in self.measures:
                measure = self.measures[id_m]
                sample_idx = max(measure["y_samples"].keys()) + 1 if measure["y_samples"] else 1

                # Create sample data with some variation
                noise = np.random.normal(0, 0.3, size=len(self.base_y))
                shifted = self.base_y + noise - np.linspace(0, 1.0, num=len(self.base_y)) * 0.1

                measure["y_samples"][sample_idx] = {
                    "name": name,
                    "y_res": shifted.tolist(),
                    "tgo": float(6.1e-4 + random.random() * 1e-4),
                    "E": float(11.0 + random.random() * 0.3)
                }

                return {"id": id_m, "name": name}

        elif method == "method_end":
            return {"id": params.get("id_m", "")}

        elif method == "read_data":
            id_m = params.get("id_m")
            if id_m in self.measures:
                return self.measures[id_m]
            elif self.measures:
                return list(self.measures.values())[0]

        return {}

    def get_measurement_json(self, measure_id):
        """Get JSON data for specific measurement"""
        try:
            # Здесь должна быть логика получения JSON данных
            # Для демо вернем пример данных

            # Ищем файл в measurement_data
            data_dir = "measurement_data"
            if os.path.exists(data_dir):
                # Ищем файлы, содержащие ID измерения
                json_files = [f for f in os.listdir(data_dir)
                              if f.endswith('.json') and str(measure_id) in f]

                if json_files:
                    file_path = os.path.join(data_dir, json_files[0])
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)

            # Если файл не найден, вернем пример данных
            return self.get_sample_json_data()

        except Exception as e:
            print(f"Error getting measurement JSON: {e}")
            return None

    def list_json_files(self):
        """List all available JSON files"""
        data_dir = "measurement_data"
        if os.path.exists(data_dir):
            return [f for f in os.listdir(data_dir) if f.endswith('.json')]
        return []