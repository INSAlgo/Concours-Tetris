import random
import sys

# Read game parameters: WIDTH HEIGHT
W, H = map(int, input().split())

# Read number of pieces
N = int(input())

# Discard the shape lines
for _ in range(N):
    input()

while True:
    try:
        # Receive the current piece name
        line = input().strip()
        piece_name = line.split()[0]
    except EOFError:
        break
    
    # Output random x and rotation
    x = random.randrange(0, W)
    rotation = random.randrange(0, 4)
    print(f"{x} {rotation}")
    sys.stdout.flush()
