from dataclasses import dataclass
from enum import Enum, auto


class Action(Enum):
    # -- Player Input Actions --
    LEFT_SHIFT = 0
    RIGHT_SHIFT = 1
    SOFT_DROP = 2
    HARD_DROP = 3
    CW_ROTATE = 4
    CCW_ROTATE = 5
    HOLD = 6

    # -- Engine Actions --
    FALL = 99
    LOCK_DOWN = 100


PLAYER_ACTION_SPACE = (
    Action.LEFT_SHIFT,
    Action.RIGHT_SHIFT,
    Action.SOFT_DROP,
    Action.HARD_DROP,
    Action.CW_ROTATE,
    Action.CCW_ROTATE,
    Action.HOLD,
)


class Color(Enum):
    YELLOW = auto()
    PURPLE = auto()
    ORANGE = auto()
    LIGHT_BLUE = auto()
    DARK_BLUE = auto()
    GREEN = auto()
    RED = auto()
    CYAN = auto()
    BLACK = auto()
    PINK = auto()


class RunOutcome(Enum):
    VICTORY = auto()
    DEFEAT = auto()


class PieceType(Enum):
    I_PIECE = auto()
    O_PIECE = auto()
    T_PIECE = auto()
    J_PIECE = auto()
    L_PIECE = auto()
    S_PIECE = auto()
    Z_PIECE = auto()


class PieceOrientation(Enum):
    NORTH = auto()
    EAST = auto()
    SOUTH = auto()
    WEST = auto()


@dataclass(frozen=True)
class GameConfig:
    fps: int  # frames per second
    gravity_speed: float  # time in seconds it takes for the active piece to fall by one line
    lock_down_speed: float  # time in seconds it takes for the active piece to lock on its surface
    lock_down_reset_limit: int  # number of resets allowed before immediate lock
    matrix_height: int  # active game area height; does not account for the invisible buffer above
    matrix_width: int  # active game area width
    buffer_height: int  # buffer above the matrix skyline
    piece_count: int  # the total number of pieces; theoretically, we can have more than 7
    visible_queue_size: int  # the number of visible pieces in the queue
    line_clear_goal: int  # victory condition


# module level instance; modules are singletons, so there is only a single
# canonical dataclass representing the game settings and constants
CONFIG = GameConfig(
    fps=60,
    gravity_speed=0.8,
    lock_down_speed=0.5,
    lock_down_reset_limit=15,
    matrix_height=20,
    matrix_width=10,
    buffer_height=10,
    piece_count=7,
    visible_queue_size=6,
    line_clear_goal=40,
)


@dataclass(frozen=True)
class Observation:
    """
    Attributes:
        action_mask: boolean mask of valid actions at the given moment
        lines_cleared: lines cleared thus far
        run_outcome: indicates Victory or Defeat or still running if None
    """

    matrix: tuple[tuple[Color | None]]
    active_piece_type: PieceType
    active_piece_position: tuple[tuple[int, int]]
    active_piece_orientation: PieceOrientation
    held_piece: PieceType | None
    hold_disabled: bool
    action_mask: tuple[bool]
    piece_queue: tuple[PieceType]
    gravity_frames_remaining: int
    lock_down_active: bool
    lock_down_frames_remaining: int
    lock_down_resets_remaining: int
    lines_cleared: int
    run_outcome: RunOutcome | None
    active_piece_rotations: int
    active_piece_left_translations: int
    active_piece_right_translations: int
    active_piece_down_translations: int
    active_piece_left_shifted: bool
    active_piece_right_shifted: bool


class TranslateDirection(Enum):
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class Rotation(Enum):
    CW = auto()
    CCW = auto()
