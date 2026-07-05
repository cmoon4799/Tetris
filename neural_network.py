import torch
from torch import nn

"""
Observation Tensor
- Binary encoding of occupied cells of the matrix
- 
"""


class DQN(nn.Module):
    def __init__(self, observation_size: int, action_count: int):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(observation_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_count),
        )

    def forward(self, observation: torch.Tensor) -> torch.Tensor:
        return self.network(observation)
