"""
Core gameplay orchestration.
"""

from collections import deque
from enum import Enum, auto

import pygame

from input import InputManager
from matrix import Matrix
from piece import (
    PIECE_TO_COLOR_MAP,
    ActivePiece,
    PieceOrientation,
    PieceType,
    Rotation,
    generate_position_with_anchor,
    generate_random_bag,
    rotate_i_piece,
    rotate_j_piece,
    rotate_l_piece,
    rotate_s_piece,
    rotate_t_piece,
    rotate_z_piece,
)
from shared import Action, Color


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


class TranslateDirection(Enum):
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class Game:
    """
    Action requesters and resolvers should be placed within the Game class as it requires access to Game
    internals and follow internal Game rules.
    """

    CELL_SIZE = 30

    MATRIX_WIDTH = 10  # in unit of CELL_SIZE
    MATRIX_HEIGHT = 20  # in unit of CELL_SIZE
    TOP_MARGIN = 3  # in unit of CELL_SIZE
    FRAMED_PIECE_WIDTH = 5  # in unit of CELL_SIZE
    FRAMED_PIECE_HEIGHT = 3  # in unit of CELL_SIZE

    VISIBLE_QUEUE_SIZE = 6  # number of visible pieces in the queue

    COLOR_MAP = {
        Color.YELLOW: (255, 255, 0),
        Color.CYAN: (0, 255, 255),
        Color.PURPLE: (128, 0, 128),
        Color.ORANGE: (255, 165, 0),
        Color.LIGHT_BLUE: (0, 128, 254),
        Color.DARK_BLUE: (25, 25, 112),
        Color.GREEN: (0, 128, 0),
        Color.RED: (255, 0, 0),
        Color.BLACK: (25, 25, 25),
    }

    def __init__(self):
        # visible queue of pieces
        self.piece_queue: deque[PieceType] = deque(generate_random_bag())
        # bag from which we grab pieces to enqueue
        self.piece_bag: deque[PieceType] = deque(generate_random_bag())
        self.held_piece: PieceType | None = None
        self.hold_disabled: bool = False

        self.active_piece: ActivePiece | None = ActivePiece(PieceType.I_PIECE)
        self.action_queue: list[Action] = []
        self.matrix: Matrix = Matrix(
            matrix_width=self.MATRIX_WIDTH, matrix_height=self.MATRIX_HEIGHT
        )

        pygame.init()

        # calculate window width; A, B, C are the held piece, matrix, and queue respectively
        # * - A -- * - B -- * - C --
        window_width = (self.MATRIX_WIDTH + 5 + 5 + 4) * self.CELL_SIZE
        window_height = (self.MATRIX_HEIGHT + 1 + self.TOP_MARGIN) * self.CELL_SIZE

        self.screen = pygame.display.set_mode((window_width, window_height))
        self.clock = pygame.time.Clock()
        self.fps = 60  # frames per second
        self.frame_ticks = 0

        self.fall_speed = 0.8  # time in seconds it takes for the active piece to fall by one line
        self.fall_frame_rate = round(self.fall_speed * self.fps)

        self.lock_down_speed = 0.5  # time in seconds until piece is locked
        self.lock_down_frame_rate = round(self.lock_down_speed * self.fps)
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0

        self.input_manager: InputManager = PygameInputManager()
        self.ACTION_TO_CONTROL_MAP = {
            Action.RIGHT_SHIFT: self.right_shift,
            Action.LEFT_SHIFT: self.left_shift,
            Action.HARD_DROP: self.hard_drop,
            Action.SOFT_DROP: self.soft_drop,
            Action.CW_ROTATE: self.cw_rotate,
            Action.CCW_ROTATE: self.ccw_rotate,
            Action.HOLD: self.hold_piece,
            Action.FALL: self.fall,
            Action.QUIT: self.quit,
        }
        self.MOVEMENT_ACTIONS = {
            Action.RIGHT_SHIFT,
            Action.LEFT_SHIFT,
            Action.SOFT_DROP,
            Action.HARD_DROP,
            Action.CW_ROTATE,
            Action.CCW_ROTATE,
        }

        self.running = True

    def render(self):
        self.screen.fill(self.COLOR_MAP[Color.BLACK])

        self.render_framed_piece(
            piece_type=self.held_piece,
            offset=(self.CELL_SIZE, self.TOP_MARGIN * self.CELL_SIZE),
            draw_border=True,
        )
        self.render_matrix()
        self.render_queue()

    def render_framed_piece(
        self, piece_type: PieceType | None, offset: tuple[int, int], draw_border: bool
    ):
        """Render the 5 by 3 framing rectangle, along with its framed piece. Without any offset,
        these cells will be drawn in the top left corner of the pygame screen.
        """

        offset_x, offset_y = offset
        if draw_border:
            held_piece_rectangle = pygame.Rect(
                offset_x,
                offset_y,
                self.CELL_SIZE * self.FRAMED_PIECE_WIDTH,
                self.CELL_SIZE * self.FRAMED_PIECE_HEIGHT,
            )
            pygame.draw.rect(self.screen, self.COLOR_MAP[Color.CYAN], held_piece_rectangle, width=1)

        if piece_type is None:
            return

        position = generate_position_with_anchor(
            piece_type=piece_type,
            orientation=PieceOrientation.NORTH,
            anchor=(0, 0),
        )
        color = self.COLOR_MAP[PIECE_TO_COLOR_MAP[piece_type]]
        match piece_type:
            case PieceType.I_PIECE:
                top_margin = 1
                left_margin = 0.5
            case PieceType.O_PIECE:
                top_margin = 1.5
                left_margin = 0.5
            case _:
                top_margin = 1.5
                left_margin = 1
        for i, j in position:
            x = (j + left_margin) * self.CELL_SIZE
            # pygame has its origin at the top left of the screen with the positive x-axis
            # stretching from left to right and the positive y-axis stretching from top to
            # bottom; the position of our piece is generated from the horizontally mirrored
            # coordinate plane, i.e. the positive y-axis stretches from bottom to top; to
            # account for this difference, we flip the position by computing -1 - i
            y = (-1 - i + top_margin) * self.CELL_SIZE
            cell = pygame.Rect(x + offset_x, y + offset_y, self.CELL_SIZE, self.CELL_SIZE)
            pygame.draw.rect(self.screen, color, cell)

    def render_matrix(self):
        matrix_anchor_x, matrix_anchor_y = (self.FRAMED_PIECE_WIDTH + 2, self.TOP_MARGIN)
        for i in range(self.MATRIX_HEIGHT):
            for j in range(self.MATRIX_WIDTH):
                x = (j + matrix_anchor_x) * self.CELL_SIZE
                y = (self.MATRIX_HEIGHT - 1 - i + matrix_anchor_y) * self.CELL_SIZE

                cell = pygame.Rect(x, y, self.CELL_SIZE, self.CELL_SIZE)
                if self.matrix[i][j]:
                    color = self.COLOR_MAP[self.matrix[i][j]]
                    pygame.draw.rect(self.screen, color, cell)
                pygame.draw.rect(self.screen, self.COLOR_MAP[Color.CYAN], cell, width=1)
        for i, j in self.active_piece.position:
            x = (j + matrix_anchor_x) * self.CELL_SIZE
            y = (self.MATRIX_HEIGHT - 1 - i + matrix_anchor_y) * self.CELL_SIZE

            cell = pygame.Rect(x, y, self.CELL_SIZE, self.CELL_SIZE)
            color = self.COLOR_MAP[self.active_piece.color]
            pygame.draw.rect(self.screen, color, cell)

    def render_queue(self):
        offset_x = (3 + self.FRAMED_PIECE_WIDTH + self.MATRIX_WIDTH) * self.CELL_SIZE
        offset_y = self.TOP_MARGIN * self.CELL_SIZE
        queue_height = self.FRAMED_PIECE_HEIGHT * self.CELL_SIZE * self.VISIBLE_QUEUE_SIZE
        queue_width = self.FRAMED_PIECE_WIDTH * self.CELL_SIZE
        queue_rectangle = pygame.Rect(offset_x, offset_y, queue_width, queue_height)

        pygame.draw.rect(self.screen, self.COLOR_MAP[Color.CYAN], queue_rectangle, width=1)

        for i in range(self.VISIBLE_QUEUE_SIZE):
            self.render_framed_piece(
                piece_type=self.piece_queue[i],
                offset=(offset_x, offset_y + self.FRAMED_PIECE_HEIGHT * self.CELL_SIZE * i),
                draw_border=False,
            )

    def main(self):
        while self.running:
            self.frame_ticks += 1
            self.lock_down_frame_ticks += 1

            if self.lock_down_frame_ticks == self.lock_down_frame_rate and self.surface_contact():
                self.lock_down()

            action_queue = []
            if self.frame_ticks > 0 and self.frame_ticks % self.fall_frame_rate == 0:
                action_queue.append(Action.FALL)
            action_queue.extend(self.input_manager.poll())
            for action in action_queue:
                self.ACTION_TO_CONTROL_MAP[action]()

                if self.surface_contact():
                    self.switch_on_lock_down()
                if self.lock_down_active:
                    if action in self.MOVEMENT_ACTIONS:
                        self.lock_down_frame_ticks = 0

                self.matrix.clear()

            self.render()
            pygame.display.flip()
            self.clock.tick(self.fps)

    def switch_off_lock_down(self) -> None:
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0

    def switch_on_lock_down(self) -> None:
        if not self.lock_down_active:
            self.lock_down_frame_ticks = 0
        self.lock_down_active = True

    def surface_contact(self) -> bool:
        new_position = self.get_active_piece_translation(TranslateDirection.DOWN)
        return self.matrix.check_collision(new_position)

    def quit(self) -> None:
        self.running = False

    def get_active_piece_translation(self, direction: TranslateDirection) -> list[tuple[int, int]]:
        match direction:
            case TranslateDirection.DOWN:
                return [(i - 1, j) for (i, j) in self.active_piece.position]
            case TranslateDirection.LEFT:
                return [(i, j - 1) for (i, j) in self.active_piece.position]
            case TranslateDirection.RIGHT:
                return [(i, j + 1) for (i, j) in self.active_piece.position]

    def fall(self):
        new_position = self.get_active_piece_translation(TranslateDirection.DOWN)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position

    def pull_active_piece_from_queue(self):
        self.switch_off_lock_down()

        self.active_piece = ActivePiece(self.piece_queue.popleft())
        self.piece_queue.append(self.piece_bag.popleft())
        if not self.piece_bag:
            self.piece_bag = deque(generate_random_bag())

    def lock_down(self) -> None:
        """Lock down the active piece and pull the next active piece from the queue."""

        if not self.surface_contact():
            raise RuntimeError("lock_down must only be called on surface contact")

        for i, j in self.active_piece.position:
            self.matrix[i][j] = self.active_piece.color
        self.hold_disabled = False

        self.pull_active_piece_from_queue()

    def hard_drop(self) -> None:
        while not self.matrix.check_collision(
            self.get_active_piece_translation(TranslateDirection.DOWN)
        ):
            self.active_piece.position = self.get_active_piece_translation(TranslateDirection.DOWN)
        self.lock_down()

    def soft_drop(self) -> None:
        new_position = self.get_active_piece_translation(TranslateDirection.DOWN)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position

    def left_shift(self) -> None:
        new_position = self.get_active_piece_translation(TranslateDirection.LEFT)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position

    def right_shift(self) -> None:
        new_position = self.get_active_piece_translation(TranslateDirection.RIGHT)
        if not self.matrix.check_collision(new_position):
            self.active_piece.position = new_position

    def hold_piece(self) -> None:
        if self.hold_disabled:
            return

        if self.held_piece is None:
            self.held_piece = self.active_piece.piece_type
            self.pull_active_piece_from_queue()
        else:
            active_piece_type = self.active_piece.piece_type
            self.active_piece = ActivePiece(self.held_piece)
            self.held_piece = active_piece_type
        self.hold_disabled = True

    def cw_rotate(self) -> None:
        match self.active_piece.piece_type:
            case PieceType.I_PIECE:
                rotate_i_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.T_PIECE:
                rotate_t_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.L_PIECE:
                rotate_l_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.J_PIECE:
                rotate_j_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.S_PIECE:
                rotate_s_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.Z_PIECE:
                rotate_z_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.O_PIECE:
                pass  # no rotation for O piece

    def ccw_rotate(self) -> None:
        match self.active_piece.piece_type:
            case PieceType.I_PIECE:
                rotate_i_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.T_PIECE:
                rotate_t_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.L_PIECE:
                rotate_l_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.J_PIECE:
                rotate_j_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.S_PIECE:
                rotate_s_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.Z_PIECE:
                rotate_z_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.O_PIECE:
                pass  # no rotation for O piece


if __name__ == "__main__":
    game = Game()

    game.main()
