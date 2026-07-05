from dataclasses import dataclass
from enum import Enum, auto


class Action(Enum):
    restricted: bool

    def __init__(self, _: int, restricted: bool):
        self.restricted = restricted

    # -- Player Input Actions --
    CW_ROTATE = (auto(), False)
    CCW_ROTATE = (auto(), False)
    RIGHT_SHIFT = (auto(), False)
    LEFT_SHIFT = (auto(), False)
    SOFT_DROP = (auto(), False)
    HARD_DROP = (auto(), False)
    HOLD = (auto(), False)

    # -- Engine Actions --
    FALL = (auto(), True)
    LOCK_DOWN = (auto(), True)


PLAYER_ACTION_SPACE = [
    Action.CW_ROTATE,
    Action.CCW_ROTATE,
    Action.RIGHT_SHIFT,
    Action.LEFT_SHIFT,
    Action.SOFT_DROP,
    Action.HARD_DROP,
    Action.HOLD,
]


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
    piece_count=7,
    visible_queue_size=6,
    line_clear_goal=40,
)


@dataclass(frozen=True)
class Observation:
    matrix: tuple[tuple[Color | None]]
    active_piece_type: PieceType
    active_piece_position: tuple[tuple[int, int]]
    active_piece_orientation: PieceOrientation
    held_piece: PieceType | None
    hold_disabled: bool
    piece_queue: tuple[PieceType]
    gravity_frames_remaining: int
    lock_down_active: bool
    lock_down_frames_remaining: int
    lock_down_resets_remaining: int


@dataclass(frozen=True)
class FrameResult:
    observation: Observation
    lines_cleared: int
    terminated: bool
