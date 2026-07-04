from abc import abstractmethod
from typing import Protocol

import pygame

from shared import Action


class InputManager(Protocol):
    @abstractmethod
    def poll(self) -> list[Action]: ...


class PygameInputManager(InputManager):
    KEY_TO_ACTION_MAP = {
        pygame.K_RIGHT: Action.RIGHT_SHIFT,
        pygame.K_LEFT: Action.LEFT_SHIFT,
        pygame.K_UP: Action.CW_ROTATE,
        pygame.K_DOWN: Action.SOFT_DROP,
        pygame.K_LCTRL: Action.CCW_ROTATE,
        pygame.K_SPACE: Action.HARD_DROP,
        pygame.K_LSHIFT: Action.HOLD,
    }

    def poll(self) -> list[Action]:
        actions = []

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key in self.KEY_TO_ACTION_MAP:
                    actions.append(self.KEY_TO_ACTION_MAP[event.key])
            if event.type == pygame.QUIT:
                actions.append(Action.QUIT)

        return actions
