from collections import deque

import pygame

from fixtures.layouts import apply_layout_to_matrix, load_layout_rows
from matrix import Matrix
from piece import (
    ActivePiece,
    get_rotated_position,
    get_translated_position,
    rotate_orientation,
)
from planning.placements import generate_initial_final_placement_positions
from render import Renderer
from shared import (
    CONFIG,
    Action,
    Color,
    Observation,
    PieceOrientation,
    PieceType,
    Rotation,
    TranslateDirection,
)


def map_reachable_placements_to_actions(
    matrix: Matrix,
    current_position: tuple[tuple[int, int], ...],
    current_orientation: PieceOrientation,
    piece_type: PieceType,
    final_placement_positions: list[tuple[tuple[int, int], ...]],
) -> dict[tuple[tuple[int, int], ...], tuple[Action, ...]]:
    """Return a mapping of reachable final placement positions to the shortest sequence of actions
    required to get it there.
    """

    current_position = tuple(sorted(current_position))
    final_placement_positions = set(final_placement_positions)
    position_to_actions: dict[tuple[tuple[int, int], ...], tuple[Action, ...]] = {}

    queue = deque([(current_position, current_orientation, ())])
    seen_positions = set()

    actions = (
        Action.HARD_DROP,
        Action.LEFT_SHIFT,
        Action.RIGHT_SHIFT,
        Action.SOFT_DROP,
        Action.CW_ROTATE,
        Action.CCW_ROTATE,
    )

    while queue:
        position, orientation, action_history = queue.popleft()

        print(position, action_history)

        # record the action history only if the position is a final placement position
        # and a shorter sequence has not been recorded
        if position in final_placement_positions and position not in position_to_actions:
            position_to_actions[position] = action_history

        # end progression if the last action was not a hard drop
        if action_history and action_history[-1] == Action.HARD_DROP:
            continue

        for action in actions:
            match action:
                case Action.LEFT_SHIFT:
                    new_position = get_translated_position(
                        TranslateDirection.LEFT, position, matrix
                    )
                    if new_position is not None:
                        new_position = tuple(sorted(new_position))
                        if new_position not in seen_positions:
                            seen_positions.add(new_position)
                            queue.append((new_position, orientation, action_history + (action,)))
                case Action.RIGHT_SHIFT:
                    new_position = get_translated_position(
                        TranslateDirection.RIGHT, position, matrix
                    )
                    if new_position is not None:
                        new_position = tuple(sorted(new_position))
                        if new_position not in seen_positions:
                            seen_positions.add(new_position)
                            queue.append((new_position, orientation, action_history + (action,)))
                case Action.SOFT_DROP:
                    new_position = get_translated_position(
                        TranslateDirection.DOWN, position, matrix
                    )
                    if new_position is not None:
                        new_position = tuple(sorted(new_position))
                        if new_position not in seen_positions:
                            seen_positions.add(new_position)
                            queue.append((new_position, orientation, action_history + (action,)))
                case Action.HARD_DROP:
                    new_position = position
                    shifted_position = get_translated_position(
                        TranslateDirection.DOWN, position, matrix
                    )
                    while shifted_position is not None and not matrix.check_collision(
                        shifted_position
                    ):
                        new_position = shifted_position
                        shifted_position = get_translated_position(
                            TranslateDirection.DOWN, shifted_position, matrix
                        )
                    new_position = tuple(sorted(new_position))
                    if new_position in final_placement_positions:
                        queue.append((new_position, orientation, action_history + (action,)))
                case Action.CW_ROTATE:
                    new_position = get_rotated_position(
                        position=position,
                        piece_type=piece_type,
                        rotation=Rotation.CW,
                        orientation=orientation,
                        matrix=matrix,
                    )
                    if new_position is not None:
                        new_position = tuple(sorted(new_position))
                        new_orientation = rotate_orientation(
                            orientation=orientation, rotation=Rotation.CW
                        )
                        if new_position not in seen_positions:
                            seen_positions.add(new_position)
                            queue.append(
                                (new_position, new_orientation, action_history + (action,))
                            )
                case Action.CCW_ROTATE:
                    new_position = get_rotated_position(
                        position=position,
                        piece_type=piece_type,
                        rotation=Rotation.CCW,
                        orientation=orientation,
                        matrix=matrix,
                    )
                    if new_position is not None:
                        new_position = tuple(sorted(new_position))
                        new_orientation = rotate_orientation(
                            orientation=orientation, rotation=Rotation.CCW
                        )
                        if new_position not in seen_positions:
                            seen_positions.add(new_position)
                            queue.append(
                                (new_position, new_orientation, action_history + (action,))
                            )

    return position_to_actions


if __name__ == "__main__":

    def generate_observation(matrix: Matrix, active_piece: ActivePiece):
        return Observation(
            matrix=matrix.snapshot(),
            active_piece_type=active_piece.piece_type,
            active_piece_position=active_piece.position,
            active_piece_orientation=active_piece.orientation,
            held_piece=None,
            hold_disabled=True,
            action_mask=tuple(False for _ in range(7)),
            piece_queue=tuple(PieceType.L_PIECE for _ in range(CONFIG.visible_queue_size)),
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

    matrix = Matrix(
        matrix_width=CONFIG.matrix_width,
        matrix_height=(CONFIG.matrix_height + CONFIG.buffer_height),
    )

    layout_rows = load_layout_rows("l_spin_well")
    apply_layout_to_matrix(matrix, layout_rows)

    pygame.init()
    renderer = Renderer()
    clock = pygame.time.Clock()

    final_placement_positions = generate_initial_final_placement_positions(
        matrix, PieceType.L_PIECE
    )

    active_piece = ActivePiece(PieceType.L_PIECE)

    placements_to_actions = map_reachable_placements_to_actions(
        matrix=matrix,
        current_position=active_piece.position,
        current_orientation=active_piece.orientation,
        piece_type=PieceType.L_PIECE,
        final_placement_positions=final_placement_positions,
    )

    for position in final_placement_positions:
        if position not in final_placement_positions:
            continue
        action_sequence = placements_to_actions[position]
        active_piece = ActivePiece(PieceType.L_PIECE)

        matrix_copy = matrix.clone()
        for row, col in position:
            matrix_copy[row][col] = Color.PINK

        print(position, action_sequence)

        renderer.render(generate_observation(matrix_copy, active_piece))
        for action in action_sequence:
            match action:
                case Action.LEFT_SHIFT:
                    active_piece.translate(TranslateDirection.LEFT, matrix)
                case Action.RIGHT_SHIFT:
                    active_piece.translate(TranslateDirection.RIGHT, matrix)
                case Action.SOFT_DROP:
                    active_piece.translate(TranslateDirection.DOWN, matrix)
                case Action.HARD_DROP:
                    while active_piece.translate(TranslateDirection.DOWN, matrix):
                        pass
                case Action.CW_ROTATE:
                    active_piece.rotate(Rotation.CW, matrix)
                case Action.CCW_ROTATE:
                    active_piece.rotate(Rotation.CCW, matrix)

            renderer.render(generate_observation(matrix_copy, active_piece))

            clock.tick(10)
