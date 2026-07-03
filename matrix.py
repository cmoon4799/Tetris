from shared import Color


class Matrix:
    def __init__(self, matrix_height: int, matrix_width: int):
        self.matrix_height = matrix_height
        self.matrix_width = matrix_width
        self._matrix: list[list[Color]] = [[0 for _ in range(matrix_width)]
                                           for _ in range(matrix_height)]

    def check_collision(self, position: list[tuple[int, int]]):
        """Check if the provided position collides with existing pieces of the matrix or the walls of the matrix."""

        for i, j in position:
            # wall collision
            if j >= self.matrix_width or j < 0:
                return True
            # floor collision
            if i < 0:
                return True
            # matrix collision
            if i < self.matrix_height and self._matrix[i][j]:
                return True

        return False

    def __getitem__(self, index: int):
        return self._matrix[index]
