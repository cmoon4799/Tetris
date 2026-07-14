import pygame

from engine import Engine
from input import PygameInputManager
from render import Renderer
from shared import CONFIG, RunOutcome

if __name__ == "__main__":
    pygame.init()
    clock = pygame.time.Clock()

    engine = Engine()
    renderer = Renderer()
    input_manager = PygameInputManager()

    while engine.running:
        observation = engine.build_observation()
        renderer.render(observation)
        actions = input_manager.poll()
        engine.process_frame(actions)

        clock.tick(CONFIG.fps)

    match engine.run_outcome:
        case RunOutcome.VICTORY:
            print("VICTORY")
        case RunOutcome.DEFEAT:
            print("DEFEAT")
