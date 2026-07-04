from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

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
from shared import Action, RunOutcome


class TranslateDirection(Enum):
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


@dataclass(frozen=True)
class ActionResult:
    success: bool
    piece_generated: bool = False


class Engine:
    MATRIX_WIDTH = 10
    MATRIX_HEIGHT = 20
    BUFFER_HEIGHT = 5  # rendered space above the matrix skyline

    LINE_CLEAR_GOAL = 40

    def __init__(self, fall_frame_rate: int, lock_down_frame_rate: int):
        # visible queue of pieces; pieces in the queue are replaced with those from the piece_bag
        self.piece_queue: deque[PieceType] = deque(generate_random_bag())
        self.piece_bag: deque[PieceType] = deque(generate_random_bag())

        self.held_piece: PieceType | None = None
        self.hold_disabled: bool = False

        self.active_piece: ActivePiece | None = ActivePiece(self.piece_queue.popleft())
        self.matrix: Matrix = Matrix(
            matrix_width=self.MATRIX_WIDTH, matrix_height=(self.MATRIX_HEIGHT + self.BUFFER_HEIGHT)
        )
        self.action_queue = deque()

        self.fall_frame_rate = fall_frame_rate
        self.lock_down_frame_rate = lock_down_frame_rate
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0

        self.ACTION_TO_CONTROL_MAP: dict[Action, Callable[[], ActionResult]] = {
            Action.RIGHT_SHIFT: self.right_shift,
            Action.LEFT_SHIFT: self.left_shift,
            Action.HARD_DROP: self.hard_drop,
            Action.SOFT_DROP: self.soft_drop,
            Action.CW_ROTATE: self.cw_rotate,
            Action.CCW_ROTATE: self.ccw_rotate,
            Action.HOLD: self.hold_piece,
            Action.QUIT: self.quit,
            Action.FALL: self.fall,
            Action.LOCK_DOWN: self.lock_down,
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
        self.run_outcome: RunOutcome | None = None
        self.frame_ticks = 0

    def process_frame(self, actions: list[Action]) -> None:
        for action in actions:
            if not isinstance(action, Action) or action.restricted:
                raise ValueError(f"Provided input {action} is not a valid player action.")

        self.frame_ticks += 1
        if self.lock_down_active:
            self.lock_down_frame_ticks += 1

        self.action_queue.clear()
        self.action_queue.extend(actions)

        if self.lock_down_frame_ticks == self.lock_down_frame_rate and self.surface_contact():
            self.action_queue.appendleft(Action.LOCK_DOWN)
        if self.frame_ticks > 0 and self.frame_ticks % self.fall_frame_rate == 0:
            self.action_queue.appendleft(Action.FALL)

        while self.action_queue:
            action = self.action_queue.popleft()
            result = self.ACTION_TO_CONTROL_MAP[action]()

            if self.check_defeat_condition(result):
                break
            if self.check_win_condition(result):
                break

            # actions are presumed to be for the current active piece; if a new active piece is
            # generated, we ignore actions by exiting early
            if result.piece_generated:
                break

            if self.surface_contact():
                self.switch_on_lock_down()
            else:
                self.switch_off_lock_down()

            # in Infinite Lock Down, any successful movement action resets the lock down
            # frame counter
            if action in self.MOVEMENT_ACTIONS and result.success and self.lock_down_active:
                self.lock_down_frame_ticks = 0

    # --- State Management ---

    def switch_on_lock_down(self) -> None:
        if not self.lock_down_active:
            self.lock_down_frame_ticks = 0
        self.lock_down_active = True

    def switch_off_lock_down(self) -> None:
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0

    # --- Game Logic ---

    def check_defeat_condition(self, result: ActionResult) -> bool:
        """Check the defeat condition and returns whether the condition has been met."""

        if result.piece_generated and self.matrix.check_collision(self.active_piece.position):
            self.run_outcome = RunOutcome.DEFEAT
            self.running = False
            return True
        return False

    def check_win_condition(self, result: ActionResult) -> bool:
        """Check the victory condition and returns whether the condition has been met."""

        if self.matrix.lines_cleared >= self.LINE_CLEAR_GOAL:
            self.run_outcome = RunOutcome.VICTORY
            self.running = False
            return True
        return False

    def pull_active_piece_from_queue(self) -> None:
        self.switch_off_lock_down()

        self.active_piece = ActivePiece(self.piece_queue.popleft())
        self.piece_queue.append(self.piece_bag.popleft())
        if not self.piece_bag:
            self.piece_bag = deque(generate_random_bag())

    # --- Input Handlers ---

    def lock_down(self) -> ActionResult:
        """Lock down the active piece and pull the next active piece from the queue."""

        if not self.surface_contact():
            raise RuntimeError("lock_down must only be called on surface contact")

        for i, j in self.active_piece.position:
            self.matrix[i][j] = self.active_piece.color

        self.matrix.clear()

        self.hold_disabled = False

        self.pull_active_piece_from_queue()

        return ActionResult(True, True)

    def fall(self) -> ActionResult:
        new_position = self.get_active_piece_translation(TranslateDirection.DOWN)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position
            return ActionResult(True)
        return ActionResult(False)

    def left_shift(self) -> ActionResult:
        new_position = self.get_active_piece_translation(TranslateDirection.LEFT)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position
            return ActionResult(True)
        return ActionResult(False)

    def right_shift(self) -> ActionResult:
        new_position = self.get_active_piece_translation(TranslateDirection.RIGHT)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position
            return ActionResult(True)
        return ActionResult(False)

    def soft_drop(self) -> ActionResult:
        new_position = self.get_active_piece_translation(TranslateDirection.DOWN)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position
            return ActionResult(True)
        return ActionResult(False)

    def hard_drop(self) -> ActionResult:
        while not self.matrix.check_collision(
            self.get_active_piece_translation(TranslateDirection.DOWN)
        ):
            self.active_piece.position = self.get_active_piece_translation(TranslateDirection.DOWN)
        self.action_queue.appendleft(Action.LOCK_DOWN)
        return ActionResult(True)

    def cw_rotate(self) -> ActionResult:
        match self.active_piece.piece_type:
            case PieceType.I_PIECE:
                success = rotate_i_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.T_PIECE:
                success = rotate_t_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.L_PIECE:
                success = rotate_l_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.J_PIECE:
                success = rotate_j_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.S_PIECE:
                success = rotate_s_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.Z_PIECE:
                success = rotate_z_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.O_PIECE:
                success = False
        return ActionResult(success)

    def ccw_rotate(self) -> ActionResult:
        match self.active_piece.piece_type:
            case PieceType.I_PIECE:
                success = rotate_i_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.T_PIECE:
                success = rotate_t_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.L_PIECE:
                success = rotate_l_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.J_PIECE:
                success = rotate_j_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.S_PIECE:
                success = rotate_s_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.Z_PIECE:
                success = rotate_z_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.O_PIECE:
                success = False
        return ActionResult(success)

    def hold_piece(self) -> ActionResult:
        if self.hold_disabled:
            return ActionResult(False)

        if self.held_piece is None:
            self.held_piece = self.active_piece.piece_type
            self.pull_active_piece_from_queue()
        else:
            active_piece_type = self.active_piece.piece_type
            self.active_piece = ActivePiece(self.held_piece)
            self.held_piece = active_piece_type
        self.hold_disabled = True

        return ActionResult(True, True)

    def quit(self) -> ActionResult:
        self.running = False
        return ActionResult(True)

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
