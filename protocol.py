from abc import abstractmethod
from enum import Enum, auto
from collections import deque
from typing import Protocol


class Action(Enum):
    RIGHT_SHIFT = auto()
    LEFT_SHIFT = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()
    SAVE_PIECE = auto()
    ROTATE_PIECE = auto()
    GRAVITY = auto()
    QUIT = auto()


class InputManager(Protocol):
    def __init__(self):
        self.input_queue = deque()

    @abstractmethod
    def poll(self) -> Action:
        ...


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
