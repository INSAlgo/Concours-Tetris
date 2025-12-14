# Tetris Coding Contest

This is a Tetris game module for the Discord bot Dijkstra-Chan, designed for AI bot coding contests!

## Game Description

This is a **solo scoring game** where each AI plays independently to achieve the highest score possible. All AIs receive the same predetermined sequence of pieces (using a fixed random seed), and rankings are based on the final score achieved.

The classic Tetris rules apply with the standard 7 tetrominoes (I, O, T, S, Z, J, L pieces).

## Rules

1. **Board**: Each player has a 10x20 board (width x height)
2. **Pieces**: The game uses the 7 standard tetrominoes (I, O, T, S, Z, J, L)
3. **Piece Sequence**: All players receive the **same sequence** of pieces (deterministic seed)
4. **Moves**: On each turn, players must place their current piece by specifying:
   - Column position (x: 0-9)
   - Rotation (0-3, representing 0°, 90°, 180°, 270°)
5. **Scoring**:
   - Each line cleared: +100 points
   - Each piece placed: +1 point
6. **Line Clearing**: When a horizontal line is completely filled, it is cleared and all lines above drop down
7. **Game Over**: Game ends when the player cannot place their current piece on the board
8. **Ranking**: Players are ranked by their final score (highest wins)

## Input/Output Protocol

### Game Start
At the beginning, AIs receive: `WIDTH HEIGHT`
- WIDTH: Board width (10)
- HEIGHT: Board height (20)

### Each Turn
The AI receives the current piece name: `PIECE_NAME`
- PIECE_NAME: One of: I, O, T, S, Z, J, L

AIs must output: `X ROTATION`
- X: Column where the piece should drop (0-9)
- ROTATION: Number of 90° rotations (0-3)

## Making Your AI

Use the Python template in `test-ai/template.py` as a starting point for your bot!

The template includes:
- Board state tracking
- Piece definitions and rotations
- Helper functions for valid move checking