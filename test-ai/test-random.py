import random
import sys

# Read game parameters: WIDTH HEIGHT
W, H = map(int, input().split())

while True:
    try:
        # Receive the current piece name
        piece_name = input().strip()
    except EOFError:
        break
    
    # Output random x and rotation
    x = random.randrange(0, W)
    rotation = random.randrange(0, 4)
    print(f"{x} {rotation}")
    sys.stdout.flush()


