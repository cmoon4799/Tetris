Implemented using the 2009 Tetris Design Guideline

## TODO

### High Priority
- Add a finite lock down reset cap.
- Add tests for spawn validity and collision constraints.
- Inject seeded RNG into piece generation so identical seeds and actions reproduce identical runs.

### Low Priority
- Improve matrix clearing performance.
- Stop drift of gameplay dimensions across classes.
- Remove direct renderer access to mutable engine internals.
- Refactor `piece.py` toward data driven tables to reduce duplicated logic.