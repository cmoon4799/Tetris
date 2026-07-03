from enum import Enum, auto


class Action(Enum):
    RIGHT_SHIFT = auto()
    LEFT_SHIFT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    SAVE = auto()
    CW_ROTATE = auto()
    CCW_ROTATE = auto()
    GRAVITY = auto()
    QUIT = auto()


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
