from enum import Enum, auto


class Action(Enum):
    CW_ROTATE = auto()
    CCW_ROTATE = auto()
    RIGHT_SHIFT = auto()
    LEFT_SHIFT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    HOLD = auto()
    GRAVITY = auto()
    QUIT = auto()
    FALL = auto()


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
