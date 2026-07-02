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

def get_anchor_point(piece_type: PieceType, orientation: PieceOrientation) -> tuple[int, int]:
    match piece_type:
        case PieceType.I_PIECE:
            ...

def get_i_piece_anchor_point(position: list[tuple[int, int]], orientation: PieceOrientation) -> tuple[int, int]:
    min_i = min(i for i, j in position)
    max_i = max(i for i, j in position)
    min_j = min(j for i, j in position)
    max_j = max(j for i, j in position)
    match orientation:
        case PieceOrientation.NORTH:
            return (min_i + 1, min_j)
        case PieceOrientation.EAST:
            return (max_i, min_j - 2)
        case PieceOrientation.SOUTH:
            return (1, 2)
        case PieceOrientation.WEST:
            return (0, 1)


def rotate_i_piece(matrix: list[list[int]], orientation: PieceOrientation, rotation: Rotation):
    ...


def rotate_i_piece_visual(matrix: list[list[int]], orientation: PieceOrientation, rotation: Rotation):
    if orientation == PieceOrientation.NORTH:
        if rotation == Rotation.CW:
            return [[0, 0, 1, 0],
                    [0, 0, 1, 0],
                    [0, 0, 1, 0],
                    [0, 0, 1, 0]], PieceOrientation.EAST
        else:  # CCW
            return [[0, 0, 1, 0],
                    [0, 0, 1, 0],
                    [0, 0, 1, 0],
                    [0, 0, 1, 0]], PieceOrientation.WEST
    elif orientation == PieceOrientation.EAST:
        if rotation == Rotation.CW:
            return [[1, 1, 1, 1],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0]], PieceOrientation.SOUTH
        else:  # CCW
            return [[1, 1, 1, 1],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0]], PieceOrientation.NORTH
    elif orientation == PieceOrientation.SOUTH:
        if rotation == Rotation.CW:
            return [[1], 
                    [1], 
                    [1], 
                    [1]], PieceOrientation.WEST
        else: # CCW
            return [[1], 
                    [1], 
                    [1], 
                    [1]], PieceOrientation.EAST
    elif orientation == PieceOrientation.WEST:
        if rotation == Rotation.CW:
            return [[1], 
                    [1], 
                    [1], 
                    [1]], PieceOrientation.NORTH
        else: # CCW
            return [[1], 
                    [1], 
                    [1], 
                    [1]], PieceOrientation.SOUTH
