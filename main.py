from engine import Engine
from input import PygameInputManager
from render import Renderer
from shared import RunOutcome

if __name__ == "__main__":
    engine = Engine()
    renderer = Renderer(engine=engine)
    input_manager = PygameInputManager()

    while engine.running:
        renderer.render()
        actions = input_manager.poll()
        engine.process_frame(actions)

    if engine.run_outcome is None:
        raise RuntimeError("Engine has stopped running without a definitive RunOutcome.")

    match engine.run_outcome:
        case RunOutcome.VICTORY:
            print("VICTORY")
        case RunOutcome.DEFEAT:
            print("DEFEAT")
