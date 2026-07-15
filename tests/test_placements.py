from matrix import Matrix
from planning.placements import generate_initial_final_placement_positions
from shared import CONFIG, Color, PieceType


def make_matrix() -> Matrix:
    return Matrix(
        matrix_width=CONFIG.matrix_width,
        matrix_height=(CONFIG.matrix_height + CONFIG.buffer_height),
    )


def test_empty_board_o_piece_has_one_floor_row_of_placements() -> None:
    matrix = make_matrix()

    placements = generate_initial_final_placement_positions(matrix, PieceType.O_PIECE)

    assert len(placements) == CONFIG.matrix_width - 1
    assert all(min(row for row, _ in placement) == 0 for placement in placements)


def test_empty_board_i_piece_includes_horizontal_and_vertical_floor_placements() -> None:
    matrix = make_matrix()

    placements = generate_initial_final_placement_positions(matrix, PieceType.I_PIECE)

    assert len(placements) == (CONFIG.matrix_width - 3) + CONFIG.matrix_width


def test_stack_creates_supported_placement_above_matrix_floor() -> None:
    matrix = make_matrix()
    for col in range(4):
        matrix[0][col] = Color.DARK_BLUE

    placements = generate_initial_final_placement_positions(matrix, PieceType.I_PIECE)

    assert any(set(placement) == {(1, 0), (1, 1), (1, 2), (1, 3)} for placement in placements)
