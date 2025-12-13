#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Any
from io import StringIO
from pathlib import Path
import argparse, asyncio, os, re, sys

# Tetris game constants
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# Tetris pieces definitions (each piece defined by its coordinates relative to origin)
PIECES = {
    'I': [[(0, 0), (1, 0), (2, 0), (3, 0)]],  # I piece (rotations will be computed)
    'O': [[(0, 0), (1, 0), (0, 1), (1, 1)]],  # O piece (no rotation needed)
    'T': [[(1, 0), (0, 1), (1, 1), (2, 1)]],  # T piece
    'S': [[(1, 0), (2, 0), (0, 1), (1, 1)]],  # S piece
    'Z': [[(0, 0), (1, 0), (1, 1), (2, 1)]],  # Z piece
    'J': [[(0, 0), (0, 1), (1, 1), (2, 1)]],  # J piece
    'L': [[(2, 0), (0, 1), (1, 1), (2, 1)]],  # L piece
}

# Generate all rotations for pieces
def generate_rotations():
    rotations = {}
    for name, shapes in PIECES.items():
        if name == 'O':  # O piece doesn't need rotation
            rotations[name] = shapes * 4
        else:
            all_rots = []
            base = shapes[0]
            for _ in range(4):
                all_rots.append(base)
                # Rotate 90 degrees clockwise: (x, y) -> (y, -x)
                base = [(y, -x) for x, y in base]
                # Normalize to have min coordinates at 0
                min_x = min(x for x, y in base)
                min_y = min(y for x, y in base)
                base = [(x - min_x, y - min_y) for x, y in base]
            rotations[name] = all_rots
    return rotations

PIECE_ROTATIONS = generate_rotations()
PIECE_NAMES = list(PIECES.keys())

# Default Timeouts :
TIMEOUT_LENGTH = 0.1
DISCORD_TIMEOUT = 60

# Usefull emojis :
EMOJI_NUMBERS = ('0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')
EMOJI_COLORS = ('🟠', '🔴', '🟡', '🟢', '🔵', '🟣', '🟤',  '⚪️', '⚫️')

# what is the type of a valid move or a valid input (when it has a specific format) to use in typing
ValidMove = tuple[int, int]  # (x, rotation)
ValidInput = str  # "x rotation"

# input and output functions types
InputFunction = Callable[..., str]      # function asking a discord player to make a move, returns the discord answer
OutputFunction = Callable[[str], None]  # function called when an AI wants to "talk" to discord, the argument being the message


class Player(ABC):

    ofunc = None

    def __init__(self, no: int, name: str = None, **kwargs):
        """The abstract Player constructor

        Args:
            no (int): player number/id
            name (str, optional): The player name. Defaults to None.
        """
        # You can add any number of kwargs you want that will be passed in the discord command for your game
        
        self.no = no

        # These can be altered to give personnality to your game display (with emojis for example)
        self.icon = self.no
        self.name = name
        self.rendered_name = None
        
        # Tetris-specific attributes
        self.board = [[0 for _ in range(BOARD_HEIGHT)] for _ in range(BOARD_WIDTH)]
        self.current_piece = None
        self.current_piece_name = None

    @abstractmethod
    async def start_game(self):
        self.alive = True

    @abstractmethod
    async def lose_game(self):
        await Player.print(f"{self} is eliminated")

    @abstractmethod
    async def ask_move(self, **kwargs) -> tuple[ValidMove, None] | tuple[None | str]:
        pass

    @abstractmethod
    async def tell_move(self, move: ValidInput):
        pass

    async def tell_other_players(self, players: list[Player], move: ValidInput):
        for other_player in players:
            if self != other_player and other_player.alive:
                await other_player.tell_move(move)

    @staticmethod
    async def sanithize(userInput: str, **kwargs) -> tuple[ValidMove, None] | tuple[None, str]:
        """Parses raw user input text into an error message or a valid move

        Args:
            userInput (`str`): the raw user input text

        Returns:
            `tuple[ValidMove, None] | tuple[None | str]`
        """
        # You can add any number of kwargs you want
        # that will be necessary to parse the input
        # (like the game board for example),
        # just remember to pass them when calling this method.
        
        if userInput == "stop":
            # When a human player (or an AI, who knows) wants to abandon.
            return None, "user interrupt"
        
        # Parse Tetris move: "x rotation"
        try:
            parts = userInput.strip().split()
            if len(parts) != 2:
                return None, "invalid format (expected: x rotation)"
            
            x = int(parts[0])
            rotation = int(parts[1])
            
            # Validate ranges
            if x < 0 or x >= BOARD_WIDTH:
                return None, f"x must be between 0 and {BOARD_WIDTH - 1}"
            
            if rotation < 0 or rotation > 3:
                return None, "rotation must be between 0 and 3"
            
            # Get current piece and board from kwargs
            current_piece = kwargs.get('current_piece')
            board = kwargs.get('board')
            
            if current_piece is None or board is None:
                return None, "missing game state"
            
            # Check if the move is valid
            if not is_valid_placement(board, current_piece, x, rotation):
                return None, "invalid placement"
            
            processed_input: ValidMove = (x, rotation)
            return processed_input, None
            
        except ValueError:
            return None, "x and rotation must be integers"

    @staticmethod
    async def print(output: StringIO | str, send_discord=True, end="\n"):
        if isinstance(output, StringIO):
            text = output.getvalue()
            output.close()
        else:
            text = output + end
        print(text, end="")
        if Player.ofunc and send_discord:
            await Player.ofunc(text)

    def __str__(self):
        return self.rendered_name


class Human(Player):

    def __init__(self, no: int, name: str = None, ifunc: InputFunction = None, **kwargs):
        """The human player constructor
        Let ifunc be None to get terminal input (for a local game)

        Args:
            no (`int`): player number/id
            name (`str`, optional): The player name. Defaults to None.
            ifunc (`InputFunction`, optional): The input function. Defaults to None.
        """
        super().__init__(no, name, **kwargs)
        self.ifunc = ifunc

        # Here you can personnalize human players name specifically
        self.rendered_name = f"{self.name} {self.icon}" if name else f"Player {self.icon}"

    async def start_game(self):
        await super().start_game()

    async def lose_game(self):
        await super().lose_game()
    
    # Don't forget to replace <**kwargs> with the arguments necessary for parsing the input
    async def ask_move(self, **kwargs):
        await super().ask_move(**kwargs)
        # You can customize your message asking for a move here :
        await Player.print(f"Awaiting {self}'s move (x rotation): ", end="")
        try:
            user_input = await self.input()
        except asyncio.TimeoutError:
            await Player.print(f"User did not respond in time (over {DISCORD_TIMEOUT}s)")
            return None, "timeout"
        # This is where the kwargs are usefull :
        return await Human.sanithize(user_input, **kwargs)

    async def tell_move(self, move: ValidInput):
        return super().tell_move(move)

    async def input(self):
        if self.ifunc:
            user_input = await asyncio.wait_for(self.ifunc(self.name), timeout=DISCORD_TIMEOUT)
            await Player.print(user_input, send_discord=False)
            return user_input
        else:
            return input()

class AI(Player):

    @staticmethod
    def prepare_command(progPath: str | Path):
        """Prepares the command to start the AI

        Args:
            progPath (`str` | `Path`): the path to the program

        Raises:
            Exception: File not found error

        Returns:
            `str`: the command to start the AI
        """
        path = Path(progPath)
        if not path.is_file():
            raise FileNotFoundError(f"File {progPath} not found\n")

        match path.suffix:
            case ".py":
                return f"python3 {progPath}"
            case ".js":
                return f"node {progPath}"
            case ".class":
                return f"java -cp {os.path.dirname(progPath)} {os.path.splitext(os.path.basename(progPath))[0]}"
            case _:
                return f"./{progPath}"

    def __init__(self, no: int, prog_path: str, discord: bool, **kwargs):
        """The AI player constructor

        Args:
            no (int): player number/id
            prog_path (str): AI's program path
            discord (bool): if it is instantiated through discord to associate the user tag
        """
        super().__init__(no, Path(prog_path).stem, **kwargs)
        self.prog_path = prog_path
        self.command = AI.prepare_command(self.prog_path)

        # Once again, you can personnalize how the AI player will be called during the game here
        if discord:
            # if it's through discord, self.name should be the discord user's ID
            self.rendered_name = f"<@{self.name}>'s AI {self.icon}"
        else:
            self.rendered_name = f"AI {self.icon} ({self.name})"
    
    async def drain(self):
        if self.prog.stdin.transport._conn_lost:
            self.prog.stdin.close()
            self.prog.stdin = asyncio.subprocess.PIPE
        await self.prog.stdin.drain()

    async def start_game(self, **kwargs):
        # You can specify here what parameters are required to start a game for an AI player.
        # For example : board size, number of players...
        await super().start_game()
        self.prog = await asyncio.create_subprocess_shell(
            AI.prepare_command(self.prog_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        if self.prog.stdin:
            # Send initial game parameters: WIDTH HEIGHT NB_PLAYERS PLAYER_ID
            nb_players = kwargs.get('nb_players', 2)
            self.prog.stdin.write(f"{BOARD_WIDTH} {BOARD_HEIGHT} {nb_players} {self.no + 1}\n".encode())
            await self.drain()

    async def lose_game(self):
        await super().lose_game()

    # Don't forget to replace <**kwargs> with the arguments necessary for parsing the input
    async def ask_move(self, debug: bool = True, **kwargs) -> tuple[tuple[int, int] | None, str | None]:
        await super().ask_move(**kwargs)
        try:
            while True:
                if not self.prog.stdout:
                    return None, "communication failed"
                progInput = await asyncio.wait_for(self.prog.stdout.readuntil(), TIMEOUT_LENGTH)

                if not isinstance(progInput, bytes):
                    continue
                progInput = progInput.decode().strip()

                if progInput.startswith("Traceback"):
                    output = StringIO()
                    if debug:
                        print(file=output)
                        print(progInput, file=output)
                        progInput = self.prog.stdout.read()
                        if isinstance(progInput, bytes):
                            print(progInput.decode(), file=output)
                        await Player.print(output)
                    return None, "error"
                
                if progInput.startswith(">"):
                    # Any bot can write lines starting with ">" to debug in local.
                    # It is recommended to remove any debug before playing
                    # against other players to avoid reverse engineering!
                    if debug:
                        await Player.print(f"{self} {progInput}")
                else:
                    break

            # You can customize the message all bots will send to announce their moves here :
            await Player.print(f"{self}'s move : {progInput}")

        except (asyncio.TimeoutError, asyncio.exceptions.IncompleteReadError):
            await Player.print(f"AI did not respond in time (over {TIMEOUT_LENGTH}s)")
            return None, "timeout"
        
        # This is where the kwargs are usefull :
        return await AI.sanithize(progInput, **kwargs)

    async def tell_move(self, move: ValidInput):
        if self.prog.stdin:
            # The AIs should keep track of who's playing themselves.
            self.prog.stdin.write(f"{move}\n".encode())
            await self.drain()

    async def stop_game(self):
        try:
            self.prog.terminate()
            await self.prog.wait()
        except ProcessLookupError:
            pass


# Here is a place to define functions useful for your game, typically:
#  - checking for a win or a draw,
#  - drawing the grid in terminal or in discord
#  - processing a move
#  - ...

def get_piece_shape(piece_name: str, rotation: int) -> list[tuple[int, int]]:
    """Get the shape of a piece with a specific rotation"""
    return PIECE_ROTATIONS[piece_name][rotation % 4]


def is_valid_placement(board: list[list[int]], piece_name: str, x: int, rotation: int) -> bool:
    """Check if a piece can be placed at position x with given rotation"""
    shape = get_piece_shape(piece_name, rotation)
    
    # Check each block of the piece
    for dx, dy in shape:
        px = x + dx
        py = BOARD_HEIGHT - 1  # Start from bottom
        
        # Check if piece fits horizontally
        if px < 0 or px >= BOARD_WIDTH:
            return False
        
        # Find where the piece would land
        while py >= 0:
            if board[px][py] != 0:
                py -= 1
            else:
                break
        
        # Check if piece goes above board
        if py < 0:
            return False
    
    # Find the minimum landing position for all blocks
    landing_positions = []
    for dx, dy in shape:
        px = x + dx
        py = BOARD_HEIGHT - 1
        
        # Find landing position for this block
        while py > 0 and board[px][py] != 0:
            py -= 1
        
        # The block will land at py + dy (offset from base)
        landing_y = py - dy
        if landing_y < 0:
            return False
        
        landing_positions.append((px, landing_y))
    
    # Check if all landing positions are valid
    for px, py in landing_positions:
        if py < 0 or py >= BOARD_HEIGHT:
            return False
        if board[px][py] != 0:
            return False
    
    return True


def place_piece(board: list[list[int]], piece_name: str, x: int, rotation: int, player_id: int) -> int:
    """Place a piece on the board and return number of lines cleared"""
    shape = get_piece_shape(piece_name, rotation)
    
    # Find landing position for each block
    placed_blocks = []
    for dx, dy in shape:
        px = x + dx
        py = BOARD_HEIGHT - 1
        
        # Find where this block lands
        while py > 0 and board[px][py] != 0:
            py -= 1
        
        # Place the block at its final position considering the shape offset
        final_y = py - dy
        placed_blocks.append((px, final_y))
    
    # Place all blocks
    for px, py in placed_blocks:
        board[px][py] = player_id
    
    # Clear lines
    lines_cleared = 0
    for y in range(BOARD_HEIGHT):
        if all(board[x][y] != 0 for x in range(BOARD_WIDTH)):
            # Clear this line
            lines_cleared += 1
            # Move everything down
            for yy in range(y, 0, -1):
                for x in range(BOARD_WIDTH):
                    board[x][yy] = board[x][yy - 1]
            # Clear top line
            for x in range(BOARD_WIDTH):
                board[x][0] = 0
    
    return lines_cleared


def render_board(board: list[list[int]], player_name: str) -> str:
    """Render a board as a string"""
    output = StringIO()
    print(f"\n{player_name}'s Board:", file=output)
    print("┌" + "─" * BOARD_WIDTH + "┐", file=output)
    
    for y in range(BOARD_HEIGHT):
        line = "│"
        for x in range(BOARD_WIDTH):
            if board[x][y] == 0:
                line += " "
            else:
                line += "█"
        line += "│"
        print(line, file=output)
    
    print("└" + "─" * BOARD_WIDTH + "┘", file=output)
    print(" " + "".join(str(i) for i in range(BOARD_WIDTH)), file=output)
    
    return output.getvalue()


def get_next_piece() -> str:
    """Get the next random piece"""
    import random
    return random.choice(PIECE_NAMES)



async def game(players: list[Human | AI], debug: bool, **kwargs) -> tuple[list[Human | AI], Human | AI | None, dict]:
    """The function handling all the game logic.
    Once again, you can add as many kwargs as you need.
    Note that you can return anything you need that will be treated in `main()` after the specified args.

    Args:
        players (`list[Human | AI]`): The list of players
        debug (`bool`): _description_

    Returns:
        `tuple[list[Human | AI], Human | AI | None, dict, ...]`: A whole bunch of game data to help display and judge the result
    """

    nb_players = len(players)
    alive_players = nb_players
    errors = {} # This is for logging and debugginf purposes
    starters = (player.start_game(nb_players=nb_players, **kwargs) for player in players)
    await asyncio.gather(*starters)
    turn = 0
    winner = None

    # Initialize pieces for each player
    for player in players:
        player.current_piece_name = get_next_piece()

    # game loop
    while alive_players >= 2:
        i = turn % nb_players
        player = players[i]

        if not player.alive:
            # It is essential to notify of a player "death" so that AIs can skip their turn.
            # Replace `None` by a NORMALIZED simple value signifying an incorrect move. 
            await player.tell_other_players(players, "-1 -1")

        else:
            # Render the board for the player
            board_display = render_board(player.board, str(player))
            await Player.print(board_display)
            await Player.print(f"Current piece: {player.current_piece_name}")

            # player input
            user_input, error = None, None
            while not user_input:
                # Pass current piece and board for validation
                user_input, error = await player.ask_move(
                    debug=debug, 
                    current_piece=player.current_piece_name,
                    board=player.board
                )
                if isinstance(player, AI) or error in ("user interrupt", "timeout"):
                    break

            # saving eventual error
            if not user_input:
                await player.lose_game()
                errors[player] = error
                player.alive = False
                alive_players -= 1
                # It is essential to notify of a player "death" so that AIs can skip their turn.
                await player.tell_other_players(players, "-1 -1")

            else:
                # Apply the move
                x, rotation = user_input
                lines_cleared = place_piece(player.board, player.current_piece_name, x, rotation, player.no + 1)
                
                if lines_cleared > 0:
                    await Player.print(f"{player} cleared {lines_cleared} line(s)!")
                
                # Notify other players of the move
                move_str = f"{x} {rotation}"
                await player.tell_other_players(players, move_str)
                
                # Get next piece
                player.current_piece_name = get_next_piece()
                
                # Check if player can place the next piece
                can_place = any(
                    is_valid_placement(player.board, player.current_piece_name, x, rot)
                    for x in range(BOARD_WIDTH)
                    for rot in range(4)
                )
                
                if not can_place:
                    await player.lose_game()
                    errors[player] = "board full"
                    player.alive = False
                    alive_players -= 1
                    await player.tell_other_players(players, "-1 -1")
        
        turn += 1

    if alive_players == 1:
        # nobreak
        winner = [player for player in players if player.alive][0]
    
    enders = (player.stop_game() for player in players if isinstance(player, AI))
    await asyncio.gather(*enders)

    # You can add extra returned stuff here, like the final board and other stuff
    return players, winner, errors


async def main(raw_args: str = None, ifunc: InputFunction = None, ofunc: OutputFunction = None, discord=False):
    # these arguments should not be messed with because that's how the discord bot works

    parser = argparse.ArgumentParser()
    parser.add_argument("prog", nargs="*", \
            help="AI program to play the game ('user' to play yourself)")
    parser.add_argument("-p", "--players", type=int, default=2, metavar="NB_PLAYERS", \
            help="number of players (if more players than programs are provided, the other ones will be filled as real players)")
    parser.add_argument("-s", "--silent", action="store_true", \
            help="only show the result of the game")
    parser.add_argument("-n", "--nodebug", action="store_true", \
            help="do not print the debug output of the programs")
    # Add here any extra argument you need to define the game (board size for example)

    args = parser.parse_args(raw_args)

    Player.ofunc = ofunc
    players = []
    ai_only = True
    pattern = re.compile(r"^\<\@[0-9]{18}\>$")
    for i, name in enumerate(args.prog):
        if name == "user":
            players.append(Human(i))                # Add extra arguments extracted from `args`
            ai_only = False
        elif pattern.match(name):
            players.append(Human(i, name, ifunc))   # Add extra arguments extracted from `args`
            ai_only = False
        else:
            players.append(AI(i, name, discord))    # Add extra arguments extracted from `args`
    while len(players) < args.players:
        players.append(Human(len(players)))         # Add extra arguments extracted from `args`
        ai_only = False

    origin_stdout = sys.stdout
    if args.silent:
        if not ai_only:
            output = StringIO("Game cannot be silent since humans are playing")
            tmp = output.getvalue()
            await Player.print(output)
            raise Exception(tmp)
        if discord:
            Player.ofunc = None
        else:
            sys.stdout = open(os.devnull, "w")

    players, winner, errors = await game(players, not args.nodebug) # Add extra arguments extracted from `args`

    if args.silent:
        sys.stdout = origin_stdout
        Player.ofunc = ofunc
    else:
        # Display final boards
        for player in players:
            board_display = render_board(player.board, str(player))
            await Player.print(board_display)
    
    # Announce winner
    if winner:
        await Player.print(f"\n🎉 {winner} wins the game! 🎉")
    else:
        await Player.print("\n🤝 It's a draw!")

    return players, winner, errors  # this should not be messed with because that's how the discord bot works

if __name__ == "__main__":
    asyncio.run(main())

