from collections import deque

from matrix import Matrix
from piece import (
    get_anchor,
    get_rotated_position,
    get_translated_position,
    rotate_orientation,
)
from shared import (
    Action,
    PieceOrientation,
    PieceType,
    Rotation,
    TranslateDirection,
)


def _normalize_position(position: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(position))


def _get_potential_position(
    piece_type: PieceType,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
) -> tuple[tuple[int, int], PieceOrientation]:
    return (get_anchor(piece_type, position, orientation), orientation)


def _get_hard_drop_position(
    matrix: Matrix,
    position: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, int], ...]:
    current_position = position
    shifted_position = get_translated_position(TranslateDirection.DOWN, current_position, matrix)
    while shifted_position is not None:
        current_position = shifted_position
        shifted_position = get_translated_position(
            TranslateDirection.DOWN, current_position, matrix
        )

    return current_position


def map_reachable_positions_to_actions(
    matrix: Matrix,
    current_position: tuple[tuple[int, int], ...],
    current_orientation: PieceOrientation,
    piece_type: PieceType,
    potential_positions: list[tuple[tuple[int, int], PieceOrientation]],
) -> dict[tuple[tuple[int, int], PieceOrientation], tuple[Action, ...]]:
    """Return a mapping of reachable final placement positions to the shortest sequence of actions
    required to get it there.
    """

    current_position = tuple(sorted(current_position))
    potential_positions = set(potential_positions)
    position_to_actions: dict[tuple[tuple[int, int], PieceOrientation], tuple[Action, ...]] = {}

    queue = deque([(current_position, current_orientation, (), False)])
    seen_states = {(current_position, current_orientation, False)}

    def enqueue_state(
        position: tuple[tuple[int, int], ...],
        orientation: PieceOrientation,
        action_history: tuple[Action, ...],
        hard_dropped: bool,
    ) -> None:
        state = (position, orientation, hard_dropped)
        if state in seen_states:
            return

        seen_states.add(state)
        queue.append((position, orientation, action_history, hard_dropped))

    actions = (
        Action.HARD_DROP,
        Action.LEFT_SHIFT,
        Action.RIGHT_SHIFT,
        Action.SOFT_DROP,
        Action.CW_ROTATE,
        Action.CCW_ROTATE,
    )

    while queue:
        position, orientation, action_history, hard_dropped = queue.popleft()
        potential_position = _get_potential_position(piece_type, position, orientation)

        # record the action history only if the position is a final placement position
        # and a shorter sequence has not been recorded
        if (
            potential_position in potential_positions
            and potential_position not in position_to_actions
        ):
            position_to_actions[potential_position] = action_history
            if len(position_to_actions) == len(potential_positions):
                break

        if hard_dropped:
            continue

        for action in actions:
            match action:
                case Action.LEFT_SHIFT:
                    new_position = get_translated_position(
                        TranslateDirection.LEFT, position, matrix
                    )
                    if new_position is not None:
                        enqueue_state(
                            _normalize_position(new_position),
                            orientation,
                            action_history + (action,),
                            False,
                        )
                case Action.RIGHT_SHIFT:
                    new_position = get_translated_position(
                        TranslateDirection.RIGHT, position, matrix
                    )
                    if new_position is not None:
                        enqueue_state(
                            _normalize_position(new_position),
                            orientation,
                            action_history + (action,),
                            False,
                        )
                case Action.SOFT_DROP:
                    new_position = get_translated_position(
                        TranslateDirection.DOWN, position, matrix
                    )
                    if new_position is not None:
                        enqueue_state(
                            _normalize_position(new_position),
                            orientation,
                            action_history + (action,),
                            False,
                        )
                case Action.HARD_DROP:
                    new_position = _normalize_position(_get_hard_drop_position(matrix, position))
                    new_potential_position = _get_potential_position(
                        piece_type, new_position, orientation
                    )
                    if new_potential_position in potential_positions:
                        enqueue_state(
                            new_position,
                            orientation,
                            action_history + (action,),
                            True,
                        )
                case Action.CW_ROTATE:
                    new_position = get_rotated_position(
                        position=position,
                        piece_type=piece_type,
                        rotation=Rotation.CW,
                        orientation=orientation,
                        matrix=matrix,
                    )
                    if new_position is not None:
                        new_position = _normalize_position(new_position)
                        new_orientation = rotate_orientation(
                            orientation=orientation, rotation=Rotation.CW
                        )
                        enqueue_state(
                            new_position,
                            new_orientation,
                            action_history + (action,),
                            False,
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
                        new_position = _normalize_position(new_position)
                        new_orientation = rotate_orientation(
                            orientation=orientation, rotation=Rotation.CCW
                        )
                        enqueue_state(
                            new_position,
                            new_orientation,
                            action_history + (action,),
                            False,
                        )

    return position_to_actions


if __name__ == "__main__":
    import pygame

    from fixtures.layouts import apply_layout_to_matrix, load_layout_rows
    from piece import ActivePiece, generate_anchor_relative_position
    from planning.placements import generate_potential_final_positions
    from render import Renderer
    from shared import CONFIG, Color, Observation

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

    final_placement_positions = generate_potential_final_positions(matrix, PieceType.L_PIECE)

    active_piece = ActivePiece(PieceType.L_PIECE)

    position_to_actions = map_reachable_positions_to_actions(
        matrix=matrix,
        current_position=active_piece.position,
        current_orientation=active_piece.orientation,
        piece_type=PieceType.L_PIECE,
        potential_positions=final_placement_positions,
    )

    for final_position in final_placement_positions:
        if final_position not in position_to_actions:
            continue
        action_sequence = position_to_actions[final_position]
        active_piece = ActivePiece(PieceType.L_PIECE)
        anchor, orientation = final_position

        matrix_copy = matrix.clone()
        position = generate_anchor_relative_position(PieceType.L_PIECE, orientation, anchor)
        for row, col in position:
            matrix_copy[row][col] = Color.PINK

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
