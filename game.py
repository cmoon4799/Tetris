"""
Core gameplay orchestration.
"""


from input import InputManager
from piece import ActivePiece, PieceType, generate_random_bag, rotate_i_piece, Rotation, rotate_t_piece, rotate_l_piece
from shared import Action, Color
import pygame
from collections import deque
from enum import Enum, auto
from matrix import Matrix


class PygameInputManager(InputManager):
    KEY_TO_ACTION_MAP = {
        pygame.K_RIGHT: Action.RIGHT_SHIFT,
        pygame.K_LEFT: Action.LEFT_SHIFT,
        pygame.K_UP: Action.CW_ROTATE,
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
                print("appending quit")
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

    MATRIX_WIDTH = 10
    MATRIX_HEIGHT = 20
    CELL_SIZE = 30
    WINDOW_WIDTH = (MATRIX_WIDTH + 2) * CELL_SIZE
    WINDOW_HEIGHT = (MATRIX_HEIGHT + 4) * CELL_SIZE
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

        self.active_piece: ActivePiece | None = ActivePiece(PieceType.L_PIECE)
        self.action_queue: list[Action] = []
        self.matrix: Matrix = Matrix(
            matrix_height=self.MATRIX_HEIGHT, matrix_width=self.MATRIX_WIDTH)

        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
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
            Action.CW_ROTATE: self.cw_rotate,
            Action.CCW_ROTATE: self.ccw_rotate,
            Action.HOLD: self.hold_piece,
            Action.FALL: self.fall,
            Action.QUIT: self.quit,
        }
        self.MOVEMENT_ACTIONS = {Action.RIGHT_SHIFT, Action.LEFT_SHIFT,
                                 Action.SOFT_DROP, Action.HARD_DROP, Action.CW_ROTATE, Action.CCW_ROTATE}

        self.running = True

    def render(self):
        self.screen.fill(self.COLOR_MAP[Color.BLACK])

        for i in range(self.MATRIX_HEIGHT):
            for j in range(self.MATRIX_WIDTH):
                x = (j + 1) * self.CELL_SIZE
                y = (i + 2) * self.CELL_SIZE

                cell = pygame.Rect(x, y, self.CELL_SIZE, self.CELL_SIZE)

                if self.matrix[self.MATRIX_HEIGHT - 1 - i][j]:
                    color = self.COLOR_MAP[self.matrix[self.MATRIX_HEIGHT - 1 - i][j]]
                    pygame.draw.rect(self.screen, color, cell)
                pygame.draw.rect(
                    self.screen, self.COLOR_MAP[Color.CYAN], cell, width=1)

        for i, j in self.active_piece.position:
            x = (j + 1) * self.CELL_SIZE
            y = (self.MATRIX_HEIGHT + 1 - i) * self.CELL_SIZE

            cell = pygame.Rect(x, y, self.CELL_SIZE, self.CELL_SIZE)
            color = self.COLOR_MAP[self.active_piece.color]
            pygame.draw.rect(self.screen, color, cell)

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

            self.render()
            pygame.display.flip()
            self.clock.tick(self.fps)

    def switch_off_lock_down(self):
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0

    def switch_on_lock_down(self):
        if not self.lock_down_active:
            self.lock_down_frame_ticks = 0
        self.lock_down_active = True

    def surface_contact(self):
        new_position = self.get_active_piece_translation(
            TranslateDirection.DOWN)
        return self.matrix.check_collision(new_position)

    def quit(self):
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
        new_position = self.get_active_piece_translation(
            TranslateDirection.DOWN)
        if self.matrix.check_collision(new_position):
            return
        self.active_piece.position = new_position

    def pull_active_piece_from_queue(self):
        self.active_piece = ActivePiece(self.piece_queue.popleft())
        self.piece_queue.append(self.piece_bag.popleft())
        if not self.piece_bag:
            self.piece_bag = deque(generate_random_bag())

    def reset(self):
        ...

    def lock_down(self):
        assert self.surface_contact(), "lock_down must only be called on surface contact"

        for i, j in self.active_piece.position:
            self.matrix[i][j] = self.active_piece.color
        self.hold_disabled = False
        self.switch_off_lock_down()

        self.pull_active_piece_from_queue()

    def hard_drop(self):
        while not self.matrix.check_collision(self.get_active_piece_translation(TranslateDirection.DOWN)):
            self.active_piece.position = self.get_active_piece_translation(
                TranslateDirection.DOWN)
        self.lock_down()

    def soft_drop(self): ...

    def left_shift(self):
        new_position = self.get_active_piece_translation(
            TranslateDirection.LEFT)
        if self.matrix.check_collision(new_position):
            return
        self.active_piece.position = new_position

    def right_shift(self):
        new_position = self.get_active_piece_translation(
            TranslateDirection.RIGHT)
        if self.matrix.check_collision(new_position):
            return
        self.active_piece.position = new_position

    def hold_piece(self):
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

    def cw_rotate(self):
        match self.active_piece.piece_type:
            case PieceType.I_PIECE:
                rotate_i_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.T_PIECE:
                rotate_t_piece(self.matrix, self.active_piece, Rotation.CW)
            case PieceType.L_PIECE:
                rotate_l_piece(self.matrix, self.active_piece, Rotation.CW)

    def ccw_rotate(self):
        match self.active_piece.piece_type:
            case PieceType.I_PIECE:
                rotate_i_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.T_PIECE:
                rotate_t_piece(self.matrix, self.active_piece, Rotation.CCW)
            case PieceType.L_PIECE:
                rotate_l_piece(self.matrix, self.active_piece, Rotation.CCW)


if __name__ == "__main__":
    game = Game()

    game.main()
