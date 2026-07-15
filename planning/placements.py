import pygame

from fixtures.layouts import apply_layout_to_matrix, load_layout_rows
from matrix import Matrix
from piece import ActivePiece, generate_anchor_relative_position
from render import Renderer
from shared import (
    CONFIG,
    Observation,
    PieceOrientation,
    PieceType,
)


def generate_initial_final_placement_positions(
    matrix: Matrix, piece_type: PieceType
) -> list[tuple[tuple[int, int], ...]]:
    """For a given matrix and piece type, generate the list of final placement positions."""

    seen_placements: set[tuple[tuple[int, int], ...]] = set()
    seen_shapes: set[tuple[tuple[int, int], ...]] = set()

    for orientation in PieceOrientation:
        relative_shape = tuple(
            sorted(generate_anchor_relative_position(piece_type, orientation, (0, 0)))
        )
        if relative_shape in seen_shapes:
            continue
        seen_shapes.add(relative_shape)

        min_rel_row = min(row for row, _ in relative_shape)
        max_rel_col = max(col for _, col in relative_shape)
        min_rel_col = min(col for _, col in relative_shape)

        min_anchor_row = -min_rel_row
        max_anchor_row = matrix.matrix_height - min_rel_row
        min_anchor_col = -min_rel_col
        max_anchor_col = matrix.matrix_width - 1 - max_rel_col

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

                translated_down = tuple((row - 1, col) for row, col in position)
                if not matrix.check_collision(translated_down):
                    continue

                normalized_position = tuple(sorted(position))
                if normalized_position in seen_placements:
                    continue

                seen_placements.add(normalized_position)

    placements = list(seen_placements)
    placements.sort(
        key=lambda position: (min(row for row, _ in position), min(col for _, col in position))
    )

    return placements


if __name__ == "__main__":
    print("????")
    matrix = Matrix(
        matrix_width=CONFIG.matrix_width,
        matrix_height=(CONFIG.matrix_height + CONFIG.buffer_height),
    )

    layout_rows = load_layout_rows("t_spin_well")
    apply_layout_to_matrix(matrix, layout_rows)

    pygame.init()
    renderer = Renderer()
    clock = pygame.time.Clock()

    for position in generate_initial_final_placement_positions(matrix, PieceType.I_PIECE):
        print(position)
        active_piece = ActivePiece(piece_type=PieceType.I_PIECE)

        observation = Observation(
            matrix=matrix.snapshot(),
            active_piece_type=active_piece.piece_type,
            active_piece_position=position,
            active_piece_orientation=active_piece.orientation,
            held_piece=None,
            hold_disabled=True,
            action_mask=tuple(False for _ in range(7)),
            piece_queue=tuple(PieceType.I_PIECE for _ in range(CONFIG.visible_queue_size)),
            gravity_frames_remaining=0,
            lock_down_active=False,
            lock_down_frames_remaining=0,
            lock_down_resets_remaining=0,
            lines_cleared=0,
            run_outcome=None,
            active_piece_rotations=0,
            active_piece_left_translations=0,
            active_piece_right_translations=0,
            active_piece_down_translations=0,
            active_piece_left_shifted=False,
            active_piece_right_shifted=False,
        )

        renderer.render(observation)

        clock.tick(2)
