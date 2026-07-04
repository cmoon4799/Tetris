from shared import Color


class Matrix:
    def __init__(self, matrix_width: int, matrix_height: int):
        self.matrix_width = matrix_width
        self.matrix_height = matrix_height
        self._matrix: list[list[Color]] = [
            [0 for _ in range(matrix_width)] for _ in range(matrix_height)
        ]

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

    def clear(self):
        surviving_rows = []
        for row in self._matrix:
            if any(cell == 0 for cell in row):
                surviving_rows.append(row)

        self._matrix = [*surviving_rows]
        self._matrix += [
            [0 for _ in range(self.matrix_width)]
            for _ in range(self.matrix_height - len(surviving_rows))
        ]

    def __getitem__(self, index: int):
        return self._matrix[index]
