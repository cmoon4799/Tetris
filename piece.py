from enum import Enum, auto
from random import shuffle
from protocol import Color


class PieceType(Enum):
    I_PIECE = auto()
    O_PIECE = auto()
    T_PIECE = auto()
    J_PIECE = auto()
    L_PIECE = auto()
    S_PIECE = auto()
    Z_PIECE = auto()


PIECE_TO_COLOR_MAP = {
    PieceType.I_PIECE: Color.LIGHT_BLUE,
    PieceType.O_PIECE: Color.YELLOW,
    PieceType.T_PIECE: Color.PURPLE,
    PieceType.J_PIECE: Color.DARK_BLUE,
    PieceType.L_PIECE: Color.ORANGE,
    PieceType.S_PIECE: Color.GREEN,
    PieceType.Z_PIECE: Color.RED,
}


class PieceOrientation(Enum):
    NORTH = auto()
    EAST = auto()
    SOUTH = auto()
    WEST = auto()


class Rotation(Enum):
    CW = auto()
    CCW = auto()


def generate_random_bag() -> list[PieceType]:
    bag = list(PieceType)
    shuffle(bag)
    return bag


def rotate_i_piece(matrix: list[list[int]], orientation: PieceOrientation, rotation: Rotation):
    ...


def rotate_i_piece_visual(matrix: list[list[int]], orientation: PieceOrientation, rotation: Rotation):
    ...
