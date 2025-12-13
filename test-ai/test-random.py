import random
import time

# Read game parameters: WIDTH HEIGHT NB_PLAYERS PLAYER_ID
W, H, N, S = map(int, input().split())

player = 0
while True:
    player = player % N + 1
    time.sleep(0.08)
    
    if player == S:
        # Our turn: output random x and rotation
        x = random.randrange(0, W)
        rotation = random.randrange(0, 4)
        print(f"{x} {rotation}")
    else:
        # Opponent's turn: read their move
        input()

