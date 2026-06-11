from enum import Enum

"""
Design Thoughts
- Action requesters and resolvers should be placed within the Game class as it requires access to Game 
internals and follow internal Game rules.

Notes
    Tetromino
    - Active or Inactive
    - Coordinates
    - Piece Enum

    Control Interface
    - Soft Drop
    - Left Shift
    - Right Shift
    - Hard Drop
    - Save Piece
    - Rotate Piece

    Keyboard Control
    - Key Press
    - Key Hold
        - Only relevant for Soft Drop or Left/Right Shift; after a delay, ...

    Action Queue
    - Calls to exposed controls adds actions to the queue.
    - After every fixed time interval, add a gravity action to the queue.
    - On active piece becoming in active, add a hook to the queue.
        - Check if there are lines to clear, and if so, clear lines.
        - Set the next piece in line to be the new active piece.
"""


class ActivePiece:
    def __init__(self):
        ...


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

    # -- exposed controls --
    def hard_drop(self):
        ...

    def soft_drop(self):
        ...

    def left_shift(self):
        ...

    def right_shift(self):
        ...

    def save_piece(self):
        """Once a piece is saved, the new active piece cannot be switched out.
        """
        ...

    def rotate_piece(self):
        ...

    # -- action resolvers --
    def resolve_hard_drop(self):
        ...
