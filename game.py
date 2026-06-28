"""
Entrypoint and core gameplay orchestration.
"""

from enum import Enum
from pieces import PieceType


class ActivePiece:
    def __init__(self, piece_type: PieceType):
        self.piece_type = piece_type
        self.rotation: int = 0


class Action(Enum):
    ...


class Game:
    """
    Action requesters and resolvers should be placed within the Game class as it requires access to Game
    internals and follow internal Game rules.
    """

    def __init__(self):
        self.active_piece: ActivePiece = None
        self.action_queue: list[Action] = []

    def initialize(self): ...

    # -- exposed controls --
    def hard_drop(self): ...

    def soft_drop(self): ...

    def left_shift(self): ...

    def right_shift(self): ...

    def save_piece(self): ...

    def rotate_piece(self): ...

    # -- action resolvers --
    def resolve_hard_drop(self): ...

    def resolve_soft_drop(self): ...

    def resolve_left_shift(self): ...

    def resolve_right_shift(self): ...

    def resolve_save_piece(self): ...

    def resolve_rotate_piece(self): ...
