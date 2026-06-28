Implemented using the 2009 Tetris Design Guideline

Design Thoughts
- Action requesters and resolvers should be placed within the Game class as it requires access to Game 
internals and follow internal Game rules.

Tetromino
- Active or Inactive
- Coordinates
- Piece Enum

Control Interface
- Soft Drop
- Hard Drop
- Left
- Right
- Hold
- Rotate Piece CW
- Rotate Piece CCW

Keyboard Control
- Key Press
- Key Hold
    - Only relevant for Soft Drop or Left/Right Shift; after a delay, ...

Action Queue
- Calls to exposed controls adds actions to the queue.
- After every fixed time interval, add a gravity action to the queue.
- On active piece becoming in active, add a hook to the queue.
    - Check if there are lines to clear, and if so, clear lines.
    - Set the next piece in line to be the new active piece.

Rules
- Spawning
    - 3x2 pieces spwan on rows 21/22 and span from columns 4 to 6
    - I piece spawns on row 21 and spans from 4 to 7
    - O piece spawns on rows 21/22 and spans from columns 5 to 6
- Lock Delay
    - Once a piece becomes grounded, i.e. meaning it cannot move one row downward,
    a timer starts; lock delay is about 0.5 seconds.
    - The timer is reset upon a successful shift or rotation; however, there is a
    cap on the number of resets, usually about 15.
- Piece Generation
    - A sequence of one of each piece is permuted. Every time a tetrimino starts its
    fall in th Matrix, the piece at the start of the sequence is added to the queue.
- Saving
    - Once a piece is saved, the new active piece cannot be switched out.
- Super Rotation
    - The Super Rotation System is an expanded rotation system that allows more flexibility and freedom of movement. It is designed to be intuitive.
    - If there is an obstruction, the game will attempt to shift the piece away from the obstruction.

TODO
- Color
    - O (Yellow), I (Blue), T (Purple), L (Orange), J (Dark Blue), S (Green), Z (Red)
