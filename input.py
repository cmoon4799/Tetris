from shared import Action


from abc import abstractmethod
from collections import deque
from typing import Protocol


class InputManager(Protocol):
    def __init__(self):
        self.input_queue = deque()

    @abstractmethod
    def poll(self) -> Action:
        ...
