# Tetris Coding Contest

This is a Tetris game module for the Discord bot Dijkstra-Chan, designed for AI bot coding contests!

## Game Description

Players compete in a battle Tetris game where they must survive the longest by clearing lines and avoiding their board filling up. The classic Tetris rules apply with the standard 7 tetrominoes (I, O, T, S, Z, J, L pieces).

## Rules

1. **Board**: Each player has their own 10x20 board (width x height)
2. **Pieces**: The game uses the 7 standard tetrominoes (I, O, T, S, Z, J, L)
3. **Moves**: On each turn, players must place their current piece by specifying:
   - Column position (x: 0-9)
   - Rotation (0-3, representing 0°, 90°, 180°, 270°)
4. **Line Clearing**: When a horizontal line is completely filled, it is cleared and all lines above drop down
5. **Game Over**: A player loses when they cannot place their current piece on the board
6. **Winner**: The last player remaining wins

## Input/Output Protocol

### Game Start
At the beginning, AIs receive: `WIDTH HEIGHT NB_PLAYERS PLAYER_ID`
- WIDTH: Board width (10)
- HEIGHT: Board height (20)
- NB_PLAYERS: Number of players in the game
- PLAYER_ID: Your player ID (1-indexed)

### Each Turn
AIs must output: `X ROTATION`
- X: Column where the piece should drop (0-9)
- ROTATION: Number of 90° rotations (0-3)

AIs receive opponents' moves: `X ROTATION` or `-1 -1` if a player is eliminated

## Making Your AI

Use the Python template in `test-ai/template.py` as a starting point for your bot!

The template includes:
- Board state tracking
- Piece definitions and rotations
- Helper functions for valid move checking