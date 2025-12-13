import time

# Read game parameters: WIDTH HEIGHT NB_PLAYERS PLAYER_ID
W, H, N, S = map(int, input().split())

p = 0
x = 0
rotation = 0

while True:
    time.sleep(0.08)
    p = p % N + 1
    
    if p == S:
        # Our turn: cycle through positions and rotations
        print(f"{x} {rotation}")
        rotation = (rotation + 1) % 4
        if rotation == 0:
            x = (x + 1) % W
    else:
        # Opponent's turn: read their move
        input()

