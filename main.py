from engine import Engine
from input import PygameInputManager
from render import Renderer

if __name__ == "__main__":
    engine = Engine()
    renderer = Renderer(engine=engine)
    input_manager = PygameInputManager()

    while engine.running:
        renderer.render()
        actions = input_manager.poll()
        engine.process_frame(actions)
