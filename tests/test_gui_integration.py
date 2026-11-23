"""Оффскрин-смоук GUI <-> backend: карточки, формы, сессия (ТЗ-9).

QT_QPA_PLATFORM=offscreen — виджеты создаются без дисплея.
"""

import os
import sys

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

pytest.importorskip('PyQt6')
from PyQt6.QtWidgets import QApplication  # noqa: E402

from backend.api.micronix_api import MicronixAPI  # noqa: E402


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def api(tmp_path):
    return MicronixAPI(db_path=str(tmp_path / 'test.db'),
                       simulate=True,
                       report_dir=str(tmp_path / 'report'))


class TestNewMeasurementPage:
    def test_cards_from_registry(self, app, api):
        from pages.new_measurement_page import NewMeasurementPage
        page = NewMeasurementPage(api)
        assert set(page._method_meta) == {
            'mfch', 'mfd', 'so', 'svchf', 'msr9'}
        assert len(page._param_fields) > 0
        page.deleteLater()

    def test_form_fields_per_method(self, app, api):
        from pages.new_measurement_page import NewMeasurementPage
        page = NewMeasurementPage(api)
        page.select_method('so')
        assert set(page._param_fields) == {'a', 'R0', 'L',
                                           'e_calibration'}
        page.deleteLater()

    def test_variant_combo(self, app, api):
        from pages.new_measurement_page import NewMeasurementPage
        page = NewMeasurementPage(api)
        page.select_method('svchf')
        assert hasattr(page, 'variant_combo')
        # вариант square добавляет поля a и b
        page.select_variant('square')
        assert {'a', 'b'} <= set(page._param_fields)
        page.deleteLater()

    def test_validation_blocks_start(self, app, api):
        from pages.new_measurement_page import NewMeasurementPage
        page = NewMeasurementPage(api)
        page.select_method('mfd')
        page._param_fields['t'].setText('99')  # вне диапазона
        page._param_fields['D'].setText('45')
        page._param_fields['L0'].setText('80')
        page.start_measurement()
        assert not page.error_label.isHidden()
        assert 'диапазон' in page.error_label.text()
        page.deleteLater()

    def test_start_creates_session(self, app, api):
        from pages.new_measurement_page import NewMeasurementPage
        page = NewMeasurementPage(api)
        page.select_method('mfd')
        page._param_fields['t'].setText('1.0')
        page._param_fields['D'].setText('45')
        page._param_fields['L0'].setText('80')

        emitted = []
        page.measurement_started.connect(emitted.append)
        page.start_measurement()

        assert len(emitted) == 1
        sid = emitted[0]['session_id']
        assert sid in api.sessions
        page.deleteLater()


class TestProcessWidgetFlow:
    def test_real_flow(self, app, api):
        """Виджет процесса гоняет реальную сессию (ТЗ-9)."""
        from widgets.measurement_process_widget import (
            MeasurementProcessWidget)

        session = api.start_measurement(
            'mfd', {'t': 1.0, 'D': 45.0, 'L0': 80.0}, title='T')
        widget = MeasurementProcessWidget(api, {
            'session_id': session.id,
            'measurement_id': session.id,
            'method': 'mfd',
        })
        assert widget.session is session

        widget._measure_base()
        assert session.state == 'base_done'
        assert widget._base_done

        widget._measure_sample('Образец X')
        assert len(session.samples) == 1
        assert len(widget.samples_added) == 1

        widget.finish_measurement()
        assert session.state == 'finished'
        assert api.load_measurement(session.id) is not None
        widget.deleteLater()


class TestMainWindow:
    def test_window_builds(self, app, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from main_window import MicronixMainWindow
        win = MicronixMainWindow()
        assert isinstance(win.backend, MicronixAPI)
        # карточки методов на главной — из реестра (5 штук)
        assert len(win.home_page.method_cards) == 5
        win.deleteLater()
