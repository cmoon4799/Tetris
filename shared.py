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
