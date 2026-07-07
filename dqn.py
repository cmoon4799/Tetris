import os
import random
from collections import deque
from typing import NamedTuple, Sequence

import torch
import torch.nn.functional as F
import torch.optim as optim
from torch import nn

from engine import Engine
from render import Renderer
from shared import (
    CONFIG,
    PLAYER_ACTION_SPACE,
    Action,
    Color,
    Observation,
    PieceOrientation,
    PieceType,
    RunOutcome,
)

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

DQN_PT_FILEPATH = "tetris_dqn.pt"


class Transition(NamedTuple):
    spatial: torch.Tensor
    flat: torch.Tensor
    action: Action
    reward: float
    terminated: bool
    next_spatial: torch.Tensor
    next_flat: torch.Tensor
    next_action_mask: torch.Tensor


class TransitionBatch(NamedTuple):
    spatial_tensors: torch.Tensor
    flat_tensors: torch.Tensor
    actions: torch.Tensor
    rewards: torch.Tensor
    terminated_flags: torch.Tensor
    next_spatial_tensors: torch.Tensor
    next_flat_tensors: torch.Tensor
    next_action_masks: torch.Tensor


class ReplayBuffer:
    def __init__(self, buffer_capacity: int = 100_000):
        self.buffer: deque[Transition] = deque(maxlen=buffer_capacity)

    def push(
        self,
        spatial: torch.Tensor,
        flat: torch.Tensor,
        action: Action,
        reward: float,
        terminated: bool,
        next_spatial: torch.Tensor,
        next_flat: torch.Tensor,
        next_action_mask: torch.Tensor,
    ):
        self.buffer.append(
            Transition(
                spatial=spatial.cpu(),
                flat=flat.cpu(),
                action=action,
                reward=reward,
                terminated=terminated,
                next_spatial=next_spatial.cpu(),
                next_flat=next_flat.cpu(),
                next_action_mask=next_action_mask.cpu(),
            )
        )

    def sample(self, batch_size: int) -> TransitionBatch:
        batch: list[Transition] = random.sample(self.buffer, batch_size)

        spatial_tensors = tuple(t.spatial for t in batch)
        flat_tensors = tuple(t.flat for t in batch)
        actions = tuple(t.action.value for t in batch)
        rewards = tuple(t.reward for t in batch)
        terminated_flags = tuple(t.terminated for t in batch)
        next_spatial_tensors = tuple(t.next_spatial for t in batch)
        next_flat_tensors = tuple(t.next_flat for t in batch)
        next_action_masks = tuple(t.next_action_mask for t in batch)

        # tensors are of the shape (batch_size, ...)
        return TransitionBatch(
            spatial_tensors=torch.stack(spatial_tensors),
            flat_tensors=torch.stack(flat_tensors),
            actions=torch.tensor(actions, dtype=torch.int64),
            rewards=torch.tensor(rewards, dtype=torch.float32),
            terminated_flags=torch.tensor(terminated_flags, dtype=torch.float32),
            next_spatial_tensors=torch.stack(next_spatial_tensors),
            next_flat_tensors=torch.stack(next_flat_tensors),
            next_action_masks=torch.stack(next_action_masks),
        )

    def __len__(self) -> int:
        return len(self.buffer)


class DQN(nn.Module):
    MATRIX_HEIGHT = CONFIG.matrix_height + CONFIG.buffer_height
    MATRIX_WIDTH = CONFIG.matrix_width
    FPS = CONFIG.fps
    GRAVITY_SPEED = CONFIG.gravity_speed
    LOCK_DOWN_SPEED = CONFIG.lock_down_speed
    LOCK_DOWN_RESET_LIMIT = CONFIG.lock_down_reset_limit

    FLAT_FEATURE_DIMENSION = 73
    SPATIAL_FEATURE_DIMENSION = 2 * MATRIX_HEIGHT * MATRIX_WIDTH

    def __init__(self, gamma: float = 0.99):
        super().__init__()
        self.gamma = gamma

        # channel 1 represents the matrix; channel 2 represents the active piece position
        self.convolution = nn.Conv2d(in_channels=2, out_channels=16, kernel_size=3, padding=1)
        convolution_dimension = 16 * self.MATRIX_HEIGHT * self.MATRIX_WIDTH

        spatial_dimension = 128
        flat_dimension = 32
        self.spatial_fc = nn.Linear(convolution_dimension, spatial_dimension)
        self.flat_fc = nn.Linear(self.FLAT_FEATURE_DIMENSION, flat_dimension)

        self.fc1 = nn.Linear(spatial_dimension + flat_dimension, 256)
        self.fc2 = nn.Linear(256, len(PLAYER_ACTION_SPACE))

    def forward(self, spatial_tensor: torch.Tensor, flat_tensor: torch.Tensor) -> torch.Tensor:
        expected_spatial_tensor_dim = 4
        if spatial_tensor.dim() != expected_spatial_tensor_dim:
            raise ValueError(
                f"""
                Unexpected spatial tensor dimension.
                Expected {expected_spatial_tensor_dim} but got {spatial_tensor.dim()}.
                """
            )
        expected_flat_tensor_dim = 2
        if flat_tensor.dim() != expected_flat_tensor_dim:
            raise ValueError(
                f"""
                Unexpected spatial tensor dimension.
                Expected {expected_flat_tensor_dim} but got {flat_tensor.dim()}.
                """
            )

        # shape (16, MATRIX_HEIGHT, MATRIX_WIDTH)
        x_spatial = F.relu(self.convolution(spatial_tensor))
        # flatten into (batch_size, 16 * MATRIX_HEIGHT * MATRIX_WIDTH)
        x_spatial = x_spatial.view(x_spatial.size(0), -1)
        x_spatial_features = F.relu(self.spatial_fc(x_spatial))

        x_flat_features = F.relu(self.flat_fc(flat_tensor))

        # fuse by concatenating
        x_combined = torch.cat([x_spatial_features, x_flat_features], dim=1)

        x = F.relu(self.fc1(x_combined))
        q_values = self.fc2(x)

        return q_values


class DQNAgent:
    def __init__(
        self,
        gamma: float = 0.99,
        lr: float = 1e-4,
        buffer_capacity: int = 10_000,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        self.gamma = gamma

        self.model = DQN().to(self.device)
        self.target_model = DQN().to(self.device)

        self.target_model.load_state_dict(self.model.state_dict())
        self.target_model.eval()
        for parameter in self.target_model.parameters():
            parameter.requires_grad = False

        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)

        self.replay_buffer = ReplayBuffer(buffer_capacity=buffer_capacity)

        self.steps = 0
        self.target_update_frequency = 1000

    def tensorize_spatial_features(self, observation: Observation) -> torch.Tensor:
        matrix_grid = [[1 if cell is not None else 0 for cell in row] for row in observation.matrix]
        matrix_tensor = torch.tensor(matrix_grid, dtype=torch.float32)

        matrix_height = len(observation.matrix)
        matrix_width = len(observation.matrix[0])

        active_grid_tensor = torch.zeros((matrix_height, matrix_width), dtype=torch.float32)
        for i, j in observation.active_piece_position:
            active_grid_tensor[i][j] = 1.0

        return torch.stack([matrix_tensor, active_grid_tensor], dim=0)

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
        held_piece_index = PIECE_TYPE_TO_INDEX[observation.held_piece]
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

        max_gravity = CONFIG.gravity_speed * CONFIG.fps
        max_lockdown = CONFIG.lock_down_speed * CONFIG.fps
        max_resets = CONFIG.lock_down_reset_limit

        flat_features.append(torch.tensor([observation.gravity_frames_remaining / max_gravity]))
        flat_features.append(torch.tensor([float(observation.lock_down_active)]))
        flat_features.append(torch.tensor([observation.lock_down_frames_remaining / max_lockdown]))
        flat_features.append(torch.tensor([observation.lock_down_resets_remaining / max_resets]))

        flat_tensor = torch.cat(flat_features).float()

        return flat_tensor

    def select_action(
        self,
        spatial_tensor: torch.Tensor,
        flat_tensor: torch.Tensor,
        action_mask_tensor: torch.Tensor,
        epsilon: float,
    ) -> Action:
        if random.random() < epsilon:  # exploration
            actions = [
                PLAYER_ACTION_SPACE[i] for i, valid in enumerate(action_mask_tensor) if valid
            ]
            if actions:  # theoretically always True; at the very least, hard drop is available
                return random.choice(actions)

        with torch.no_grad():
            # force the tensors to be batched
            spatial_tensor = spatial_tensor.to(self.device).unsqueeze(0)
            flat_tensor = flat_tensor.to(self.device).unsqueeze(0)

            q_values = self.model(spatial_tensor, flat_tensor)
            action_mask_tensor = action_mask_tensor.to(self.device).unsqueeze(0)
            masked_q_values = q_values.masked_fill(~action_mask_tensor, -1e9)

            return PLAYER_ACTION_SPACE[torch.argmax(masked_q_values, dim=1).item()]

    def train_step(self, batch_size: int) -> float | None:
        if len(self.replay_buffer) < batch_size:
            return None

        batch = self.replay_buffer.sample(batch_size)
        spatial_tensors = batch.spatial_tensors.to(self.device)
        flat_tensors = batch.flat_tensors.to(self.device)
        actions = batch.actions.to(self.device)
        rewards = batch.rewards.to(self.device)
        terminated_flags = batch.terminated_flags.to(self.device)
        next_spatial_tensors = batch.next_spatial_tensors.to(self.device)
        next_flat_tensors = batch.next_flat_tensors.to(self.device)
        next_action_masks = batch.next_action_masks.to(self.device)

        q_values = self.model(spatial_tensors, flat_tensors)
        current_q_values = q_values.gather(dim=1, index=actions.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_online_q_values = self.model(next_spatial_tensors, next_flat_tensors)
            masked_next_online_q_values = next_online_q_values.masked_fill(~next_action_masks, -1e9)
            next_actions = torch.argmax(masked_next_online_q_values, dim=1, keepdim=True)

            next_target_q_values = self.target_model(next_spatial_tensors, next_flat_tensors)
            max_next_q_values = next_target_q_values.gather(dim=1, index=next_actions).squeeze(1)

            target_q = rewards + (self.gamma * max_next_q_values * (1.0 - terminated_flags))

        loss = F.smooth_l1_loss(current_q_values, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.steps += 1
        if self.steps % self.target_update_frequency == 0:
            self.target_model.load_state_dict(self.model.state_dict())

        return loss.item()

    def save_checkpoint(self, filepath: str) -> None:
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "target_model_state_dict": self.target_model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "steps": self.steps,
        }
        torch.save(checkpoint, filepath)
        print(f"Checkpoint saved to {filepath}!")

    def load_checkpoint(self, filepath: str) -> None:
        if not os.path.exists(filepath):
            print(f"No checkpoint found at {filepath}. Starting from scratch.")
            return

        checkpoint = torch.load(filepath, map_location=self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.target_model.load_state_dict(checkpoint["target_model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.steps = checkpoint["steps"]

        print(f"Successfully loaded checkpoint from {filepath}. Resuming from step {self.steps}!")


class Trainer:
    def __init__(
        self,
        agent: DQNAgent,
        max_episodes: int = 1000,
        batch_size: int = 256,
        seed: int | None = None,
    ):
        self.seed = seed
        self.agent = agent
        self.max_episodes = max_episodes
        self.batch_size = batch_size
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01
        self.save_frequency = 100

    def train(self):
        for episode in range(self.max_episodes):
            engine = Engine(self.seed)

            observation = engine.build_observation()
            spatial = self.agent.tensorize_spatial_features(observation)
            flat = self.agent.tensorize_flat_features(observation)
            action_mask = torch.tensor(observation.action_mask, dtype=torch.bool)

            episode_losses = []
            if episode > 0 and episode % 100 == 0:
                renderer = Renderer(engine=engine)
            else:
                renderer = None

            while engine.running:
                if renderer is not None:
                    renderer.render()

                action = self.agent.select_action(spatial, flat, action_mask, self.epsilon)

                engine.process_frame([action])

                next_observation = engine.build_observation()
                next_spatial = self.agent.tensorize_spatial_features(next_observation)
                next_flat = self.agent.tensorize_flat_features(next_observation)
                next_action_mask = torch.tensor(next_observation.action_mask, dtype=torch.bool)

                self.agent.replay_buffer.push(
                    spatial=spatial,
                    flat=flat,
                    action=action,
                    reward=self.compute_reward(observation, next_observation),
                    terminated=next_observation.run_outcome is not None,
                    next_spatial=next_spatial,
                    next_flat=next_flat,
                    next_action_mask=next_action_mask,
                )

                spatial, flat, action_mask, observation = (
                    next_spatial,
                    next_flat,
                    next_action_mask,
                    next_observation,
                )

                loss = self.agent.train_step(self.batch_size)
                if loss is not None:
                    episode_losses.append(loss)

            average_loss = sum(episode_losses) / len(episode_losses) if episode_losses else 0
            print(
                f"""
                Episode: {episode}
                    Outcome: {observation.run_outcome.name}
                    Lines Cleared: {observation.lines_cleared}
                    Epsilon: {self.epsilon}
                    Average Loss: {average_loss:.4f}
                """
            )

            if episode > 0 and episode % self.save_frequency == 0:
                self.agent.save_checkpoint(DQN_PT_FILEPATH)

            self.epsilon = max(0.01, self.epsilon * 0.995)

    def compute_reward(self, observation1: Observation, observation2: Observation) -> float:
        wlc = 1  # weight for lines cleared
        whd = 3.5  # weight for holes delta
        victory_reward = 20
        defeat_penalty = 10

        lines_cleared = observation2.lines_cleared - observation1.lines_cleared
        holes1 = self.compute_holes(observation1.matrix)
        holes2 = self.compute_holes(observation2.matrix)
        holes_delta = holes2 - holes1

        base_reward = wlc * lines_cleared**2 - whd * holes_delta

        if observation2.run_outcome == RunOutcome.VICTORY:
            return base_reward + victory_reward
        if observation2.run_outcome == RunOutcome.DEFEAT:
            return base_reward - defeat_penalty

        return base_reward

    def compute_holes(self, matrix: Sequence[Sequence[Color | None]]) -> int:
        holes = 0

        height = len(matrix)
        width = len(matrix[0])
        for j in range(width):
            block_found = False
            for i in range(height - 1, -1, -1):
                if matrix[i][j] is not None:
                    block_found = True
                elif block_found:
                    holes += 1

        return holes


if __name__ == "__main__":
    agent = DQNAgent()
    agent.load_checkpoint(DQN_PT_FILEPATH)
    trainer = Trainer(agent=agent)

    trainer.train()
