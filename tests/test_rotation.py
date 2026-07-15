import os

import pygame
import pytest

from fixtures.layouts import apply_layout_to_matrix, load_layout_rows
from matrix import Matrix
from piece import ActivePiece, rotate_orientation
from render import Renderer
from shared import (
    CONFIG,
    Observation,
    PieceOrientation,
    PieceType,
    Rotation,
)


def make_matrix() -> Matrix:
    return Matrix(
        matrix_width=CONFIG.matrix_width,
        matrix_height=(CONFIG.matrix_height + CONFIG.buffer_height),
    )


def generate_observation(matrix, active_piece: ActivePiece) -> Observation:
    """Generate a dummy observation for the renderer for purely visual purposes."""

    return Observation(
        matrix=matrix.snapshot(),
        active_piece_type=active_piece.piece_type,
        active_piece_position=active_piece.position,
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


def maybe_visualize_rotation(
    matrix: Matrix,
    active_piece: ActivePiece,
    rotation_sequence: list[Rotation],
) -> None:
    if os.getenv("TETRIS_TINKER_RENDER") != "1":
        for rotation in rotation_sequence:
            active_piece.rotate(rotation, matrix=matrix)
        return

    pygame.init()
    renderer = Renderer()
    clock = pygame.time.Clock()

    rotation_queue = list(rotation_sequence)
    last_rotation_tick = pygame.time.get_ticks()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        renderer.render(generate_observation(matrix, active_piece))

        now = pygame.time.get_ticks()
        if rotation_queue and now - last_rotation_tick >= 500:
            active_piece.rotate(rotation_queue.pop(0), matrix=matrix)
            last_rotation_tick = now

        clock.tick(CONFIG.fps)

    for rotation in rotation_queue:
        active_piece.rotate(rotation, matrix=matrix)

    pygame.quit()


def test_rotate_orientation_cycles_back_after_four_cw_turns() -> None:
    orientation = PieceOrientation.NORTH
    for _ in range(4):
        orientation = rotate_orientation(orientation, Rotation.CW)

    assert orientation == PieceOrientation.NORTH


def test_rotate_orientation_cycles_back_after_four_ccw_turns() -> None:
    orientation = PieceOrientation.NORTH
    for _ in range(4):
        orientation = rotate_orientation(orientation, Rotation.CCW)

    assert orientation == PieceOrientation.NORTH


def test_rotate_orientation_clockwise_path() -> None:
    orientation = PieceOrientation.NORTH

    orientation = rotate_orientation(orientation, Rotation.CW)
    assert orientation == PieceOrientation.EAST

    orientation = rotate_orientation(orientation, Rotation.CW)
    assert orientation == PieceOrientation.SOUTH

    orientation = rotate_orientation(orientation, Rotation.CW)
    assert orientation == PieceOrientation.WEST

    orientation = rotate_orientation(orientation, Rotation.CW)
    assert orientation == PieceOrientation.NORTH


def test_rotate_orientation_counterclockwise_path() -> None:
    orientation = PieceOrientation.NORTH

    orientation = rotate_orientation(orientation, Rotation.CCW)
    assert orientation == PieceOrientation.WEST

    orientation = rotate_orientation(orientation, Rotation.CCW)
    assert orientation == PieceOrientation.SOUTH

    orientation = rotate_orientation(orientation, Rotation.CCW)
    assert orientation == PieceOrientation.EAST

    orientation = rotate_orientation(orientation, Rotation.CCW)
    assert orientation == PieceOrientation.NORTH


@pytest.mark.parametrize(
    "piece_type",
    [
        PieceType.I_PIECE,
        PieceType.T_PIECE,
        PieceType.J_PIECE,
        PieceType.L_PIECE,
        PieceType.S_PIECE,
        PieceType.Z_PIECE,
    ],
)
def test_rotatable_pieces_can_rotate_clockwise_from_spawn(piece_type: PieceType) -> None:
    matrix = make_matrix()
    piece = ActivePiece(piece_type)

    success = piece.rotate(Rotation.CW, matrix)

    assert success
    assert piece.orientation == PieceOrientation.EAST


@pytest.mark.parametrize(
    "piece_type",
    [
        PieceType.I_PIECE,
        PieceType.T_PIECE,
        PieceType.J_PIECE,
        PieceType.L_PIECE,
        PieceType.S_PIECE,
        PieceType.Z_PIECE,
    ],
)
def test_cw_then_ccw_returns_piece_to_start(piece_type: PieceType) -> None:
    matrix = make_matrix()
    piece = ActivePiece(piece_type)
    start_position = set(piece.position)
    start_orientation = piece.orientation

    assert piece.rotate(Rotation.CW, matrix)
    assert piece.rotate(Rotation.CCW, matrix)

    assert set(piece.position) == start_position
    assert piece.orientation == start_orientation


def test_l_spin():
    matrix = make_matrix()
    layout_rows = load_layout_rows("l_spin_well")
    apply_layout_to_matrix(matrix, layout_rows)

    active_piece = ActivePiece(piece_type=PieceType.L_PIECE)
    active_piece.orientation = PieceOrientation.WEST
    active_piece.position = ((7, 7), (7, 8), (6, 8), (5, 8))
    rotation_sequence = [Rotation.CW, Rotation.CW]

    maybe_visualize_rotation(
        matrix,
        active_piece,
        rotation_sequence=rotation_sequence,
    )

    assert set(active_piece.position) == set(((2, 6), (2, 7), (3, 6), (4, 6)))


def test_t_spin_overhang():
    matrix = make_matrix()
    layout_rows = load_layout_rows("t_spin_overhang")
    apply_layout_to_matrix(matrix, layout_rows)

    active_piece = ActivePiece(piece_type=PieceType.T_PIECE)
    active_piece.orientation = PieceOrientation.WEST
    active_piece.position = ((3, 2), (3, 3), (4, 3), (2, 3))
    rotation_sequence = []
    rotation_sequence = [Rotation.CCW]

    maybe_visualize_rotation(
        matrix,
        active_piece,
        rotation_sequence=rotation_sequence,
    )

    assert set(active_piece.position) == set(((3, 2), (3, 3), (3, 4), (2, 3)))


def test_t_spin_well():
    matrix = make_matrix()
    layout_rows = load_layout_rows("t_spin_well")
    apply_layout_to_matrix(matrix, layout_rows)

    active_piece = ActivePiece(piece_type=PieceType.T_PIECE)
    active_piece.orientation = PieceOrientation.EAST
    active_piece.position = ((10, 1), (9, 1), (9, 2), (8, 1))
    rotation_sequence = [Rotation.CCW, Rotation.CCW, Rotation.CW, Rotation.CW]

    maybe_visualize_rotation(
        matrix,
        active_piece,
        rotation_sequence=rotation_sequence,
    )

    assert set(active_piece.position) == set(((4, 1), (3, 1), (3, 2), (2, 1)))
