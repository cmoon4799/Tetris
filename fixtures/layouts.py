import json
from pathlib import Path

from matrix import Matrix
from shared import CONFIG, Color

LAYOUT_FILE = Path(__file__).parent / "render_layouts.json"
LAYOUT_SYMBOL_TO_COLOR: dict[str, Color | None] = {
    ".": None,
    "#": Color.DARK_BLUE,
}


def load_layout_rows(layout_name: str) -> list[str]:
    with LAYOUT_FILE.open("r", encoding="utf-8") as f:
        layouts = json.load(f)

    if layout_name not in layouts:
        raise ValueError(f"Unknown layout '{layout_name}' in {LAYOUT_FILE}")

    rows = layouts[layout_name]["rows"]
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"Layout '{layout_name}' must contain non-empty 'rows'.")

    return rows


def apply_layout_to_matrix(matrix: Matrix, rows: list[str]) -> None:
    for row, row_text in enumerate(rows):
        if len(row_text) != CONFIG.matrix_width:
            raise ValueError(
                f"Layout row width mismatch at row {row}; expected {CONFIG.matrix_width}, got {len(row_text)}"
            )

        matrix_row = len(rows) - 1 - row

        for col, symbol in enumerate(row_text):
            if symbol not in LAYOUT_SYMBOL_TO_COLOR:
                raise ValueError(f"Unknown symbol '{symbol}' at ({row}, {col}) in layout")
            color = LAYOUT_SYMBOL_TO_COLOR[symbol]
            if color is not None:
                matrix[matrix_row][col] = color
