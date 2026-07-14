import os

import pygame
import pytest

from matrix import Matrix
from piece import ActivePiece, Rotation, rotate_orientation
from render import Renderer
from shared import CONFIG, Color, Observation, PieceOrientation, PieceType


def make_matrix() -> Matrix:
    return Matrix(
        matrix_width=CONFIG.matrix_width,
        matrix_height=(CONFIG.matrix_height + CONFIG.buffer_height),
    )


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


def test_random():
    if os.getenv("TETRIS_TINKER_RENDER") != "1":
        pytest.skip("Set TETRIS_TINKER_RENDER=1 to run interactive render tinker test")

    matrix = make_matrix()
    for col in range(CONFIG.matrix_width):
        matrix[0][col] = Color.DARK_BLUE

    renderer = Renderer()
    observation = Observation(
        matrix=matrix.snapshot(),
        active_piece_type=PieceType.L_PIECE,
        active_piece_position=((20, 5), (19, 5), (18, 5), (18, 6)),
        active_piece_orientation=PieceOrientation.NORTH,
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

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        renderer.render(observation)
        clock.tick(CONFIG.fps)

    pygame.quit()
