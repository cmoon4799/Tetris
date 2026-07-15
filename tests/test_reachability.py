from fixtures.layouts import apply_layout_to_matrix, load_layout_rows
from matrix import Matrix
from piece import ActivePiece, get_anchor
from planning.placements import generate_potential_final_positions
from planning.reachability import map_reachable_positions_to_actions
from shared import CONFIG, Action, Color, PieceOrientation, PieceType


def make_matrix() -> Matrix:
    return Matrix(
        matrix_width=CONFIG.matrix_width,
        matrix_height=(CONFIG.matrix_height + CONFIG.buffer_height),
    )


def test_reachability_allows_passing_through_resting_position_without_hard_drop() -> None:
    matrix = make_matrix()
    matrix[2][2] = Color.DARK_BLUE
    matrix[3][2] = Color.DARK_BLUE

    current_position = ((4, 0), (4, 1), (3, 0), (3, 1))
    current_orientation = PieceOrientation.NORTH
    potential_positions = generate_potential_final_positions(matrix, PieceType.O_PIECE)

    positions_to_actions = map_reachable_positions_to_actions(
        matrix=matrix,
        current_position=current_position,
        current_orientation=current_orientation,
        piece_type=PieceType.O_PIECE,
        potential_positions=potential_positions,
    )

    target_position = ((1, 1), (1, 2), (0, 1), (0, 2))
    final_position = (
        get_anchor(PieceType.O_PIECE, target_position, PieceOrientation.NORTH),
        PieceOrientation.NORTH,
    )

    assert final_position in positions_to_actions
    assert positions_to_actions[final_position] == (
        Action.SOFT_DROP,
        Action.SOFT_DROP,
        Action.SOFT_DROP,
        Action.RIGHT_SHIFT,
    )


def test_reachability_includes_bottom_of_t_spin_well() -> None:
    matrix = make_matrix()
    layout_rows = load_layout_rows("t_spin_well")
    apply_layout_to_matrix(matrix, layout_rows)

    active_piece = ActivePiece(PieceType.T_PIECE)
    potential_positions = generate_potential_final_positions(matrix, PieceType.T_PIECE)

    positions_to_actions = map_reachable_positions_to_actions(
        matrix=matrix,
        current_position=active_piece.position,
        current_orientation=active_piece.orientation,
        piece_type=PieceType.T_PIECE,
        potential_positions=potential_positions,
    )

    assert ((4, 0), PieceOrientation.EAST) in positions_to_actions
