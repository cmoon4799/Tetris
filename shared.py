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
    QUIT = (auto(), False)

    # -- Engine Actions --
    FALL = (auto(), True)
    LOCK_DOWN = (auto(), True)


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
