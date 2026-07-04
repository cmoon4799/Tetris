from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

import pygame

from matrix import Matrix
from piece import (
    ActivePiece,
    PieceType,
    Rotation,
    generate_random_bag,
    rotate_i_piece,
    rotate_j_piece,
    rotate_l_piece,
    rotate_s_piece,
    rotate_t_piece,
    rotate_z_piece,
)
from shared import Action


class TranslateDirection(Enum):
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


@dataclass(frozen=True)
class ActionResult:
    success: bool
    new_piece_generated: bool = False
    game_over: bool = False


class Engine:
    MATRIX_WIDTH = 10
    MATRIX_HEIGHT = 20
    BUFFER_HEIGHT = 5

    def __init__(self):
        # visible queue of pieces; pieces in the queue are replaced with those from the piece_bag
        self.piece_queue: deque[PieceType] = deque(generate_random_bag())
        self.piece_bag: deque[PieceType] = deque(generate_random_bag())

        self.held_piece: PieceType | None = None
        self.hold_disabled: bool = False

        self.active_piece: ActivePiece | None = ActivePiece(PieceType.I_PIECE)
        self.matrix: Matrix = Matrix(
            matrix_width=self.MATRIX_WIDTH, matrix_height=(self.MATRIX_HEIGHT + self.BUFFER_HEIGHT)
        )

        pygame.init()

        self.clock = pygame.time.Clock()
        self.fps = 60  # frames per second
        self.frame_ticks = 0

        self.fall_speed = 0.8  # time in seconds it takes for the active piece to fall by one line
        self.fall_frame_rate = round(self.fall_speed * self.fps)

        self.lock_down_speed = 0.5  # time in seconds until piece is locked
        self.lock_down_frame_rate = round(self.lock_down_speed * self.fps)
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0

        self.ACTION_TO_CONTROL_MAP = {
            Action.RIGHT_SHIFT: self.right_shift,
            Action.LEFT_SHIFT: self.left_shift,
            Action.HARD_DROP: self.hard_drop,
            Action.SOFT_DROP: self.soft_drop,
            Action.CW_ROTATE: self.cw_rotate,
            Action.CCW_ROTATE: self.ccw_rotate,
            Action.HOLD: self.hold_piece,
            Action.FALL: self.fall,
            Action.QUIT: self.quit,
        }
        self.MOVEMENT_ACTIONS = {
            Action.RIGHT_SHIFT,
            Action.LEFT_SHIFT,
            Action.SOFT_DROP,
            Action.HARD_DROP,
            Action.CW_ROTATE,
            Action.CCW_ROTATE,
        }

        self.running = True

    def process_frame(self, actions: list[Action]) -> None:
        self.frame_ticks += 1
        self.lock_down_frame_ticks += 1

        if self.lock_down_frame_ticks == self.lock_down_frame_rate and self.surface_contact():
            self.lock_down()
        else:
            if self.frame_ticks > 0 and self.frame_ticks % self.fall_frame_rate == 0:
                actions = [Action.FALL, *actions]
            for action in actions:
                # actions are presumed to be for the current active piece; because lock down
                # generates a new active piece, we ignore actions by exiting early
                self.ACTION_TO_CONTROL_MAP[action]()

                if self.surface_contact():
                    self.switch_on_lock_down()
                if self.lock_down_active:
                    if action in self.MOVEMENT_ACTIONS:
                        self.lock_down_frame_ticks = 0

            self.matrix.clear()

        self.clock.tick(self.fps)

    # --- State Management ---

    def switch_on_lock_down(self) -> None:
        """Activate lock-down timer."""
        if not self.lock_down_active:
            self.lock_down_frame_ticks = 0
        self.lock_down_active = True

    def switch_off_lock_down(self) -> None:
        """Deactivate lock-down timer."""
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0

    # --- Game Logic ---

    def pull_active_piece_from_queue(self) -> None:
        self.switch_off_lock_down()

        self.active_piece = ActivePiece(self.piece_queue.popleft())
        self.piece_queue.append(self.piece_bag.popleft())
        if not self.piece_bag:
            self.piece_bag = deque(generate_random_bag())

        # this particular lose condition is known as "Block Out", meaning
        # the new active piece spawns in a position that collides with
        # the existing cells of the matrix
        if self.matrix.check_collision(self.active_piece.position):
            self.running = False

    def lock_down(self) -> None:
        """Lock down the active piece and pull the next active piece from the queue."""

        if not self.surface_contact():
            raise RuntimeError("lock_down must only be called on surface contact")

        for i, j in self.active_piece.position:
            self.matrix[i][j] = self.active_piece.color

        self.matrix.clear()

        self.hold_disabled = False

        self.pull_active_piece_from_queue()

    def fall(self) -> None:
        new_position = self.get_active_piece_translation(TranslateDirection.DOWN)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position

    # --- Input Handlers ---

    def left_shift(self) -> ActionResult:
        new_position = self.get_active_piece_translation(TranslateDirection.LEFT)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position
            return ActionResult(True)
        else:
            return ActionResult(False)

    def right_shift(self) -> None:
        new_position = self.get_active_piece_translation(TranslateDirection.RIGHT)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position
            return ActionResult(True)
        else:
            return ActionResult(False)

    def soft_drop(self) -> None:
        new_position = self.get_active_piece_translation(TranslateDirection.DOWN)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position
            return ActionResult(True)
        else:
            return ActionResult(False)

    def hard_drop(self) -> None:
        while not self.matrix.check_collision(
            self.get_active_piece_translation(TranslateDirection.DOWN)
        ):
            self.active_piece.position = self.get_active_piece_translation(TranslateDirection.DOWN)
        self.lock_down()

    def cw_rotate(self) -> None:
        match self.active_piece.piece_type:
            case PieceType.I_PIECE:
                rotate_i_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.T_PIECE:
                rotate_t_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.L_PIECE:
                rotate_l_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.J_PIECE:
                rotate_j_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.S_PIECE:
                rotate_s_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.Z_PIECE:
                rotate_z_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.O_PIECE:
                pass  # no rotation for O piece

    def ccw_rotate(self) -> None:
        match self.active_piece.piece_type:
            case PieceType.I_PIECE:
                rotate_i_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.T_PIECE:
                rotate_t_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.L_PIECE:
                rotate_l_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.J_PIECE:
                rotate_j_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.S_PIECE:
                rotate_s_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.Z_PIECE:
                rotate_z_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.O_PIECE:
                pass  # no rotation for O piece

    def hold_piece(self) -> None:
        if self.hold_disabled:
            return

        if self.held_piece is None:
            self.held_piece = self.active_piece.piece_type
            self.pull_active_piece_from_queue()
        else:
            active_piece_type = self.active_piece.piece_type
            self.active_piece = ActivePiece(self.held_piece)
            self.held_piece = active_piece_type
        self.hold_disabled = True

    # --- Utilities ---

    def get_active_piece_translation(self, direction: TranslateDirection) -> list[tuple[int, int]]:
        match direction:
            case TranslateDirection.DOWN:
                return [(i - 1, j) for (i, j) in self.active_piece.position]
            case TranslateDirection.LEFT:
                return [(i, j - 1) for (i, j) in self.active_piece.position]
            case TranslateDirection.RIGHT:
                return [(i, j + 1) for (i, j) in self.active_piece.position]

    def surface_contact(self) -> bool:
        new_position = self.get_active_piece_translation(TranslateDirection.DOWN)
        return self.matrix.check_collision(new_position)

    def quit(self) -> None:
        self.running = False
