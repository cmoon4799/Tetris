from enum import Enum, auto
from random import shuffle

from matrix import Matrix
from shared import Color


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


class ActivePiece:
    def __init__(self, piece_type: PieceType):
        self.piece_type: PieceType = piece_type
        self.orientation: PieceOrientation = PieceOrientation.NORTH
        self.position: list[tuple[int, int]] = []
        self.color: Color = PIECE_TO_COLOR_MAP[self.piece_type]

        self.load_starting_position()
        self.lowest_row = self.min_row

    def load_starting_position(self):
        match self.piece_type:
            case PieceType.I_PIECE:
                self.position = [(20, 3), (20, 4), (20, 5), (20, 6)]
            case PieceType.O_PIECE:
                self.position = [(20, 4), (20, 5), (21, 4), (21, 5)]
            case PieceType.T_PIECE:
                self.position = [(20, 3), (20, 4), (20, 5), (21, 4)]
            case PieceType.L_PIECE:
                self.position = [(20, 3), (20, 4), (20, 5), (21, 5)]
            case PieceType.J_PIECE:
                self.position = [(20, 3), (20, 4), (20, 5), (21, 5)]
            case PieceType.S_PIECE:
                self.position = [(20, 3), (20, 4), (21, 4), (21, 5)]
            case PieceType.Z_PIECE:
                self.position = [(21, 3), (21, 4), (20, 4), (20, 5)]

    @property
    def anchor(self):
        """Each piece, according to its orientation, lies in a fixed position within a square that frames it.
        Anchor returns the top-left corner of the framing square.
        """

        match self.piece_type:
            case PieceType.I_PIECE:
                return self._get_i_piece_anchor_point()
            case PieceType.O_PIECE:
                return self._get_o_piece_anchor_point()
            case _:
                return self._get_three_by_two_piece_anchor_point()

    @property
    def min_row(self):
        return min(i for (i, j) in self.position)

    @property
    def max_row(self):
        return max(i for (i, j) in self.position)

    @property
    def min_col(self):
        return min(j for (i, j) in self.position)

    @property
    def max_col(self):
        return max(j for (i, j) in self.position)

    def _get_i_piece_anchor_point(self) -> tuple[int, int]:
        match self.orientation:
            case PieceOrientation.NORTH:
                return (self.max_row + 1, self.min_col)
            case PieceOrientation.EAST:
                return (self.max_row, self.min_col - 2)
            case PieceOrientation.SOUTH:
                return (self.max_row + 2, self.min_col)
            case PieceOrientation.WEST:
                return (self.max_row, self.min_col - 1)

    def _get_o_piece_anchor_point(self) -> tuple[int, int]:
        return (self.max_row, self.min_col - 1)

    def _get_three_by_two_piece_anchor_point(self) -> tuple[int, int]:
        match self.orientation:
            case PieceOrientation.NORTH:
                return (self.max_row, self.min_col)
            case PieceOrientation.EAST:
                return (self.max_row, self.min_col - 1)
            case PieceOrientation.SOUTH:
                return (self.max_row + 1, self.min_col)
            case PieceOrientation.WEST:
                return (self.max_row, self.min_col)


def rotate_orientation(orientation: PieceOrientation, rotation: Rotation) -> PieceOrientation:
    if rotation == Rotation.CW:
        return list(PieceOrientation)[orientation.value % 4]
    else:
        return list(PieceOrientation)[(orientation.value - 2) % 4]


def rotate_i_piece(matrix: Matrix, piece: ActivePiece, rotation: Rotation):
    new_positions = [
        rotate_i_piece_visual(piece, rotation),
        rotate_i_piece_right_wall_kick(piece, rotation),
        rotate_i_piece_left_wall_kick(piece, rotation),
        rotate_i_piece_floor_kick(piece, rotation),
        rotate_i_piece_right_well_kick(piece, rotation),
        rotate_i_piece_left_well_kick(piece, rotation),
    ]

    new_orientation = rotate_orientation(piece.orientation, rotation)
    for position in new_positions:
        if not matrix.check_collision(position):
            piece.orientation = new_orientation
            piece.position = position
            return


def rotate_i_piece_visual(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    anchor_row, anchor_col = piece.anchor
    rotated_orientation = rotate_orientation(piece.orientation, rotation)

    match rotated_orientation:
        case PieceOrientation.NORTH:
            new_position = [(anchor_row - 1, anchor_col + i) for i in range(4)]
        case PieceOrientation.EAST:
            new_position = [(anchor_row - i, anchor_col + 2) for i in range(4)]
        case PieceOrientation.SOUTH:
            new_position = [(anchor_row - 2, anchor_col + i) for i in range(4)]
        case PieceOrientation.WEST:
            new_position = [(anchor_row - i, anchor_col + 1) for i in range(4)]

    return new_position


def rotate_i_piece_right_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -2)
            case PieceOrientation.EAST:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)
            case PieceOrientation.WEST:
                kick_i, kick_j = (0, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
            case PieceOrientation.EAST:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -2)
            case PieceOrientation.WEST:
                kick_i, kick_j = (0, 0)

    new_position = rotate_i_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_i_piece_left_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)
            case PieceOrientation.EAST:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 2)
            case PieceOrientation.WEST:
                kick_i, kick_j = (0, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 2)
            case PieceOrientation.EAST:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
            case PieceOrientation.WEST:
                kick_i, kick_j = (0, 0)

    new_position = rotate_i_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_i_piece_floor_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.EAST:
                kick_i, kick_j = (2, 1)
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 2)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -2)
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.WEST:
                kick_i, kick_j = (2, -1)

    new_position = rotate_i_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_i_piece_right_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (1, -2)
            case PieceOrientation.EAST:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (2, -1)
            case PieceOrientation.WEST:
                kick_i, kick_j = (0, 0)

    new_position = rotate_i_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_i_piece_left_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CCW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (1, 2)
            case PieceOrientation.EAST:
                kick_i, kick_j = (0, 0)
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (2, 1)
            case PieceOrientation.WEST:
                kick_i, kick_j = (0, 0)

    new_position = rotate_i_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece(matrix: Matrix, piece: ActivePiece, rotation: Rotation):
    new_positions = [
        rotate_t_piece_visual(piece, rotation),
        rotate_t_piece_right_wall_kick(piece, rotation),
        rotate_t_piece_left_wall_kick(piece, rotation),
        rotate_t_piece_floor_kick(piece, rotation),
        rotate_t_piece_right_well_kick(piece, rotation),
        rotate_t_piece_left_well_kick(piece, rotation),
    ]

    new_orientation = rotate_orientation(piece.orientation, rotation)
    for position in new_positions:
        if not matrix.check_collision(position):
            piece.orientation = new_orientation
            piece.position = position
            return


def rotate_t_piece_visual(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    anchor_row, anchor_col = piece.anchor
    rotated_orientation = rotate_orientation(piece.orientation, rotation)

    match rotated_orientation:
        case PieceOrientation.NORTH:
            new_position = [
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
            ]
        case PieceOrientation.EAST:
            new_position = [
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row - 2, anchor_col + 1),
            ]
        case PieceOrientation.SOUTH:
            new_position = [
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row - 2, anchor_col + 1),
            ]
        case PieceOrientation.WEST:
            new_position = [
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 2, anchor_col + 1),
            ]

    return new_position


def rotate_t_piece_right_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_t_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece_left_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_t_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece_floor_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_t_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece_right_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_t_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece_left_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_t_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece(matrix: Matrix, piece: ActivePiece, rotation: Rotation):
    new_positions = [
        rotate_l_piece_visual(piece, rotation),
        rotate_l_piece_right_wall_kick(piece, rotation),
        rotate_l_piece_left_wall_kick(piece, rotation),
        rotate_l_piece_floor_kick(piece, rotation),
        rotate_l_piece_right_well_kick(piece, rotation),
        rotate_l_piece_left_well_kick(piece, rotation),
    ]

    new_orientation = rotate_orientation(piece.orientation, rotation)
    for position in new_positions:
        if not matrix.check_collision(position):
            print(piece.orientation.name, new_orientation.name)
            piece.orientation = new_orientation
            piece.position = position
            return


def rotate_l_piece_visual(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    anchor_row, anchor_col = piece.anchor
    rotated_orientation = rotate_orientation(piece.orientation, rotation)

    match rotated_orientation:
        case PieceOrientation.NORTH:
            new_position = [
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row, anchor_col + 2),
            ]
        case PieceOrientation.EAST:
            new_position = [
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 2, anchor_col + 1),
                (anchor_row - 2, anchor_col + 2),
            ]
        case PieceOrientation.SOUTH:
            new_position = [
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row - 2, anchor_col),
            ]
        case PieceOrientation.WEST:
            new_position = [
                (anchor_row, anchor_col),
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 2, anchor_col + 1),
            ]

    return new_position


def rotate_l_piece_right_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_l_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece_left_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_l_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece_floor_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_l_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece_right_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_l_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece_left_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_l_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece(matrix: Matrix, piece: ActivePiece, rotation: Rotation):
    new_positions = [
        rotate_j_piece_visual(piece, rotation),
        rotate_j_piece_right_wall_kick(piece, rotation),
        rotate_j_piece_left_wall_kick(piece, rotation),
        rotate_j_piece_floor_kick(piece, rotation),
        rotate_j_piece_left_well_kick(piece, rotation),
        rotate_j_piece_right_well_kick(piece, rotation),
    ]

    new_orientation = rotate_orientation(piece.orientation, rotation)
    for position in new_positions:
        if not matrix.check_collision(position):
            piece.orientation = new_orientation
            piece.position = position
            return


def rotate_j_piece_visual(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    anchor_row, anchor_col = piece.anchor
    rotated_orientation = rotate_orientation(piece.orientation, rotation)

    match rotated_orientation:
        case PieceOrientation.NORTH:
            new_position = [
                (anchor_row, anchor_col),
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
            ]
        case PieceOrientation.EAST:
            new_position = [
                (anchor_row, anchor_col + 2),
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 2, anchor_col + 1),
            ]
        case PieceOrientation.SOUTH:
            new_position = [
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row - 2, anchor_col + 2),
            ]
        case PieceOrientation.WEST:
            new_position = [
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 2, anchor_col),
                (anchor_row - 2, anchor_col + 1),
            ]

    return new_position


def rotate_j_piece_right_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_j_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece_left_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_j_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece_floor_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_j_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece_right_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_j_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece_left_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_j_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece(matrix: Matrix, piece: ActivePiece, rotation: Rotation):
    new_positions = [
        rotate_s_piece_visual(piece, rotation),
        rotate_s_piece_right_wall_kick(piece, rotation),
        rotate_s_piece_left_wall_kick(piece, rotation),
        rotate_s_piece_floor_kick(piece, rotation),
        rotate_s_piece_left_well_kick(piece, rotation),
        rotate_s_piece_right_well_kick(piece, rotation),
    ]

    new_orientation = rotate_orientation(piece.orientation, rotation)
    for position in new_positions:
        if not matrix.check_collision(position):
            piece.orientation = new_orientation
            piece.position = position
            return


def rotate_s_piece_visual(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    anchor_row, anchor_col = piece.anchor
    rotated_orientation = rotate_orientation(piece.orientation, rotation)

    match rotated_orientation:
        case PieceOrientation.NORTH:
            new_position = [
                (anchor_row, anchor_col + 1),
                (anchor_row, anchor_col + 2),
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
            ]
        case PieceOrientation.EAST:
            new_position = [
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row - 2, anchor_col + 2),
            ]
        case PieceOrientation.SOUTH:
            new_position = [
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row - 2, anchor_col),
                (anchor_row - 2, anchor_col + 1),
            ]
        case PieceOrientation.WEST:
            new_position = [
                (anchor_row, anchor_col),
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 2, anchor_col + 1),
            ]

    return new_position


def rotate_s_piece_right_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_s_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece_left_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_s_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece_floor_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_s_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece_right_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_s_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece_left_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_s_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece(matrix: Matrix, piece: ActivePiece, rotation: Rotation):
    new_positions = [
        rotate_z_piece_visual(piece, rotation),
        rotate_z_piece_right_wall_kick(piece, rotation),
        rotate_z_piece_left_wall_kick(piece, rotation),
        rotate_z_piece_floor_kick(piece, rotation),
        rotate_z_piece_left_well_kick(piece, rotation),
        rotate_z_piece_right_well_kick(piece, rotation),
    ]

    new_orientation = rotate_orientation(piece.orientation, rotation)
    for position in new_positions:
        if not matrix.check_collision(position):
            piece.orientation = new_orientation
            piece.position = position
            return


def rotate_z_piece_visual(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    anchor_row, anchor_col = piece.anchor
    rotated_orientation = rotate_orientation(piece.orientation, rotation)

    match rotated_orientation:
        case PieceOrientation.NORTH:
            new_position = [
                (anchor_row, anchor_col),
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
            ]
        case PieceOrientation.EAST:
            new_position = [
                (anchor_row, anchor_col + 2),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row - 2, anchor_col + 1),
            ]
        case PieceOrientation.SOUTH:
            new_position = [
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 2, anchor_col + 1),
                (anchor_row - 2, anchor_col + 2),
            ]
        case PieceOrientation.WEST:
            new_position = [
                (anchor_row, anchor_col + 1),
                (anchor_row - 1, anchor_col),
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 2, anchor_col),
            ]

    return new_position


def rotate_z_piece_right_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_z_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece_left_wall_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_z_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece_floor_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_z_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece_right_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_z_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece_left_well_kick(piece: ActivePiece, rotation: Rotation) -> list[tuple[int, int]]:
    new_orientation = rotate_orientation(piece.orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_z_piece_visual(piece, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]
