from matrix import Matrix
from piece import generate_anchor_relative_position, get_translated_position
from shared import PieceOrientation, PieceType, TranslateDirection


def generate_potential_final_positions(
    matrix: Matrix, piece_type: PieceType
) -> list[tuple[tuple[int, int], PieceOrientation]]:
    """For a given matrix and piece type, generate potential final positions. Each final position
    will be of the form ((anchor_row, anchor_col), PieceOrientation).
    """

    final_positions = []

    # start the anchor below and to the left of the matrix
    min_anchor_row = -1
    max_anchor_row = matrix.matrix_height
    min_anchor_col = -4
    max_anchor_col = matrix.matrix_width

    for orientation in PieceOrientation:
        for anchor_row in range(min_anchor_row, max_anchor_row + 1):
            for anchor_col in range(min_anchor_col, max_anchor_col + 1):
                position = tuple(
                    generate_anchor_relative_position(
                        piece_type,
                        orientation,
                        (anchor_row, anchor_col),
                    )
                )

                if matrix.check_collision(position):
                    continue

                # check surface contact
                translated_down = get_translated_position(TranslateDirection.DOWN, position, matrix)
                if translated_down is not None:
                    continue

                final_positions.append(((anchor_row, anchor_col), orientation))

    return final_positions
