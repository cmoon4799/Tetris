from collections.abc import Callable
from enum import Enum, auto
from random import Random

from matrix import Matrix
from shared import CONFIG, Color, PieceOrientation, PieceType, TranslateDirection

PIECE_TO_COLOR_MAP = {
    PieceType.I_PIECE: Color.LIGHT_BLUE,
    PieceType.O_PIECE: Color.YELLOW,
    PieceType.T_PIECE: Color.PURPLE,
    PieceType.J_PIECE: Color.DARK_BLUE,
    PieceType.L_PIECE: Color.ORANGE,
    PieceType.S_PIECE: Color.GREEN,
    PieceType.Z_PIECE: Color.RED,
}


class Rotation(Enum):
    CW = auto()
    CCW = auto()


def generate_random_bag(rng: Random) -> list[PieceType]:
    bag = list(PieceType)
    rng.shuffle(bag)
    return bag


class ActivePiece:
    def __init__(self, piece_type: PieceType):
        self.piece_type: PieceType = piece_type
        self.orientation: PieceOrientation = PieceOrientation.NORTH
        self.position: tuple[tuple[int, int], ...] = ()
        self.color: Color = PIECE_TO_COLOR_MAP[self.piece_type]

        self.load_starting_position()
        self.lowest_row = self.min_row

        self.rotations = 0
        self.left_translations = 0
        self.right_translations = 0
        self.down_translations = 0

        # these flags are used to penalize useless stuttering, i.e. back and
        # forth movement that causes the piece to stay in place;  it is reset
        # on every translation
        self.left_shifted: bool = False
        self.right_shifted: bool = False

    def load_starting_position(self):
        spawn_row = CONFIG.matrix_height
        left_spawn_col = CONFIG.matrix_width // 2 - 2

        match self.piece_type:
            case PieceType.I_PIECE:
                self.position = tuple((spawn_row, left_spawn_col + offset) for offset in range(4))
            case PieceType.O_PIECE:
                self.position = (
                    (spawn_row, left_spawn_col + 1),
                    (spawn_row, left_spawn_col + 2),
                    (spawn_row + 1, left_spawn_col + 1),
                    (spawn_row + 1, left_spawn_col + 2),
                )
            case PieceType.T_PIECE:
                self.position = (
                    (spawn_row, left_spawn_col),
                    (spawn_row, left_spawn_col + 1),
                    (spawn_row, left_spawn_col + 2),
                    (spawn_row + 1, left_spawn_col + 1),
                )
            case PieceType.L_PIECE:
                self.position = (
                    (spawn_row, left_spawn_col),
                    (spawn_row, left_spawn_col + 1),
                    (spawn_row, left_spawn_col + 2),
                    (spawn_row + 1, left_spawn_col + 2),
                )
            case PieceType.J_PIECE:
                self.position = (
                    (spawn_row, left_spawn_col),
                    (spawn_row, left_spawn_col + 1),
                    (spawn_row, left_spawn_col + 2),
                    (spawn_row + 1, left_spawn_col),
                )
            case PieceType.S_PIECE:
                self.position = (
                    (spawn_row, left_spawn_col),
                    (spawn_row, left_spawn_col + 1),
                    (spawn_row + 1, left_spawn_col + 1),
                    (spawn_row + 1, left_spawn_col + 2),
                )
            case PieceType.Z_PIECE:
                self.position = (
                    (spawn_row + 1, left_spawn_col),
                    (spawn_row + 1, left_spawn_col + 1),
                    (spawn_row, left_spawn_col + 1),
                    (spawn_row, left_spawn_col + 2),
                )

    def get_translated_position(self, direction: TranslateDirection) -> tuple[tuple[int, int], ...]:
        """Return the would be position in the matrix without translating the piece."""

        match direction:
            case TranslateDirection.DOWN:
                return tuple((i - 1, j) for (i, j) in self.position)
            case TranslateDirection.LEFT:
                return tuple((i, j - 1) for (i, j) in self.position)
            case TranslateDirection.RIGHT:
                return tuple((i, j + 1) for (i, j) in self.position)

    def get_rotated_position(
        self, rotation: Rotation, matrix: Matrix
    ) -> tuple[tuple[int, int], ...] | None:
        """Return the would be position in the matrix without rotating the piece; if rotation is not
        possible, return None.
        """

        match self.piece_type:
            case PieceType.I_PIECE:
                return rotate_i_piece(
                    matrix,
                    self.position,
                    self.orientation,
                    rotation,
                )
            case PieceType.T_PIECE:
                return rotate_t_piece(
                    matrix,
                    self.position,
                    self.orientation,
                    rotation,
                )
            case PieceType.L_PIECE:
                return rotate_l_piece(
                    matrix,
                    self.position,
                    self.orientation,
                    rotation,
                )
            case PieceType.J_PIECE:
                return rotate_j_piece(
                    matrix,
                    self.position,
                    self.orientation,
                    rotation,
                )
            case PieceType.S_PIECE:
                return rotate_s_piece(
                    matrix,
                    self.position,
                    self.orientation,
                    rotation,
                )
            case PieceType.Z_PIECE:
                return rotate_z_piece(
                    matrix,
                    self.position,
                    self.orientation,
                    rotation,
                )
            case PieceType.O_PIECE:
                return None

    def rotate(self, rotation: Rotation, matrix: Matrix) -> bool:
        """Rotate the active piece and return a boolean indicating rotation success."""

        self.left_shifted = False
        self.right_shifted = False

        rotated_position = self.get_rotated_position(rotation, matrix)
        if rotated_position is not None:
            self.position = rotated_position
            self.orientation = rotate_orientation(self.orientation, rotation)
            self.rotations += 1
            return True
        return False

    def translate(self, direction: TranslateDirection, matrix: Matrix) -> bool:
        """Translate the active piece and return a boolean indicating rotation success."""

        self.left_shifted = False
        self.right_shifted = False

        translated_position = self.get_translated_position(direction)
        if not matrix.check_collision(translated_position):
            self.position = translated_position
            match direction:
                case TranslateDirection.LEFT:
                    self.left_shifted = True
                    self.left_translations += 1
                case TranslateDirection.RIGHT:
                    self.right_shifted = True
                    self.right_translations += 1
                case TranslateDirection.DOWN:
                    self.down_translations += 1
            return True
        return False

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


def get_anchor(
    piece_type: PieceType,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
) -> tuple[int, int]:
    """Each piece, according to its orientation, lies in a fixed position within a framing
    square. Returns the top-left corner of the framing square.
    """

    max_row = max(i for (i, j) in position)
    min_col = min(j for (i, j) in position)

    match piece_type:
        case PieceType.I_PIECE:
            match orientation:
                case PieceOrientation.NORTH:
                    return (max_row + 1, min_col)
                case PieceOrientation.EAST:
                    return (max_row, min_col - 2)
                case PieceOrientation.SOUTH:
                    return (max_row + 2, min_col)
                case PieceOrientation.WEST:
                    return (max_row, min_col - 1)
        case PieceType.O_PIECE:
            return (max_row, min_col - 1)
        case _:  # 3 x 2 pieces
            match orientation:
                case PieceOrientation.NORTH:
                    return (max_row, min_col)
                case PieceOrientation.EAST:
                    return (max_row, min_col - 1)
                case PieceOrientation.SOUTH:
                    return (max_row + 1, min_col)
                case PieceOrientation.WEST:
                    return (max_row, min_col)


def generate_anchor_relative_position(
    piece_type: PieceType, orientation: PieceOrientation, anchor: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    """Generate cell positions of a piece relative to an anchor point according to the piece type
    and orientation. Each cell is represented as (x, y), meaning its position in the matrix is
    (anchor_x + x, anchor_y + y).
    """

    anchor_row, anchor_col = anchor
    match piece_type:
        case PieceType.I_PIECE:
            match orientation:
                case PieceOrientation.NORTH:
                    return tuple((anchor_row - 1, anchor_col + i) for i in range(4))
                case PieceOrientation.EAST:
                    return tuple((anchor_row - i, anchor_col + 2) for i in range(4))
                case PieceOrientation.SOUTH:
                    return tuple((anchor_row - 2, anchor_col + i) for i in range(4))
                case PieceOrientation.WEST:
                    return tuple((anchor_row - i, anchor_col + 1) for i in range(4))
        case PieceType.T_PIECE:
            match orientation:
                case PieceOrientation.NORTH:
                    return (
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                    )
                case PieceOrientation.EAST:
                    return (
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                        (anchor_row - 2, anchor_col + 1),
                    )
                case PieceOrientation.SOUTH:
                    return (
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                        (anchor_row - 2, anchor_col + 1),
                    )
                case PieceOrientation.WEST:
                    return (
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 2, anchor_col + 1),
                    )
        case PieceType.L_PIECE:
            match orientation:
                case PieceOrientation.NORTH:
                    return [
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                        (anchor_row, anchor_col + 2),
                    ]
                case PieceOrientation.EAST:
                    return [
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 2, anchor_col + 1),
                        (anchor_row - 2, anchor_col + 2),
                    ]
                case PieceOrientation.SOUTH:
                    return [
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                        (anchor_row - 2, anchor_col),
                    ]
                case PieceOrientation.WEST:
                    return [
                        (anchor_row, anchor_col),
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 2, anchor_col + 1),
                    ]
        case PieceType.J_PIECE:
            match orientation:
                case PieceOrientation.NORTH:
                    return [
                        (anchor_row, anchor_col),
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                    ]
                case PieceOrientation.EAST:
                    return [
                        (anchor_row, anchor_col + 2),
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 2, anchor_col + 1),
                    ]
                case PieceOrientation.SOUTH:
                    return [
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                        (anchor_row - 2, anchor_col + 2),
                    ]
                case PieceOrientation.WEST:
                    return [
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 2, anchor_col),
                        (anchor_row - 2, anchor_col + 1),
                    ]
        case PieceType.S_PIECE:
            match orientation:
                case PieceOrientation.NORTH:
                    return [
                        (anchor_row, anchor_col + 1),
                        (anchor_row, anchor_col + 2),
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                    ]
                case PieceOrientation.EAST:
                    return [
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                        (anchor_row - 2, anchor_col + 2),
                    ]
                case PieceOrientation.SOUTH:
                    return [
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                        (anchor_row - 2, anchor_col),
                        (anchor_row - 2, anchor_col + 1),
                    ]
                case PieceOrientation.WEST:
                    return [
                        (anchor_row, anchor_col),
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 2, anchor_col + 1),
                    ]
        case PieceType.Z_PIECE:
            match orientation:
                case PieceOrientation.NORTH:
                    return [
                        (anchor_row, anchor_col),
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                    ]
                case PieceOrientation.EAST:
                    return [
                        (anchor_row, anchor_col + 2),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 1, anchor_col + 2),
                        (anchor_row - 2, anchor_col + 1),
                    ]
                case PieceOrientation.SOUTH:
                    return [
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 2, anchor_col + 1),
                        (anchor_row - 2, anchor_col + 2),
                    ]
                case PieceOrientation.WEST:
                    return [
                        (anchor_row, anchor_col + 1),
                        (anchor_row - 1, anchor_col),
                        (anchor_row - 1, anchor_col + 1),
                        (anchor_row - 2, anchor_col),
                    ]
        case PieceType.O_PIECE:
            return [
                (anchor_row - 1, anchor_col + 1),
                (anchor_row - 1, anchor_col + 2),
                (anchor_row, anchor_col + 1),
                (anchor_row, anchor_col + 2),
            ]


def rotate_orientation(orientation: PieceOrientation, rotation: Rotation) -> PieceOrientation:
    if rotation == Rotation.CW:
        return list(PieceOrientation)[orientation.value % 4]
    else:
        return list(PieceOrientation)[(orientation.value - 2) % 4]


def _get_first_valid_rotation_position(
    matrix: Matrix,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
    candidate_generators: tuple[
        Callable[
            [tuple[tuple[int, int], ...], PieceOrientation, Rotation],
            tuple[tuple[int, int], ...],
        ],
        ...,
    ],
) -> tuple[tuple[int, int], ...] | None:
    for candidate_generator in candidate_generators:
        candidate_position = candidate_generator(position, orientation, rotation)
        if not matrix.check_collision(candidate_position):
            return candidate_position

    return None


def rotate_i_piece(
    matrix: Matrix,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...] | None:
    return _get_first_valid_rotation_position(
        matrix,
        position,
        orientation,
        rotation,
        (
            rotate_i_piece_visual,
            rotate_i_piece_right_wall_kick,
            rotate_i_piece_left_wall_kick,
            rotate_i_piece_floor_kick,
            rotate_i_piece_right_well_kick,
            rotate_i_piece_left_well_kick,
        ),
    )


def rotate_i_piece_visual(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    anchor_row, anchor_col = get_anchor(PieceType.I_PIECE, position, orientation)
    rotated_orientation = rotate_orientation(orientation, rotation)

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


def rotate_i_piece_right_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
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

    new_position = rotate_i_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_i_piece_left_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
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

    new_position = rotate_i_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_i_piece_floor_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
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

    new_position = rotate_i_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_i_piece_right_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
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

    new_position = rotate_i_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_i_piece_left_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
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

    new_position = rotate_i_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece(
    matrix: Matrix,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...] | None:
    return _get_first_valid_rotation_position(
        matrix,
        position,
        orientation,
        rotation,
        (
            rotate_t_piece_visual,
            rotate_t_piece_right_wall_kick,
            rotate_t_piece_left_wall_kick,
            rotate_t_piece_floor_kick,
            rotate_t_piece_right_well_kick,
            rotate_t_piece_left_well_kick,
        ),
    )


def rotate_t_piece_visual(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    anchor_row, anchor_col = get_anchor(PieceType.T_PIECE, position, orientation)
    rotated_orientation = rotate_orientation(orientation, rotation)

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


def rotate_t_piece_right_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_t_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece_left_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_t_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece_floor_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_t_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece_right_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_t_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_t_piece_left_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_t_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece(
    matrix: Matrix,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...] | None:
    return _get_first_valid_rotation_position(
        matrix,
        position,
        orientation,
        rotation,
        (
            rotate_l_piece_visual,
            rotate_l_piece_right_wall_kick,
            rotate_l_piece_left_wall_kick,
            rotate_l_piece_floor_kick,
            rotate_l_piece_right_well_kick,
            rotate_l_piece_left_well_kick,
        ),
    )


def rotate_l_piece_visual(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    anchor_row, anchor_col = get_anchor(PieceType.L_PIECE, position, orientation)
    rotated_orientation = rotate_orientation(orientation, rotation)

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


def rotate_l_piece_right_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_l_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece_left_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_l_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece_floor_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_l_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece_right_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_l_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_l_piece_left_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_l_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece(
    matrix: Matrix,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...] | None:
    return _get_first_valid_rotation_position(
        matrix,
        position,
        orientation,
        rotation,
        (
            rotate_j_piece_visual,
            rotate_j_piece_right_wall_kick,
            rotate_j_piece_left_wall_kick,
            rotate_j_piece_floor_kick,
            rotate_j_piece_left_well_kick,
            rotate_j_piece_right_well_kick,
        ),
    )


def rotate_j_piece_visual(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    anchor_row, anchor_col = get_anchor(PieceType.J_PIECE, position, orientation)
    rotated_orientation = rotate_orientation(orientation, rotation)

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


def rotate_j_piece_right_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_j_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece_left_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_j_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece_floor_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_j_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece_right_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_j_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_j_piece_left_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_j_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece(
    matrix: Matrix,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...] | None:
    return _get_first_valid_rotation_position(
        matrix,
        position,
        orientation,
        rotation,
        (
            rotate_s_piece_visual,
            rotate_s_piece_right_wall_kick,
            rotate_s_piece_left_wall_kick,
            rotate_s_piece_floor_kick,
            rotate_s_piece_left_well_kick,
            rotate_s_piece_right_well_kick,
        ),
    )


def rotate_s_piece_visual(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    anchor_row, anchor_col = get_anchor(PieceType.S_PIECE, position, orientation)
    rotated_orientation = rotate_orientation(orientation, rotation)

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


def rotate_s_piece_right_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_s_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece_left_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_s_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece_floor_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_s_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece_right_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_s_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_s_piece_left_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_s_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece(
    matrix: Matrix,
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...] | None:
    return _get_first_valid_rotation_position(
        matrix,
        position,
        orientation,
        rotation,
        (
            rotate_z_piece_visual,
            rotate_z_piece_right_wall_kick,
            rotate_z_piece_left_wall_kick,
            rotate_z_piece_floor_kick,
            rotate_z_piece_left_well_kick,
            rotate_z_piece_right_well_kick,
        ),
    )


def rotate_z_piece_visual(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    anchor_row, anchor_col = get_anchor(PieceType.Z_PIECE, position, orientation)
    rotated_orientation = rotate_orientation(orientation, rotation)

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


def rotate_z_piece_right_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, -1)
    else:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, -1)

    new_position = rotate_z_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece_left_wall_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.SOUTH:
                kick_i, kick_j = (0, 1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (0, 1)

    new_position = rotate_z_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece_floor_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.EAST:
                kick_i, kick_j = (1, -1)
    else:
        match new_orientation:
            case PieceOrientation.WEST:
                kick_i, kick_j = (1, 1)

    new_position = rotate_z_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece_right_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, -1)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)

    new_position = rotate_z_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]


def rotate_z_piece_left_well_kick(
    position: tuple[tuple[int, int], ...],
    orientation: PieceOrientation,
    rotation: Rotation,
) -> tuple[tuple[int, int], ...]:
    new_orientation = rotate_orientation(orientation, rotation)
    kick_i, kick_j = (0, 0)
    if rotation == Rotation.CW:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 0)
    else:
        match new_orientation:
            case PieceOrientation.NORTH:
                kick_i, kick_j = (2, 1)

    new_position = rotate_z_piece_visual(position, orientation, rotation)
    return [(i + kick_i, j + kick_j) for (i, j) in new_position]
