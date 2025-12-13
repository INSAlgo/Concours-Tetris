import random

# Read initial game parameters
W, H, N, S = map(int, input().split())

# Tetris pieces definitions with rotations
PIECES = {
    'I': [[(0, 0), (1, 0), (2, 0), (3, 0)]],
    'O': [[(0, 0), (1, 0), (0, 1), (1, 1)]],
    'T': [[(1, 0), (0, 1), (1, 1), (2, 1)]],
    'S': [[(1, 0), (2, 0), (0, 1), (1, 1)]],
    'Z': [[(0, 0), (1, 0), (1, 1), (2, 1)]],
    'J': [[(0, 0), (0, 1), (1, 1), (2, 1)]],
    'L': [[(2, 0), (0, 1), (1, 1), (2, 1)]],
}

def generate_rotations():
    """Generate all 4 rotations for each piece"""
    rotations = {}
    for name, shapes in PIECES.items():
        if name == 'O':
            rotations[name] = shapes * 4
        else:
            all_rots = []
            base = shapes[0]
            for _ in range(4):
                all_rots.append(base)
                # Rotate 90 degrees: (x, y) -> (y, -x)
                base = [(y, -x) for x, y in base]
                # Normalize
                min_x = min(x for x, y in base)
                min_y = min(y for x, y in base)
                base = [(x - min_x, y - min_y) for x, y in base]
            rotations[name] = all_rots
    return rotations

PIECE_ROTATIONS = generate_rotations()
PIECE_NAMES = list(PIECES.keys())

def get_piece_shape(piece_name, rotation):
    """Get shape of piece with rotation"""
    return PIECE_ROTATIONS[piece_name][rotation % 4]

def is_valid_placement(board, piece_name, x, rotation):
    """Check if piece can be placed at position"""
    shape = get_piece_shape(piece_name, x)
    
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

def find_valid_moves(board, piece_name):
    """Find all valid moves for current piece"""
    valid_moves = []
    for x in range(W):
        for rotation in range(4):
            if is_valid_placement(board, piece_name, x, rotation):
                valid_moves.append((x, rotation))
    return valid_moves

def strategy(board, current_piece):
    """
    Main strategy function - implement your AI logic here!
    
    Args:
        board: 2D list representing the board state
        current_piece: Name of the current piece ('I', 'O', 'T', 'S', 'Z', 'J', 'L')
    
    Returns:
        (x, rotation): The column and rotation to place the piece
    """
    # Simple strategy: find all valid moves and pick one randomly
    valid_moves = find_valid_moves(board, current_piece)
    
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
    # Initialize boards for all players
    boards = [[[0 for _ in range(H)] for _ in range(W)] for _ in range(N)]
    
    # Track current pieces (we'll guess based on moves)
    current_pieces = [random.choice(PIECE_NAMES) for _ in range(N)]
    
    player = 0
    
    while True:
        player = player % N + 1
        
        # Our turn
        if player == S:
            x, rotation = strategy(boards[S - 1], current_pieces[S - 1])
            print(f"> Playing {current_pieces[S - 1]} at x={x} rotation={rotation}")  # Debug
            print(f"{x} {rotation}")
            
            # Update our board (simplified - doesn't handle line clearing)
            # In a real implementation, you'd want to track line clears
            current_pieces[S - 1] = random.choice(PIECE_NAMES)
        
        # Opponent's turn
        else:
            move = input().strip()
            parts = move.split()
            
            if len(parts) == 2:
                x, rotation = int(parts[0]), int(parts[1])
                
                # Check for elimination
                if x == -1 and rotation == -1:
                    print(f"> Player {player} eliminated")
                else:
                    # Update opponent board (simplified)
                    current_pieces[player - 1] = random.choice(PIECE_NAMES)

if __name__ == "__main__":
    main()

