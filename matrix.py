from shared import Color


class Matrix:
    def __init__(self, matrix_width: int, matrix_height: int):
        self.matrix_width: int = matrix_width
        self.matrix_height: int = matrix_height
        self._matrix: list[list[Color | None]] = [
            [None for _ in range(matrix_width)] for _ in range(matrix_height)
        ]
        self.lines_cleared: int = 0

    def check_collision(self, position: list[tuple[int, int]]) -> bool:
        """Check if the provided position collides with existing pieces of the matrix or the walls
        of the matrix.
        """

        for i, j in position:
            # wall collision
            if j >= self.matrix_width or j < 0:
                return True
            # floor collision
            if i < 0:
                return True
            # matrix collision
            if i < self.matrix_height and self._matrix[i][j] is not None:
                return True

        return False

    def clear(self) -> None:
        surviving_rows = []
        for row in self._matrix:
            if any(cell is None for cell in row):
                surviving_rows.append(row)
            else:
                self.lines_cleared += 1

        self._matrix = [*surviving_rows]
        self._matrix += [
            [None for _ in range(self.matrix_width)]
            for _ in range(self.matrix_height - len(surviving_rows))
        ]

    def __getitem__(self, index: int) -> list[Color | None]:
        if not 0 <= index < self.matrix_height:
            raise IndexError(f"matrix index {index} out of range [0, {self.matrix_height})")
        return self._matrix[index]
