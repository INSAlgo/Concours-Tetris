#!/usr/bin/env python3

from __future__ import annotations
from abc import ABC, abstractmethod
import contextlib
import signal
from typing import Callable, Any
from io import StringIO
from pathlib import Path
import argparse, asyncio, os, platform, random, re, shutil, subprocess, sys

# Tetris game constants
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

EMOJIS = {
    'empty': '⬛',
    'I': '🟦',
    'O': '🟨',
    'T': '🟪',
    'S': '🟩',
    'Z': '🟥',
    'J': '⬜',
    'L': '🟧'
}

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
PIECE_VALUES = {name: i+1 for i, name in enumerate(PIECE_NAMES)}

# Default Timeouts :
TIMEOUT_LENGTH = 0.1
DISCORD_TIMEOUT = 60

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
        self.score = 0
        self.pieces_placed = 0

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
    async def sanitize(userInput: str, **kwargs) -> tuple[ValidMove, None] | tuple[None, str]:
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

    async def start_game(self, **_):
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
        return await Human.sanitize(user_input, **kwargs)

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
                command = f"{sys.executable} {progPath}"
            case ".js":
                command = f"node {progPath}"
            case ".class":
                command = f"java -cp {os.path.dirname(progPath)} {os.path.splitext(os.path.basename(progPath))[0]}"
            case _:
                if os.name == 'posix':
                    command = f"./{progPath}"
                else:
                    command = f"{progPath}"

        # Security enhancement: Use Firejail sandboxing if available and profile exists
        if platform.system() == 'Linux' and shutil.which('firejail') is not None and os.path.exists('tetris.profile'):
            command = f"firejail --profile=tetris.profile {command}"
            print(f'Running command with firejail!')

        print(f"Prepared command for {progPath}: {command}")
        return command

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
        print(f"Starting AI subprocess for {self.prog_path}")
        self.prog = await asyncio.create_subprocess_shell(
            AI.prepare_command(self.prog_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print(f"AI subprocess created: {self.prog}")

        if self.prog.stdin:
            # Send initial game parameters: WIDTH HEIGHT
            self.prog.stdin.write(f"{BOARD_WIDTH} {BOARD_HEIGHT}\n".encode())
            await self.drain()

    async def lose_game(self):
        await super().lose_game()

    # Don't forget to replace <**kwargs> with the arguments necessary for parsing the input
    async def ask_move(self, debug: bool = True, **kwargs) -> tuple[tuple[int, int] | None, str | None]:
        await super().ask_move(**kwargs)
        
        # Send the current piece name to the AI
        current_piece = kwargs.get('current_piece')
        if self.prog.stdin and current_piece:
            self.prog.stdin.write(f"{current_piece}\n".encode())
            await self.drain()
        
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
        return await AI.sanitize(progInput, **kwargs)

    async def tell_move(self, move: ValidInput):
        if self.prog.stdin:
            # The AIs should keep track of who's playing themselves.
            self.prog.stdin.write(f"{move}\n".encode())
            await self.drain()

    async def stop_game(self):
        if not self.prog:
            return
    
        if hasattr(self.prog, 'terminate') and callable(self.prog.terminate):
            with contextlib.suppress(ProcessLookupError):
                self.prog.terminate()
                try:
                    await asyncio.wait_for(self.prog.wait(), timeout=1)
                    return
                except asyncio.TimeoutError:
                    pass
    
        if hasattr(self.prog, 'kill') and callable(self.prog.kill):
            self.prog.kill()
            try:
                await asyncio.wait_for(self.prog.wait(), timeout=1)
                return
            except asyncio.TimeoutError:
                pass
    
        if hasattr(self.prog, 'pid') and self.prog.pid is not None:
            if os.name == 'posix':
                try:
                    os.killpg(os.getpgid(self.prog.pid), signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
            else:
                subprocess.run(['taskkill', '/PID', str(self.prog.pid), '/T', '/F'])
            try:
                await asyncio.wait_for(self.prog.wait(), timeout=1)
                return
            except asyncio.TimeoutError:
                pass
    
        raise Exception("Could not kill the AI process")


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
    
    # Check if piece fits horizontally
    for dx, dy in shape:
        px = x + dx
        if px < 0 or px >= BOARD_WIDTH:
            return False
    
    # Find the lowest position where the piece can be placed
    max_y = BOARD_HEIGHT
    for dx, dy in shape:
        px = x + dx
        # Find the highest occupied cell in this column
        for py in range(BOARD_HEIGHT):
            if board[px][py] != 0:
                max_y = min(max_y, py - dy - 1)
                break
        else:
            # Column is empty, piece can fall to bottom
            max_y = min(max_y, BOARD_HEIGHT - 1 - dy)
    
    # Check if all blocks of the piece can fit
    for dx, dy in shape:
        px = x + dx
        py = max_y + dy
        if py < 0 or py >= BOARD_HEIGHT:
            return False
        if board[px][py] != 0:
            return False
    
    return True


def place_piece(board: list[list[int]], piece_name: str, x: int, rotation: int) -> int:
    """Place a piece on the board and return number of lines cleared"""
    shape = get_piece_shape(piece_name, rotation)

    # Find the lowest position where the piece can be placed
    max_y = BOARD_HEIGHT
    for dx, dy in shape:
        px = x + dx
        # Find the highest occupied cell in this column
        for py in range(BOARD_HEIGHT):
            if board[px][py] != 0:
                max_y = min(max_y, py - dy - 1)
                break
        else:
            # Column is empty, piece can fall to bottom
            max_y = min(max_y, BOARD_HEIGHT - 1 - dy)

    # Place all blocks
    for dx, dy in shape:
        px = x + dx
        py = max_y + dy
        board[px][py] = PIECE_VALUES[piece_name]
    
    # Clear lines
    lines_cleared = 0
    y = 0
    while y < BOARD_HEIGHT:
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
            # Don't increment y, check the same line again
        else:
            y += 1
    
    return lines_cleared


def render_board(board: list[list[int]], player_name: str) -> str:
    """Render a board as a string"""
    output = StringIO()
    print(f"\n{player_name}'s Board:", file=output)
    print("┌" + "─" * BOARD_WIDTH * 2 + "┐", file=output)
    
    for y in range(BOARD_HEIGHT):
        line = "│"
        for x in range(BOARD_WIDTH):
            value = board[x][y]
            if value == 0:
                line += EMOJIS['empty']
            else:
                piece_name = PIECE_NAMES[value - 1]
                line += EMOJIS[piece_name]
        line += "│"
        print(line, file=output)
    
    print("└" + "─" * BOARD_WIDTH*2 + "┘", file=output)
    print(" " + "".join(str(i) for i in range(BOARD_WIDTH)), file=output)
    
    return output.getvalue()


def get_next_piece(rng: random.Random) -> str:
    """Get the next random piece using a seeded RNG"""
    return rng.choice(PIECE_NAMES)



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
    errors = {} # This is for logging and debugging purposes
    
    # Get seed from kwargs or use default
    seed = kwargs.get('seed', 42)
    
    # Start all players
    starters = (player.start_game(**kwargs) for player in players)
    await asyncio.gather(*starters)
    
    # Each player plays independently (solo mode)
    async def play_solo_game(player: Human | AI):
        """Each player plays their own independent game"""
        # Create seeded RNG for this player (all players get same sequence)
        rng = random.Random(seed)
        player.current_piece_name = get_next_piece(rng)
        
        while player.alive:
            # Render the board for the player
            board_display = render_board(player.board, str(player))
            await Player.print(board_display)
            await Player.print(f"Current piece: {player.current_piece_name}")
            await Player.print(f"Score: {player.score} | Pieces placed: {player.pieces_placed}")

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
            else:
                # Apply the move
                x, rotation = user_input
                lines_cleared = place_piece(player.board, player.current_piece_name, x, rotation)
                
                # Update score
                player.score += lines_cleared * 100  # 100 points per line
                player.score += 1  # 1 point per piece placed
                player.pieces_placed += 1
                
                if lines_cleared > 0:
                    await Player.print(f"{player} cleared {lines_cleared} line(s)! (+{lines_cleared * 100} points)")
                
                # Get next piece
                player.current_piece_name = get_next_piece(rng)
                
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
    
    # Run all players' games simultaneously
    await asyncio.gather(*[play_solo_game(player) for player in players])
    
    # Find winner (highest score)
    winner = max(players, key=lambda p: p.score) if players else None
    
    enders = (player.stop_game() for player in players if isinstance(player, AI))
    await asyncio.gather(*enders)

    # You can add extra returned stuff here, like the final board and other stuff
    return players, winner, errors


async def main(raw_args: str = None, ifunc: InputFunction = None, ofunc: OutputFunction = None, discord=False):
    # these arguments should not be messed with because that's how the discord bot works

    parser = argparse.ArgumentParser()
    parser.add_argument("prog", nargs="*", \
            help="AI program to play the game ('user' to play yourself)")
    parser.add_argument("-p", "--players", type=int, default=1, metavar="NB_PLAYERS", \
            help="number of players (all play independently with same piece sequence)")
    parser.add_argument("-s", "--silent", action="store_true", \
            help="only show the result of the game")
    parser.add_argument("-n", "--nodebug", action="store_true", \
            help="do not print the debug output of the programs")
    parser.add_argument("--seed", type=int, default=42, \
            help="random seed for piece sequence (default: 42)")
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

    players, winner, errors = await game(players, not args.nodebug, seed=args.seed) # Add extra arguments extracted from `args`

    if args.silent:
        sys.stdout = origin_stdout
        Player.ofunc = ofunc
    else:
        # Display final boards and scores
        await Player.print("\n=== FINAL RESULTS ===")
        for player in players:
            board_display = render_board(player.board, str(player))
            await Player.print(board_display)
            await Player.print(f"{player} - Final Score: {player.score} | Pieces Placed: {player.pieces_placed}")
    
    # Sort players by score for ranking
    sorted_players = sorted(players, key=lambda p: p.score, reverse=True)
    
    # Announce winner and rankings
    if winner:
        await Player.print(f"\n{winner} wins with {winner.score} points!")
        await Player.print("\nFinal Rankings:")
        for i, player in enumerate(sorted_players, 1):
            await Player.print(f"  {i}. {player} - {player.score} points ({player.pieces_placed} pieces)")
    else:
        await Player.print("\n It's a draw!")

    return players, winner, errors  # this should not be messed with because that's how the discord bot works

if __name__ == "__main__":
    asyncio.run(main())

