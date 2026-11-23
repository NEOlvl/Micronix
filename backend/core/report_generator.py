"""Генерация PDF-протокола измерения (ТЗ-8, исправляет Д-8).

Отличия от легаси create_pdf (main/t2.py):
- таблица строится штатным pdf.table(), без ручного счётчика строк
- метод, его название и параметры берутся из реестра методов (ТЗ-3),
  неизвестный метод не роняет генерацию (в легаси case _ -> NameError)
- параметры образца выводятся по inputs[] метода, а не хардкодом на метод
- шрифт с кириллицей ищется в fonts/, затем в системе;
  без TTF-шрифта — контролируемая ReportError
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.calculator.registry import get_method

DEFAULT_OUT_DIR = 'report'
APP_NAME = 'Микроникс'
APP_VERSION = '1.0'

_FONT_CANDIDATES_REG = (
    'fonts/timesnewromanpsmt.ttf', 'fonts/times.ttf',
    'fonts/TNR.ttf', 'C:/Windows/Fonts/times.ttf',
)
_FONT_CANDIDATES_BOLD = (
    'fonts/TNR_bold.ttf', 'fonts/timesbd.ttf',
    'C:/Windows/Fonts/timesbd.ttf',
)


class ReportError(Exception):
    """Контролируемая ошибка генерации отчёта."""


def _find_font(candidates) -> Optional[str]:
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _format_params(record: Dict) -> str:
    """Строка параметров образца по inputs[] метода из реестра."""
    params = record.get('params') or {}
    method = get_method(record.get('method_id'))
    if method is None:
        return '; '.join(f'{k}: {v}' for k, v in params.items())
    parts = []
    for inp in method.inputs:
        val = params.get(inp.name)
        if val is not None and val != '':
            unit = f' {inp.unit}' if inp.unit else ''
            parts.append(f'{inp.label}: {val}{unit}')
    return '; '.join(parts)


def _format_date(record: Dict) -> str:
    raw = record.get('created_at') or record.get('date')
    if raw:
        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%d%m%Y'):
            try:
                return datetime.strptime(str(raw), fmt).strftime('%d.%m.%Y')
            except ValueError:
                continue
    return datetime.now().strftime('%d.%m.%Y')


class ReportGenerator:
    """Формирует PDF-протокол по записи измерения (формат db_manager)."""

    def __init__(self, out_dir: str = DEFAULT_OUT_DIR):
        self.out_dir = Path(out_dir)

    def generate(self, record: Dict, out_path: Optional[str] = None) -> str:
        """Сгенерировать PDF. Возвращает путь к файлу."""
        if not record.get('measure_id'):
            raise ReportError("В записи нет 'measure_id'")

        from fpdf import FPDF
        from fpdf.fonts import FontFace
        pdf = FPDF()
        font_reg = _find_font(_FONT_CANDIDATES_REG)
        font_bold = _find_font(_FONT_CANDIDATES_BOLD) or font_reg
        if not font_reg:
            raise ReportError(
                'Не найден TTF-шрифт с кириллицей (fonts/, '
                'C:/Windows/Fonts/times.ttf)')
        pdf.add_font('T', '', font_reg)
        pdf.add_font('T', 'B', font_bold)

        pdf.add_page()
        pdf.set_font('T', 'B', 14)
        title = record.get('title') or record['measure_id']
        pdf.ln(10)
        pdf.cell(0, 10, 'Отчёт проведения измерений', align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 10, f'диэлектрической проницаемости #{title}',
                 align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(8)

        # --- общие данные ---
        pdf.set_font('T', 'B', 12)
        pdf.cell(0, 10, 'Общие данные:', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('T', '', 12)
        pdf.cell(0, 8, f'Дата проведения испытаний: {_format_date(record)}',
                 new_x='LMARGIN', new_y='NEXT')

        method_id = record.get('method_id')
        method = get_method(method_id)
        if method is not None:
            pdf.cell(0, 8, f'Метод: {method.name} ({method.standard})',
                     new_x='LMARGIN', new_y='NEXT')
        else:
            pdf.cell(0, 8, f'Метод: {method_id}',
                     new_x='LMARGIN', new_y='NEXT')

        f0 = record.get('f0')
        if f0:
            pdf.cell(0, 8,
                     'Резонансная частота свободного резонатора: '
                     f'{float(f0) / 1e9:.4f} ГГц;',
                     new_x='LMARGIN', new_y='NEXT')
        params_line = _format_params(record)
        if params_line:
            pdf.multi_cell(0, 8, params_line + ';')
        pdf.cell(0, 8, 'Допуск: -;', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(6)

        # --- расчётные данные ---
        samples: List[Dict] = record.get('samples') or []
        pdf.set_font('T', 'B', 12)
        pdf.cell(0, 10, 'Расчётные данные:', new_x='LMARGIN', new_y='NEXT')

        headings = ('№', 'Наименование образца',
                    'Частота резонанса, ГГц',
                    'Тангенс угла потерь, 10^-4',
                    'Диэлектрическая проницаемость')
        widths = (10, 45, 40, 40, 45)
        pdf.set_font('T', '', 10)
        rows = [headings]
        for i, s in enumerate(samples, 1):
            fe, tgo, e = s.get('fe'), s.get('tgo'), s.get('e')
            rows.append((
                str(i), str(s.get('name') or i),
                f'{float(fe) / 1e9:.4f}' if fe else '-',
                f'{float(tgo) * 1e4:.3f}' if tgo is not None else '-',
                f'{float(e):.5f}' if e is not None else '-'))
        with pdf.table(col_widths=widths, width=sum(widths),
                       text_align='CENTER',
                       headings_style=FontFace(emphasis='BOLD')) as table:
            for data_row in rows:
                row = table.row()
                for cell in data_row:
                    row.cell(cell)

        pdf.ln(12)
        pdf.set_font('T', 'B', 12)
        pdf.cell(0, 10, 'Измерение провёл: _____________________',
                 new_x='LMARGIN', new_y='NEXT')

        # --- подвал ---
        pdf.set_auto_page_break(False)
        pdf.set_y(-24)
        pdf.set_font('T', '', 8)
        pdf.cell(0, 5,
                 'Отчёт составлен на основе измерений '
                 f'программно-аппаратного комплекса {APP_NAME}.',
                 new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 5,
                 f'Версия: {APP_VERSION}. '
                 f'Отчёт в системе: #{record["measure_id"]}',
                 new_x='LMARGIN', new_y='NEXT')

        self.out_dir.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', str(title))
        out = Path(out_path) if out_path else self.out_dir / f'{safe_title}.pdf'
        pdf.output(str(out))
        return str(out)
