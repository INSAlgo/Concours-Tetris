import sys

# Read game parameters: WIDTH HEIGHT
W, H = map(int, input().split())

x = 0
rotation = 0

while True:
    try:
        # Receive the current piece name
        piece_name = input().strip()
    except EOFError:
        break
    
    # Output current position and rotation, then cycle
    print(f"{x} {rotation}")
    sys.stdout.flush()
    
    rotation = (rotation + 1) % 4
    if rotation == 0:
        x = (x + 1) % W


