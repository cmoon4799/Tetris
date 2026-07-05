import torch
import torch.nn.functional as F
from torch import nn

from shared import CONFIG, PLAYER_ACTION_SPACE, Observation, PieceOrientation, PieceType

"""
Deep Q-Network

Observation Tensor Sketch
- Binary encoding of occupied cells of the matrix (H X W)
- Binary encoding of active piece position (H X W)
- One hot encoding of active piece type (7)
- One hot encoding of orientation (4)
- One hot encoding of held piece type (7 + 1)
- Boolean indicating whether hold is disabled (1)
- One hot encoding of each piece in the queue (6 x 7)
- Normalized value of gravity frames remaining (1)
- Boolean indicating if lock down is active (1)
- Normalized value of lock down frames remaining (1)
- Normalized value of lock down resets remaining (1)

Reward Thoughts
- Near defeat, all actions are approximately equal, meaning we should be careful about
how we weigh the end result of a run for a state reward, if at all.
- 
"""

PIECE_TYPE_TO_INDEX = {
    None: 0,
    PieceType.I_PIECE: 1,
    PieceType.O_PIECE: 2,
    PieceType.T_PIECE: 3,
    PieceType.J_PIECE: 4,
    PieceType.L_PIECE: 5,
    PieceType.S_PIECE: 6,
    PieceType.Z_PIECE: 7,
}

ORIENTATION_TO_INDEX = {
    PieceOrientation.NORTH: 0,
    PieceOrientation.EAST: 1,
    PieceOrientation.SOUTH: 2,
    PieceOrientation.WEST: 3,
}


class DQN(nn.Module):
    FLAT_DIMENSION = 73

    # configuration constants
    MATRIX_HEIGHT = CONFIG.matrix_height
    MATRIX_WIDTH = CONFIG.matrix_width
    FPS = CONFIG.fps
    GRAVITY_SPEED = CONFIG.gravity_speed
    LOCK_DOWN_SPEED = CONFIG.lock_down_speed
    LOCK_DOWN_RESET_LIMIT = CONFIG.lock_down_reset_limit

    def __init__(self):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(in_channels=2, out_channels=16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Flatten(),
        )

        convolution_out_size = 32 * self.MATRIX_HEIGHT * self.MATRIX_WIDTH
        combined_dimension = convolution_out_size + self.FLAT_DIMENSION

        self.fc = nn.Sequential(
            nn.Linear(combined_dimension, 256),
            nn.ReLU(),
            nn.Linear(256, len(PLAYER_ACTION_SPACE)),
        )

    def tensorize_spatial_features(self, observation: Observation) -> torch.Tensor:
        matrix_grid = [[1 if cell is not None else 0 for cell in row] for row in observation.matrix]
        matrix_tensor = torch.tensor(matrix_grid, dtype=torch.float32)

        matrix_height = len(observation.matrix)
        matrix_width = len(observation.matrix[0])

        active_grid = torch.zeros((matrix_height, matrix_width), dtype=torch.float32)
        for i, j in observation.active_piece_position:
            active_grid[i][j] = 1.0

        return torch.stack([matrix_tensor, active_grid], dim=0)

    def tensorize_flat_features(self, observation: Observation) -> torch.Tensor:
        flat_features = []
        PIECE_TYPE_CLASS_COUNT = len(PIECE_TYPE_TO_INDEX)

        # one hot encoding of active piece type (shape 8)
        active_index = PIECE_TYPE_TO_INDEX[observation.active_piece_type]
        flat_features.append(
            F.one_hot(torch.tensor(active_index), num_classes=PIECE_TYPE_CLASS_COUNT)
        )

        # one hot encoding of active piece orientation (shape 4)
        orientation_index = ORIENTATION_TO_INDEX[observation.active_piece_orientation]
        flat_features.append(F.one_hot(torch.tensor(orientation_index), num_classes=4))

        # one hot encoding of held piece (shape 8)
        held_piece_index = PIECE_TYPE_TO_INDEX[observation.active_piece_type]
        flat_features.append(
            F.one_hot(torch.tensor(held_piece_index), num_classes=PIECE_TYPE_CLASS_COUNT)
        )

        # boolean encoding of hold_disabled
        flat_features.append(torch.tensor([float(observation.hold_disabled)]))

        # one hot encoding of piece queue (shape 6, 8)
        flat_features.append(
            F.one_hot(
                torch.tensor(
                    [PIECE_TYPE_TO_INDEX[piece_type] for piece_type in observation.piece_queue],
                ),
                num_classes=PIECE_TYPE_CLASS_COUNT,
            ).flatten()
        )

        max_gravity = self.GRAVITY_SPEED * self.FPS
        max_lockdown = self.LOCK_DOWN_SPEED * self.FPS
        max_resets = self.LOCK_DOWN_RESET_LIMIT

        flat_features.append(torch.tensor([observation.gravity_frames_remaining / max_gravity]))
        flat_features.append(torch.tensor([float(observation.lock_down_active)]))
        flat_features.append(torch.tensor([observation.lock_down_frames_remaining / max_lockdown]))
        flat_features.append(torch.tensor([observation.lock_down_resets_remaining / max_resets]))

        flat_tensor = torch.cat(flat_features).float()

        if len(flat_tensor) != self.FLAT_DIMENSION:
            raise ValueError(
                f"Flat feature tensor dimension mismatch. Expected shape ({self.EXPECTED_FLAT_DIM},) but got {flat_tensor.shape}"
            )

        return flat_tensor

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        return self.network(observation)
