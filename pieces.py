from enum import Enum, auto
from random import shuffle


class PieceType(Enum):
    I_PIECE = auto()
    O_PIECE = auto()
    T_PIECE = auto()
    J_PIECE = auto()
    L_PIECE = auto()
    S_PIECE = auto()
    Z_PIECE = auto()


def generate_random_bag() -> list[PieceType]:
    return shuffle(list(PieceType))
