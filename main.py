import pygame

from engine import Engine
from input import PygameInputManager
from render import Renderer
from shared import RunOutcome

if __name__ == "__main__":
    pygame.init()
    clock = pygame.time.Clock()
    fps = 60  # frames per second

    gravity_speed = 0.8  # time in seconds it takes for the active piece to fall by one line
    gravity_frame_rate = round(gravity_speed * fps)

    lock_down_speed = 0.5  # time in seconds it takes for the active piece to lock on its surface
    lock_down_frame_rate = round(lock_down_speed * fps)
    lock_down_reset_limit = 15  # number of resets allowed before immediate lock

    engine = Engine(
        gravity_frame_rate=gravity_frame_rate,
        lock_down_frame_rate=lock_down_frame_rate,
        lock_down_reset_limit=lock_down_reset_limit,
    )
    renderer = Renderer(engine=engine)
    input_manager = PygameInputManager()

    while engine.running:
        renderer.render()
        actions = input_manager.poll()
        engine.process_frame(actions)

        clock.tick(fps)

    match engine.run_outcome:
        case RunOutcome.VICTORY:
            print("VICTORY")
        case RunOutcome.DEFEAT:
            print("DEFEAT")
