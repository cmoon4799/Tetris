from collections import deque
from dataclasses import dataclass
from random import Random
from typing import Callable

from matrix import Matrix
from piece import (
    ActivePiece,
    Rotation,
    generate_random_bag,
)
from shared import (
    CONFIG,
    PLAYER_ACTION_SPACE,
    Action,
    Observation,
    PieceType,
    RunOutcome,
    TranslateDirection,
)


@dataclass(frozen=True)
class ActionResult:
    success: bool
    piece_generated: bool = False


class Engine:
    LINE_CLEAR_GOAL = CONFIG.line_clear_goal
    MATRIX_HEIGHT = CONFIG.matrix_height
    MATRIX_WIDTH = CONFIG.matrix_width
    BUFFER_HEIGHT = CONFIG.buffer_height  # buffer above the matrix skyline
    FPS = CONFIG.fps
    GRAVITY_SPEED = CONFIG.gravity_speed
    LOCK_DOWN_SPEED = CONFIG.lock_down_speed
    LOCK_DOWN_RESET_LIMIT = CONFIG.lock_down_reset_limit

    MOVEMENT_ACTIONS = {
        Action.RIGHT_SHIFT,
        Action.LEFT_SHIFT,
        Action.SOFT_DROP,
        Action.HARD_DROP,
        Action.CW_ROTATE,
        Action.CCW_ROTATE,
    }
    RESTRICTED_ACTIONS = {
        Action.FALL,
        Action.LOCK_DOWN,
    }

    def __init__(
        self,
        seed: int | None = None,
    ):
        self.rng = Random(seed)

        self.matrix: Matrix = Matrix(
            matrix_height=(self.MATRIX_HEIGHT + self.BUFFER_HEIGHT), matrix_width=self.MATRIX_WIDTH
        )

        # visible queue of pieces; pieces in the queue are replaced with those from the piece_bag
        self.piece_queue: deque[PieceType] = deque(generate_random_bag(self.rng))
        self.piece_bag: deque[PieceType] = deque(generate_random_bag(self.rng))

        self.held_piece: PieceType | None = None
        self.hold_disabled: bool = False

        self.active_piece: ActivePiece = ActivePiece(self.piece_queue.popleft())
        self.action_queue = deque()

        self.gravity_frame_rate = self.GRAVITY_SPEED * self.FPS
        self.gravity_frame_ticks = 0

        self.lock_down_frame_rate = self.LOCK_DOWN_SPEED * self.FPS
        self.lock_down_reset_limit = self.LOCK_DOWN_RESET_LIMIT
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0
        self.lock_down_reset_count = 0
        # when the piece dips below its lowest row reached, lock down resets
        self.lowest_row = self.active_piece.min_row

        self.ACTION_TO_CONTROL_MAP: dict[Action, Callable[[], ActionResult]] = {
            Action.RIGHT_SHIFT: self.right_shift,
            Action.LEFT_SHIFT: self.left_shift,
            Action.HARD_DROP: self.hard_drop,
            Action.SOFT_DROP: self.soft_drop,
            Action.CW_ROTATE: self.cw_rotate,
            Action.CCW_ROTATE: self.ccw_rotate,
            Action.HOLD: self.hold_piece,
            Action.FALL: self.fall,
            Action.LOCK_DOWN: self.lock_down,
        }

        self.running = True
        self.run_outcome: RunOutcome | None = None
        self.frame_ticks = 0

    def process_frame(self, actions: list[Action]) -> None:
        for action in actions:
            if not isinstance(action, Action) or action in self.RESTRICTED_ACTIONS:
                raise ValueError(f"Provided input {action} is not a valid player action.")

        self.action_queue.clear()
        self.action_queue.extend(actions)

        self.frame_ticks += 1
        if self.lock_down_active:
            self.lock_down_frame_ticks += 1
        self.gravity_frame_ticks += 1

        if self.lock_down_active:
            if (
                self.lock_down_frame_ticks >= self.lock_down_frame_rate
                or self.lock_down_reset_count >= self.lock_down_reset_limit
            ) and self.surface_contact():
                self.action_queue.appendleft(Action.LOCK_DOWN)

        if self.gravity_frame_ticks > 0 and self.gravity_frame_ticks % self.gravity_frame_rate == 0:
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

            if self.active_piece.min_row < self.lowest_row:
                self.lowest_row = self.active_piece.min_row
                self.switch_off_lock_down()

            switched_on = False
            if self.surface_contact() and not self.lock_down_active:
                switched_on = True
                self.switch_on_lock_down()

            if (
                action in self.MOVEMENT_ACTIONS
                and result.success
                and self.lock_down_active
                and not switched_on
            ):
                self.lock_down_frame_ticks = 0
                self.lock_down_reset_count += 1

    # --- State Management ---

    def switch_on_lock_down(self) -> None:
        if not self.lock_down_active:
            self.lock_down_frame_ticks = 0
            self.lock_down_reset_count = 0
        self.lock_down_active = True

    def switch_off_lock_down(self) -> None:
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0
        self.lock_down_reset_count = 0

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
        self.gravity_frame_ticks = 0

        self.active_piece = ActivePiece(self.piece_queue.popleft())
        self.piece_queue.append(self.piece_bag.popleft())
        if not self.piece_bag:
            self.piece_bag = deque(generate_random_bag(self.rng))

        self.lowest_row = self.active_piece.min_row

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
        success = self.active_piece.translate(TranslateDirection.DOWN, self.matrix)
        return ActionResult(success)

    def left_shift(self) -> ActionResult:
        if self.active_piece.right_shifted:
            print("left shifting when right shifted")
        success = self.active_piece.translate(TranslateDirection.LEFT, self.matrix)
        return ActionResult(success)

    def right_shift(self) -> ActionResult:
        if self.active_piece.left_shifted:
            print("right shifting when left shifted")
        success = self.active_piece.translate(TranslateDirection.RIGHT, self.matrix)
        return ActionResult(success)

    def soft_drop(self) -> ActionResult:
        success = self.active_piece.translate(TranslateDirection.DOWN, self.matrix)
        return ActionResult(success)

    def hard_drop(self) -> ActionResult:
        while self.active_piece.translate(TranslateDirection.DOWN, self.matrix):
            pass
        self.action_queue.appendleft(Action.LOCK_DOWN)
        return ActionResult(True)

    def cw_rotate(self) -> ActionResult:
        success = self.active_piece.rotate(Rotation.CW, self.matrix)
        return ActionResult(success)

    def ccw_rotate(self) -> ActionResult:
        success = self.active_piece.rotate(Rotation.CCW, self.matrix)
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

    # --- Utilities ---

    def surface_contact(self) -> bool:
        new_position = self.active_piece.get_translated_position(TranslateDirection.DOWN)
        return self.matrix.check_collision(new_position)

    def build_action_mask(self) -> tuple[bool]:
        mask = [False for _ in range(len(PLAYER_ACTION_SPACE))]

        if self.run_outcome is not None:
            return mask

        for i, action in enumerate(PLAYER_ACTION_SPACE):
            match action:
                case Action.LEFT_SHIFT:
                    if self.active_piece.right_shifted:
                        mask[i] = False
                        continue
                    new_position = self.active_piece.get_translated_position(
                        TranslateDirection.LEFT
                    )
                    mask[i] = not self.matrix.check_collision(new_position)
                case Action.RIGHT_SHIFT:
                    if self.active_piece.left_shifted:
                        mask[i] = False
                        continue
                    new_position = self.active_piece.get_translated_position(
                        TranslateDirection.RIGHT
                    )
                    mask[i] = not self.matrix.check_collision(new_position)
                case Action.SOFT_DROP:
                    new_position = self.active_piece.get_translated_position(
                        TranslateDirection.DOWN
                    )
                    mask[i] = not self.matrix.check_collision(new_position)
                case Action.HARD_DROP:
                    mask[i] = True
                case Action.CW_ROTATE:
                    if (
                        self.active_piece.piece_type == PieceType.O_PIECE
                        or self.active_piece.rotations == 4
                    ):
                        mask[i] = False
                        continue
                    mask[i] = (
                        self.active_piece.get_rotated_position(Rotation.CW, self.matrix) is not None
                    )
                case Action.CCW_ROTATE:
                    if (
                        self.active_piece.piece_type == PieceType.O_PIECE
                        or self.active_piece.rotations == 4
                    ):
                        mask[i] = False
                        continue
                    mask[i] = (
                        self.active_piece.get_rotated_position(Rotation.CCW, self.matrix)
                        is not None
                    )
                case Action.HOLD:
                    mask[i] = not self.hold_disabled

        return mask

    def build_observation(self) -> Observation:
        gravity_frames_remaining = self.gravity_frame_rate - (
            self.frame_ticks % self.gravity_frame_rate
        )
        lock_down_frames_remaining = self.lock_down_frame_rate - self.lock_down_frame_ticks
        lock_down_resets_remaining = self.lock_down_reset_limit - self.lock_down_reset_count

        return Observation(
            matrix=self.matrix.snapshot(),
            active_piece_type=self.active_piece.piece_type,
            active_piece_position=tuple(self.active_piece.position),
            active_piece_orientation=self.active_piece.orientation,
            held_piece=self.held_piece,
            hold_disabled=self.hold_disabled,
            action_mask=self.build_action_mask(),
            piece_queue=tuple(self.piece_queue),
            gravity_frames_remaining=gravity_frames_remaining,
            lock_down_active=self.lock_down_active,
            lock_down_frames_remaining=lock_down_frames_remaining,
            lock_down_resets_remaining=lock_down_resets_remaining,
            lines_cleared=self.matrix.lines_cleared,
            run_outcome=self.run_outcome,
            active_piece_rotations=self.active_piece.rotations,
            active_piece_left_translations=self.active_piece.left_translations,
            active_piece_right_translations=self.active_piece.right_translations,
            active_piece_down_translations=self.active_piece.down_translations,
            active_piece_left_shifted=self.active_piece.left_shifted,
            active_piece_right_shifted=self.active_piece.right_shifted,
        )
