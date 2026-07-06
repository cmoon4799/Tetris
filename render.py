import pygame

from engine import Engine
from piece import (
    PIECE_TO_COLOR_MAP,
    generate_anchor_relative_position,
)
from shared import CONFIG, Color, PieceOrientation, PieceType


class Renderer:
    CELL_SIZE = 30

    TOP_MARGIN = 3  # in unit of CELL_SIZE
    BOTTOM_MARGIN = 1
    FRAMED_PIECE_WIDTH = 5  # in unit of CELL_SIZE
    FRAMED_PIECE_HEIGHT = 3  # in unit of CELL_SIZE

    VISIBLE_QUEUE_SIZE = CONFIG.visible_queue_size
    MATRIX_HEIGHT = CONFIG.matrix_height
    MATRIX_WIDTH = CONFIG.matrix_width

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
        Color.PINK: (255, 192, 203),
    }

    def __init__(self, engine: Engine):
        self.engine = engine

        # the rendered space takes the following form
        # * A * B * C *
        # where A, B, C are the held piece, matrix, queue respectively and * represents the
        # borders in between
        horizontal_sections = [
            self.MATRIX_WIDTH,
            self.FRAMED_PIECE_WIDTH,
            self.FRAMED_PIECE_WIDTH,
        ]
        window_width = (sum(horizontal_sections) + len(horizontal_sections) + 1) * self.CELL_SIZE
        window_height = (self.MATRIX_HEIGHT + self.TOP_MARGIN + self.BOTTOM_MARGIN) * self.CELL_SIZE
        self.screen = pygame.display.set_mode((window_width, window_height))

    def render(self) -> None:
        self.screen.fill(self.COLOR_MAP[Color.BLACK])

        self.render_held_piece()
        self.render_matrix()
        self.render_active_piece()
        self.render_queue()

        pygame.display.flip()

    def render_held_piece(self) -> None:
        """Render the held piece in its framing rectangle."""

        # render framing rectangle
        offset_x, offset_y = (self.CELL_SIZE, self.TOP_MARGIN * self.CELL_SIZE)
        held_piece_rectangle = pygame.Rect(
            offset_x,
            offset_y,
            self.CELL_SIZE * self.FRAMED_PIECE_WIDTH,
            self.CELL_SIZE * self.FRAMED_PIECE_HEIGHT,
        )
        pygame.draw.rect(self.screen, self.COLOR_MAP[Color.CYAN], held_piece_rectangle, width=1)

        # render piece
        self.render_framed_piece(self.engine.held_piece, (offset_x, offset_y))

    def render_framed_piece(self, piece_type: PieceType | None, offset: tuple[int, int]) -> None:
        """Render a piece in its North orientation centered in a 5 by 3 rectangle. Without any
        offset, these cells will be drawn in the top left corner of the pygame screen.
        """
        if piece_type is None:
            return

        offset_x, offset_y = offset
        position = generate_anchor_relative_position(
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

    def render_matrix(self) -> None:
        """Render the game matrix and active piece."""
        matrix_anchor_x, matrix_anchor_y = (self.FRAMED_PIECE_WIDTH + 2, self.TOP_MARGIN)
        for i in range(self.MATRIX_HEIGHT + self.engine.BUFFER_HEIGHT):
            for j in range(self.MATRIX_WIDTH):
                x = (j + matrix_anchor_x) * self.CELL_SIZE
                y = (self.MATRIX_HEIGHT - 1 - i + matrix_anchor_y) * self.CELL_SIZE

                cell = pygame.Rect(x, y, self.CELL_SIZE, self.CELL_SIZE)
                if self.engine.matrix[i][j]:
                    color = self.COLOR_MAP[self.engine.matrix[i][j]]
                    pygame.draw.rect(self.screen, color, cell)
                if i < self.MATRIX_HEIGHT:
                    pygame.draw.rect(self.screen, self.COLOR_MAP[Color.CYAN], cell, width=1)

    def render_active_piece(self) -> None:
        matrix_anchor_x, matrix_anchor_y = (self.FRAMED_PIECE_WIDTH + 2, self.TOP_MARGIN)
        for i, j in self.engine.active_piece.position:
            x = (j + matrix_anchor_x) * self.CELL_SIZE
            y = (self.MATRIX_HEIGHT - 1 - i + matrix_anchor_y) * self.CELL_SIZE

            cell = pygame.Rect(x, y, self.CELL_SIZE, self.CELL_SIZE)
            # color = self.COLOR_MAP[self.engine.active_piece.color]
            color = self.COLOR_MAP[Color.PINK]
            pygame.draw.rect(self.screen, color, cell)

    def render_queue(self) -> None:
        """Render the piece preview queue."""
        offset_x = (3 + self.FRAMED_PIECE_WIDTH + self.MATRIX_WIDTH) * self.CELL_SIZE
        offset_y = self.TOP_MARGIN * self.CELL_SIZE
        queue_height = self.FRAMED_PIECE_HEIGHT * self.CELL_SIZE * self.VISIBLE_QUEUE_SIZE
        queue_width = self.FRAMED_PIECE_WIDTH * self.CELL_SIZE
        queue_rectangle = pygame.Rect(offset_x, offset_y, queue_width, queue_height)

        pygame.draw.rect(self.screen, self.COLOR_MAP[Color.CYAN], queue_rectangle, width=1)

        for i in range(self.VISIBLE_QUEUE_SIZE):
            self.render_framed_piece(
                piece_type=self.engine.piece_queue[i],
                offset=(offset_x, offset_y + self.FRAMED_PIECE_HEIGHT * self.CELL_SIZE * i),
            )
