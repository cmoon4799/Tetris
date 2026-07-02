"""
Core gameplay orchestration.
"""


from piece import PieceType, PieceOrientation, PIECE_TO_COLOR_MAP, generate_random_bag
from protocol import Action, InputManager, Color
import pygame
from collections import deque
from enum import Enum, auto


class ActivePiece:
    def __init__(self, piece_type: PieceType):
        self.piece_type: PieceType = piece_type
        self.orientation: PieceOrientation = PieceOrientation.NORTH
        self.position: list[tuple[int, int]] = []
        self.color: Color = PIECE_TO_COLOR_MAP[self.piece_type]

        self.load_starting_position()

    def load_starting_position(self):
        match self.piece_type:
            case PieceType.I_PIECE:
                self.position = [(20, 3), (20, 4), (20, 5), (20, 6)]
            case PieceType.O_PIECE:
                self.position = [(20, 4), (20, 5), (21, 4), (21, 5)]
            case PieceType.T_PIECE:
                self.position = [(20, 3), (20, 4), (20, 5), (21, 4)]
            case PieceType.L_PIECE:
                self.position = [(20, 3), (20, 4), (20, 5), (21, 3)]
            case PieceType.J_PIECE:
                self.position = [(20, 3), (20, 4), (20, 5), (21, 5)]
            case PieceType.S_PIECE:
                self.position = [(20, 3), (20, 4), (21, 4), (21, 5)]
            case PieceType.Z_PIECE:
                self.position = [(21, 3), (21, 4), (20, 4), (20, 5)]


class PygameInputManager(InputManager):
    KEY_TO_ACTION_MAP = {
        pygame.K_RIGHT: Action.RIGHT_SHIFT,
        pygame.K_LEFT: Action.LEFT_SHIFT,
        pygame.K_SPACE: Action.HARD_DROP,
        pygame.K_LSHIFT: Action.SAVE_PIECE,
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
        self.saved_piece: PieceType | None = None
        self.save_disabled: bool = False

        self.active_piece: ActivePiece | None = ActivePiece(PieceType.I_PIECE)
        self.action_queue: list[Action] = []
        self.matrix: list[list[int]] = [
            [0 for _ in range(self.MATRIX_WIDTH)] for _ in range(self.MATRIX_HEIGHT)]

        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.fps = 60  # frames per second
        self.frame_ticks = 0

        self.fall_speed = 0.8  # time it takes for the active piece to fall by one line
        self.fall_frame_rate = round(self.fall_speed * self.fps)

        self.lock_down_speed = 0.5  # time until piece is locked
        self.lock_down_frame_rate = round(self.lock_down_speed * self.fps)
        self.lock_down_active = False
        self.lock_down_frame_ticks = 0

        self.input_manager: InputManager = PygameInputManager()
        self.ACTION_TO_CONTROL_MAP = {
            Action.RIGHT_SHIFT: self.right_shift,
            Action.LEFT_SHIFT: self.left_shift,
            Action.HARD_DROP: self.hard_drop,
            Action.SAVE_PIECE: self.save_piece,
        }

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
        running = True
        while running:
            self.frame_ticks += 1
            self.lock_down_frame_ticks += 1

            if self.lock_down_active:
                if self.lock_down_frame_ticks > 0 and self.lock_down_frame_ticks % self.lock_down_frame_rate == 0:
                    self.lock_down()

            if self.frame_ticks > 0 and self.frame_ticks % self.fall_frame_rate == 0:
                self.fall()

            for action in self.input_manager.poll():
                if action == Action.QUIT:
                    running = False
                else:
                    self.ACTION_TO_CONTROL_MAP[action]()
            self.render()
            pygame.display.flip()
            self.clock.tick(self.fps)

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
        # landed on a surface, begin lock down
        if self.check_collision(new_position):
            self.lock_down_active = True
            self.lock_down_frame_ticks = 0
        else:
            if self.lock_down_active:
                self.lock_down_frame_ticks = 0
            self.active_piece.position = new_position

    def pull_active_piece_from_queue(self):
        self.active_piece = ActivePiece(self.piece_queue.popleft())
        self.piece_queue.append(self.piece_bag.popleft())
        if not self.piece_bag:
            self.piece_bag = deque(generate_random_bag())

    def lock_down(self):
        for i, j in self.active_piece.position:
            self.matrix[i][j] = self.active_piece.color

        self.lock_down_active = False
        self.lock_down_frame_ticks = 0
        self.save_disabled = False
        self.pull_active_piece_from_queue()

    def hard_drop(self):
        while not self.check_collision(self.get_active_piece_translation(TranslateDirection.DOWN)):
            self.active_piece.position = self.get_active_piece_translation(
                TranslateDirection.DOWN)
        self.lock_down()

    def soft_drop(self): ...

    def left_shift(self):
        new_position = self.get_active_piece_translation(
            TranslateDirection.LEFT)
        if self.check_collision(new_position):
            return
        self.active_piece.position = new_position

    def right_shift(self):
        new_position = self.get_active_piece_translation(
            TranslateDirection.RIGHT)
        if self.check_collision(new_position):
            return
        self.active_piece.position = new_position

    def check_collision(self, position: list[tuple[int, int]]):
        """Check if the provided position collides with existing pieces of the matrix or the walls of the matrix."""

        for i, j in position:
            if j >= self.MATRIX_WIDTH or j < 0:  # wall collision
                return True
            if i < 0:  # floor collision
                return True
            # matrix collision
            if i < self.MATRIX_HEIGHT and self.matrix[i][j]:
                return True

        return False

    def save_piece(self):
        if self.save_disabled:
            return

        if self.saved_piece is None:
            self.saved_piece = self.active_piece.piece_type
            self.pull_active_piece_from_queue()
        else:
            active_piece_type = self.active_piece.piece_type
            self.active_piece = ActivePiece(self.saved_piece)
            self.saved_piece = active_piece_type
        self.save_disabled = True

    def rotate_piece(self):
        ...

    def quit(self): ...


if __name__ == "__main__":
    game = Game()

    game.main()
