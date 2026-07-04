from abc import abstractmethod
from typing import Protocol

from shared import Action


class InputManager(Protocol):
    @abstractmethod
    def poll(self) -> list[Action]: ...
