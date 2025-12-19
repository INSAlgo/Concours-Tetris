import random
import sys

# Read initial game parameters: WIDTH HEIGHT
W, H = map(int, input().split())

# Read number of pieces
num_pieces = int(input())

# Read all pieces and store in PIECES dict
PIECES = {}
for _ in range(num_pieces):
    line = input().strip()
    parts = line.split()
    name = parts[0]
    shape = [tuple(map(int, coord.split(','))) for coord in parts[1:]]
    PIECES[name] = shape

def generate_rotations(shape):
    """Generate all 4 rotations for a given shape"""
    all_rots = []
    base = shape
    for _ in range(4):
        all_rots.append(base)
        # Rotate 90 degrees: (x, y) -> (y, -x)
        base = [(y, -x) for x, y in base]
        # Normalize
        min_x = min(x for x, y in base)
        min_y = min(y for x, y in base)
        base = [(x - min_x, y - min_y) for x, y in base]
    return all_rots

def get_piece_shape(rotations, rotation):
    """Get shape of piece with rotation"""
    return rotations[rotation % 4]

def is_valid_placement(board, shape, x):
    """Check if piece can be placed at position"""
    for dx, dy in shape:
        px = x + dx
        if px < 0 or px >= W:
            return False
        
        py = H - 1
        while py > 0 and board[px][py] != 0:
            py -= 1
        
        landing_y = py - dy
        if landing_y < 0 or landing_y >= H:
            return False
        if board[px][landing_y] != 0:
            return False
    
    return True

def find_valid_moves(board, rotations):
    """Find all valid moves for current piece"""
    valid_moves = []
    for x in range(W):
        for rotation in range(4):
            if is_valid_placement(board, rotations[rotation], x):
                valid_moves.append((x, rotation))
    return valid_moves

def strategy(board, rotations):
    """
    Main strategy function - implement your AI logic here!
    
    Args:
        board: 2D list representing the board state
        rotations: list of 4 shapes for the piece rotations
    
    Returns:
        (x, rotation): The column and rotation to place the piece
    """
    # Simple strategy: find all valid moves and pick one randomly
    valid_moves = find_valid_moves(board, rotations)
    
    if not valid_moves:
        # No valid moves (shouldn't happen in normal gameplay)
        return 0, 0
    
    # TODO: Implement smarter strategy here!
    # Ideas:
    # - Minimize board height
    # - Avoid creating holes
    # - Try to clear lines
    # - Look ahead to future pieces
    
    return random.choice(valid_moves)

def main():
    # Initialize our board
    board = [[0 for _ in range(H)] for _ in range(W)]
    
    while True:
        # Receive the current piece name
        try:
            piece_name = input().strip()
            shape = PIECES[piece_name]
        except EOFError:
            break

        # Generate rotations for this shape
        rotations = generate_rotations(shape)
        
        # Calculate the best move
        x, rotation = strategy(board, rotations)
        
        # Debug output
        print(f"> Playing {piece_name} at x={x} rotation={rotation}", file=sys.stderr)
        
        # Output the move
        print(f"{x} {rotation}")
        sys.stdout.flush()
        
        # Update our internal board (simplified - doesn't handle line clearing perfectly)
        # In a real implementation, you'd want to simulate the exact piece placement

if __name__ == "__main__":
    main()