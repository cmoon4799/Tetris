from abc import abstractmethod
from collections import deque
from typing import Protocol

from shared import Action


class InputManager(Protocol):
    def __init__(self):
        self.input_queue = deque()

    @abstractmethod
    def poll(self) -> list[Action]: ...
