from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from openpyxl import load_workbook

PROJECT_ROOT = Path(__file__).resolve().parent


def resolve_lookup_workbook_path() -> Path:
    """Resolve the workbook path in a portable, case-insensitive way."""
    candidate_dirs = [
        PROJECT_ROOT / "input",
        PROJECT_ROOT / "Input",
        PROJECT_ROOT / "lookup",
        PROJECT_ROOT / "Lookup",
        PROJECT_ROOT,
    ]

    for directory in candidate_dirs:
        candidate = directory / "PowerApp_Lookup.xlsx"
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Could not locate PowerApp_Lookup.xlsx. Expected one of: "
        + ", ".join(str(path / "PowerApp_Lookup.xlsx") for path in candidate_dirs)
    )


def load_lookup_tables(workbook_path: str | Path | None = None) -> Dict[str, List[Dict[str, Any]]]:
    """Load all worksheet rows from the lookup workbook into a normalized dictionary."""
    workbook_file = Path(workbook_path) if workbook_path is not None else resolve_lookup_workbook_path()
    workbook = load_workbook(workbook_file, data_only=True)

    lookup_tables: Dict[str, List[Dict[str, Any]]] = {}
    for sheet in workbook.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue

        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        data_rows: List[Dict[str, Any]] = []

        for row in rows[1:]:
            if not any(cell is not None and str(cell).strip() for cell in row):
                continue

            normalized_row: Dict[str, Any] = {}
            for idx, header in enumerate(headers):
                if idx < len(row):
                    normalized_row[header] = row[idx]
            data_rows.append(normalized_row)

        lookup_tables[sheet.title] = data_rows

    return lookup_tables
