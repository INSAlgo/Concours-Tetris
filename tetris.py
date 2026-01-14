#!/usr/bin/env python3
"""
Tetris Game Implementation for AI Competition.

This module implements a Tetris game engine that supports both human players and AI bots.
It handles game state, piece movement, collision detection, scoring, and communication
with external AI processes via standard input/output.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import contextlib
import signal
from typing import Callable, Any, Awaitable
from io import StringIO
from pathlib import Path
import argparse, os, platform, random, re, shutil, subprocess, sys, statistics
import asyncio

os.environ["PYTHONASYNCIODEBUG"] = "0"

# Game Configuration
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# Visual representation of board elements
EMOJIS = {
    "empty": "⬛",
    "I": "🟦",
    "O": "🟨",
    "T": "🟪",
    "S": "🟩",
    "Z": "🟥",
    "J": "⬜",
    "L": "🟧",
}

# Tetromino definitions using ASCII art
PIECES = {
    "I": """
####
""",
    "O": """
##
##
""",
    "T": """
 # 
###
""",
    "S": """
 ##
## 
""",
    "Z": """
## 
 ##
""",
    "J": """
#  
###
""",
    "L": """
  #
###
""",
}

# Scoring system: points for clearing 1, 2, 3, or 4 lines simultaneously
CLEARING_SCORE = [100, 300, 500, 800]

def parse_piece(text: str) -> list[tuple[int, int]]:
    """
    Parses an ASCII representation of a piece into a list of coordinates.
    
    Args:
        text (str): ASCII art string of the piece.
        
    Returns:
        list[tuple[int, int]]: List of (x, y) coordinates representing the piece's blocks,
                               normalized so the top-leftmost block is relative to (0,0).
    """
    lines = [line.rstrip() for line in text.strip().split("\n") if line.strip()]
    if not lines:
        return []
    
    shape = []
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char == "#":
                shape.append((x, y))
                
    if shape:
        # Normalize coordinates to start from (0,0)
        min_x = min(x for x, y in shape)
        min_y = min(y for x, y in shape)
        shape = [(x - min_x, y - min_y) for x, y in shape]
    return shape

def generate_rotations():
    """
    Pre-calculates all 4 rotations for each piece type.
    
    Returns:
        dict: Mapping of piece name to a list of 4 shapes (one for each 90-degree rotation).
    """
    rotations = {}
    for name, text in PIECES.items():
        base = parse_piece(text)
        if name == "O":
            # O piece looks the same in all rotations
            rotations[name] = [base] * 4
        else:
            all_rots = [base]
            current = base
            for _ in range(3):
                # Rotate 90 degrees clockwise: (x, y) -> (y, -x)
                current = [(y, -x) for x, y in current]
                # Re-normalize coordinates after rotation
                min_x = min(x for x, y in current)
                min_y = min(y for x, y in current)
                current = [(x - min_x, y - min_y) for x, y in current]
                all_rots.append(current)
            rotations[name] = all_rots
    return rotations

# Global lookup tables for piece data
PIECE_ROTATIONS = generate_rotations()
PIECE_NAMES = list(PIECES.keys())
PIECE_VALUES = {name: i + 1 for i, name in enumerate(PIECE_NAMES)}

# Timeouts for AI communication
TIMEOUT_LENGTH = 0.1
DISCORD_TIMEOUT = 60

# Type aliases for clarity
ValidMove = tuple[int, int]  # (x_position, rotation_index)
ValidInput = str             # Raw input string

InputFunction = Callable[..., Awaitable[str]]
OutputFunction = Callable[[str], Awaitable[None]]


class Player(ABC):
    """
    Abstract base class representing a player in the game.
    Can be implemented by Human or AI players.
    """
    ofunc: OutputFunction | None = None

    def __init__(self, no: int, name: str | None = None, **kwargs):
        """
        Initialize a player.
        
        Args:
            no (int): Player ID number.
            name (str, optional): Display name of the player.
        """
        self.no = no
        self.icon = self.no
        self.name = name
        self.rendered_name: str = ""

        # Game state
        self.board = [[0 for _ in range(BOARD_HEIGHT)] for _ in range(BOARD_WIDTH)]
        self.current_piece = None
        self.current_piece_name: str | None = None
        self.score = 0
        self.pieces_placed = 0

    def reset(self):
        """Resets the player's game state for a new run."""
        self.board = [[0 for _ in range(BOARD_HEIGHT)] for _ in range(BOARD_WIDTH)]
        self.current_piece = None
        self.current_piece_name = None
        self.score = 0
        self.pieces_placed = 0
        self.alive = True

    @abstractmethod
    async def start_game(self):
        """Prepare player for game start."""
        self.alive = True

    @abstractmethod
    async def lose_game(self):
        """Handle player losing the game."""
        await Player.print(f"{self} is eliminated")

    @abstractmethod
    async def ask_move(self, **kwargs) -> tuple[ValidMove, None] | tuple[None, str]:
        """
        Request a move from the player.
        
        Returns:
            tuple: ((x, rotation), None) if valid move, or (None, error_message) if invalid.
        """
        pass

    @abstractmethod
    async def tell_move(self, move: ValidInput) -> None:
        """Inform the player of a move (used in multiplayer context)."""
        pass

    async def tell_other_players(self, players: list[Player], move: ValidInput):
        """Broadcast a move to all other active players."""
        for other_player in players:
            if self != other_player and other_player.alive:
                await other_player.tell_move(move)

    @staticmethod
    async def sanitize(userInput: str, **kwargs) -> tuple[ValidMove, None] | tuple[None, str]:
        """
        Validates and parses raw user input into a game move.
        
        Args:
            userInput (str): The raw input string (expected format: "x rotation").
            **kwargs: Must contain 'current_piece' and 'board' for validation.
            
        Returns:
            tuple: ((x, rotation), None) if valid, or (None, error_message) if invalid.
        """
        if userInput == "stop":
            return None, "user interrupt"

        try:
            parts = userInput.strip().split()
            if len(parts) != 2:
                return None, "invalid format (expected: x rotation)"

            x = int(parts[0])
            rotation = int(parts[1])

            if x < 0 or x >= BOARD_WIDTH:
                return None, f"x must be between 0 and {BOARD_WIDTH - 1}"

            if rotation < 0 or rotation > 3:
                return None, "rotation must be between 0 and 3"

            current_piece = kwargs.get("current_piece")
            board = kwargs.get("board")

            if current_piece is None or board is None:
                return None, "missing game state"

            if not is_valid_placement(board, current_piece, x, rotation):
                return None, "invalid placement"

            return (x, rotation), None

        except ValueError:
            return None, "x and rotation must be integers"

    @staticmethod
    async def print(output: StringIO | str, send_discord=True, end="\n"):
        """
        Unified printing method that handles both console output and optional Discord messaging.
        """
        if isinstance(output, StringIO):
            text = output.getvalue()
            output.close()
        else:
            text = output + end
        print(text, end="")
        if Player.ofunc and send_discord:
            await Player.ofunc(text)

    def __str__(self) -> str:
        return self.rendered_name


class Human(Player):
    """
    Represents a human player interacting via console or Discord.
    """
    def __init__(self, no: int, name: str | None = None, ifunc: InputFunction | None = None, **kwargs):
        super().__init__(no, name, **kwargs)
        self.ifunc = ifunc
        self.rendered_name = f"{self.name} {self.icon}" if name else f"Player {self.icon}"

    async def start_game(self, **_):
        await super().start_game()

    async def lose_game(self):
        await super().lose_game()

    async def ask_move(self, **kwargs) -> tuple[ValidMove, None] | tuple[None, str]:
        """Prompts the human user for input."""
        await super().ask_move(**kwargs)
        await Player.print(f"Awaiting {self}'s move (x rotation): ", end="")
        try:
            user_input = await self.input()
        except asyncio.TimeoutError:
            await Player.print(f"User did not respond in time (over {DISCORD_TIMEOUT}s)")
            return None, "timeout"
        return await Human.sanitize(user_input, **kwargs)

    async def tell_move(self, move: ValidInput) -> None:
        return await super().tell_move(move)

    async def input(self) -> str:
        """Reads input from configured input function or stdin."""
        if self.ifunc and self.name:
            user_input = await asyncio.wait_for(
                self.ifunc(self.name), timeout=DISCORD_TIMEOUT
            )
            await Player.print(user_input, send_discord=False)
            return user_input
        else:
            return input()


class AI(Player):
    """
    Represents an AI player running as a separate subprocess.
    """
    prog: asyncio.subprocess.Process

    @staticmethod
    def prepare_command(progPath: str | Path):
        """
        Constructs the command line to execute the AI program based on file extension.
        Supports Python, Node.js, Java, and compiled binaries.
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
                command = f"./{progPath}" if os.name == "posix" else f"{progPath}"

        # Sandbox execution on Linux if firejail is available
        if (
            platform.system() == "Linux"
            and shutil.which("firejail") is not None
            and os.path.exists("tetris.profile")
        ):
            command = f"firejail --profile=tetris.profile {command}"
            print(f"Running command with firejail!")

        print(f"Prepared command for {progPath}: {command}")
        return command

    def __init__(self, no: int, prog_path: str, discord: bool, **kwargs):
        super().__init__(no, Path(prog_path).stem, **kwargs)
        self.prog_path = prog_path
        self.command = AI.prepare_command(self.prog_path)

        if discord:
            if self.name and self.name.startswith("ai_"):
                self.name = self.name[3:]
            self.rendered_name = f"<@{self.name}>'s AI {self.icon}"
        else:
            self.rendered_name = f"AI {self.icon} ({self.name})"

    async def drain(self):
        """Ensures data is flushed to the subprocess stdin."""
        if self.prog.stdin:
            # type: ignore
            if hasattr(self.prog.stdin.transport, "_conn_lost") and self.prog.stdin.transport._conn_lost: # type: ignore
                self.prog.stdin.close()
                # This assignment is technically invalid for Process.stdin but used here for recovery
                # We'll ignore the type error as this is a specific hack
                self.prog.stdin = asyncio.subprocess.PIPE # type: ignore
            else:
                await self.prog.stdin.drain()

    async def start_game(self, **kwargs):
        """
        Starts the AI subprocess and sends initial game configuration.
        Protocol:
        1. Board dimensions (WIDTH HEIGHT)
        2. Number of piece types
        3. For each piece: Name and base coordinates
        """
        await super().start_game()
        print(f"Starting AI subprocess for {self.prog_path}")
        self.prog = await asyncio.create_subprocess_shell(
            AI.prepare_command(self.prog_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        print(f"AI subprocess created: {self.prog}")

        if self.prog.stdin:
            self.prog.stdin.write(f"{BOARD_WIDTH} {BOARD_HEIGHT}\n".encode())
            await self.drain()

            self.prog.stdin.write(f"{len(PIECE_NAMES)}\n".encode())
            await self.drain()

            for piece in PIECE_NAMES:
                base_shape = PIECE_ROTATIONS[piece][0]
                coords_str = " ".join(f"{x},{y}" for x, y in base_shape)
                self.prog.stdin.write(f"{piece} {coords_str}\n".encode())
                await self.drain()

    async def lose_game(self):
        await super().lose_game()

    async def ask_move(self, debug: bool = True, **kwargs) -> tuple[ValidMove, None] | tuple[None, str]:
        """
        Sends current piece to AI and waits for its move.
        Handles timeouts and debug output from the AI.
        """
        await super().ask_move(**kwargs)

        current_piece = kwargs.get("current_piece")
        if self.prog.stdin and current_piece:
            self.prog.stdin.write(f"{current_piece}\n".encode())
            await self.drain()

        try:
            while True:
                if not self.prog.stdout:
                    return None, "communication failed"
                progInput = await asyncio.wait_for(
                    self.prog.stdout.readuntil(), TIMEOUT_LENGTH
                )

                if not isinstance(progInput, bytes):
                    continue
                progInput = progInput.decode().strip()

                # Handle debug output from AI (lines starting with 'Traceback' or '>')
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
                    if debug:
                        await Player.print(f"{self} {progInput}")
                else:
                    break

            await Player.print(f"{self}'s move : {progInput}")

        except (asyncio.TimeoutError, asyncio.exceptions.IncompleteReadError):
            await Player.print(f"AI did not respond in time (over {TIMEOUT_LENGTH}s)")
            return None, "timeout"

        return await AI.sanitize(progInput, **kwargs)

    async def tell_move(self, move: ValidInput) -> None:
        """Sends opponent moves to the AI (if protocol supports it)."""
        if self.prog.stdin:
            self.prog.stdin.write(f"{move}\n".encode())
            await self.drain()

    async def stop_game(self):
        """Terminates the AI subprocess safely."""
        if not hasattr(self, "prog") or not self.prog:
            return

        try:
            if self.prog.stdin:
                self.prog.stdin.close()
                with contextlib.suppress(Exception):
                    # type: ignore
                    self.prog.stdin._transport.__del__() # type: ignore

            if hasattr(self.prog, "terminate"):
                with contextlib.suppress(ProcessLookupError):
                    self.prog.terminate()
                    try:
                        await asyncio.wait_for(self.prog.wait(), timeout=1)
                        return
                    except asyncio.TimeoutError:
                        pass

            if hasattr(self.prog, "kill"):
                with contextlib.suppress(ProcessLookupError):
                    self.prog.kill()
                try:
                    await asyncio.wait_for(self.prog.wait(), timeout=1)
                    return
                except asyncio.TimeoutError:
                    pass

            if hasattr(self.prog, "pid") and self.prog.pid is not None:
                if os.name == "posix":
                    with contextlib.suppress(ProcessLookupError, OSError):
                        os.killpg(os.getpgid(self.prog.pid), signal.SIGKILL)
                else:
                    subprocess.run(["taskkill", "/PID", str(self.prog.pid), "/T", "/F"])
                
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self.prog.wait(), timeout=1)
                    return
        except Exception as e:
            print(f"Error while terminating AI process: {e}")
            
        raise Exception("Could not kill the AI process")


# --- Helper Functions ---

def get_piece_shape(piece_name: str, rotation: int) -> list[tuple[int, int]]:
    """Retrieves the coordinates for a specific piece and rotation."""
    return PIECE_ROTATIONS[piece_name][rotation % 4]

def get_drop_position(board: list[list[int]], shape: list[tuple[int, int]], x: int) -> int:
    """
    Calculates the lowest Y position a piece can drop to at a given X coordinate.
    This implements the "hard drop" mechanic logic.
    """
    max_y = BOARD_HEIGHT
    for dx, dy in shape:
        px = x + dx
        # Check column for highest occupied block
        for py in range(BOARD_HEIGHT):
            if board[px][py] != 0:
                max_y = min(max_y, py - dy - 1)
                break
        else:
            # Column is empty
            max_y = min(max_y, BOARD_HEIGHT - 1 - dy)
    return max_y

def is_valid_placement(board: list[list[int]], piece_name: str, x: int, rotation: int) -> bool:
    """
    Checks if a piece can be validly placed at the given X coordinate and rotation.
    A placement is valid if:
    1. The piece fits within the board width.
    2. The piece does not overlap with existing blocks when dropped.
    3. The piece stays within the board height.
    """
    shape = get_piece_shape(piece_name, rotation)

    # Check horizontal bounds
    for dx, dy in shape:
        px = x + dx
        if px < 0 or px >= BOARD_WIDTH:
            return False

    # Calculate drop position
    max_y = get_drop_position(board, shape, x)

    # Check vertical bounds and collision
    for dx, dy in shape:
        px = x + dx
        py = max_y + dy
        if py < 0 or py >= BOARD_HEIGHT:
            return False
        if board[px][py] != 0:
            return False

    return True

def place_piece(board: list[list[int]], piece_name: str, x: int, rotation: int) -> int:
    """
    Places a piece on the board at the calculated drop position and clears full lines.
    
    Returns:
        int: The number of lines cleared.
    """
    shape = get_piece_shape(piece_name, rotation)
    max_y = get_drop_position(board, shape, x)

    # Update board with new piece blocks
    for dx, dy in shape:
        px = x + dx
        py = max_y + dy
        board[px][py] = PIECE_VALUES[piece_name]

    # Check for and clear full lines
    lines_cleared = 0
    y = 0
    while y < BOARD_HEIGHT:
        if all(board[x][y] != 0 for x in range(BOARD_WIDTH)):
            lines_cleared += 1
            # Shift all lines above down by one
            for yy in range(y, 0, -1):
                for x in range(BOARD_WIDTH):
                    board[x][yy] = board[x][yy - 1]
            # Clear the top line
            for x in range(BOARD_WIDTH):
                board[x][0] = 0
            # Re-check the same row index as lines have shifted down
        else:
            y += 1

    return lines_cleared

def render_board(board: list[list[int]], player_name: str) -> str:
    """
    Creates a string representation of the game board for display.
    
    Args:
        board (list[list[int]]): The game board matrix.
        player_name (str): Name of the player to display above the board.
        
    Returns:
        str: The formatted board string with borders and emojis.
    """
    output = StringIO()
    print(f"\n{player_name}'s Board:", file=output)
    print("┌" + "─" * BOARD_WIDTH * 2 + "┐", file=output)

    for y in range(BOARD_HEIGHT):
        line = "│"
        for x in range(BOARD_WIDTH):
            value = board[x][y]
            line += EMOJIS[PIECE_NAMES[value - 1]] if value != 0 else EMOJIS["empty"]
        line += "│"
        print(line, file=output)

    print("└" + "─" * BOARD_WIDTH * 2 + "┘", file=output)
    print("  " + " ".join(str(i) for i in range(BOARD_WIDTH)), file=output)

    return output.getvalue()

def get_next_piece(rng: random.Random) -> str:
    """
    Selects the next piece randomly.
    
    Args:
        rng (random.Random): Seeded random number generator for deterministic gameplay.
        
    Returns:
        str: The name of the next piece (e.g., "I", "T", "O").
    """
    return rng.choice(PIECE_NAMES)


async def game(players: list[Human | AI], debug: bool, **kwargs) -> tuple[list[Human | AI], Human | AI | None, dict]:
    """
    Main game loop managing the lifecycle of a match.
    
    Handles:
    - Player initialization
    - Concurrent game execution for all players
    - Turn management and move validation
    - Scoring and win condition checking
    - Resource cleanup
    
    Args:
        players (list[Human | AI]): List of participating players.
        debug (bool): Whether to show debug output from AIs.
        **kwargs: Additional game configuration (e.g., seed).
        
    Returns:
        tuple: (list of players, winner object or None, dictionary of errors)
    """
    errors = {}
    seed = kwargs.get("seed", 42)

    # Initialize all players concurrently
    starters = (player.start_game(**kwargs) for player in players)
    await asyncio.gather(*starters)

    async def play_solo_game(player: Human | AI):
        """
        Manages the game loop for a single player.
        Each player runs in their own async task.
        """
        # Use a seeded RNG so all players get the same sequence of pieces
        rng = random.Random(seed)
        player.current_piece_name = get_next_piece(rng)

        try:
            while player.alive:
                # Display game state
                board_display = render_board(player.board, str(player))
                await Player.print(board_display)
                await Player.print(f"Current piece: {player.current_piece_name}")
                await Player.print(f"Score: {player.score} | Pieces placed: {player.pieces_placed}")

                # Get move from player
                user_input, error = None, None
                while not user_input:
                    user_input, error = await player.ask_move(
                        debug=debug,
                        current_piece=player.current_piece_name,
                        board=player.board,
                    )
                    # Break immediately on critical errors or AI failure
                    if isinstance(player, AI) or error in ("user interrupt", "timeout"):
                        break

                # Handle move result
                if not user_input:
                    await player.lose_game()
                    errors[player] = error
                    player.alive = False
                else:
                    x, rotation = user_input
                    lines_cleared = place_piece(player.board, player.current_piece_name, x, rotation)

                    # Update score based on lines cleared
                    if lines_cleared > 0:
                        if lines_cleared <= 4:
                            line_points = CLEARING_SCORE[lines_cleared-1]
                        else:
                            line_points = 800 + (lines_cleared - 4) * 300
                        player.score += line_points
                        await Player.print(f"{player} cleared {lines_cleared} line(s)! (+{line_points} points)")

                    # Base score for placing a piece
                    player.score += 1
                    player.pieces_placed += 1
                    player.current_piece_name = get_next_piece(rng)
        except Exception as e:
            await Player.print(f"An error occurred for {player}: {e}")
            errors[player] = "error"
            player.alive = False

    # Run all games in parallel
    await asyncio.gather(*[play_solo_game(player) for player in players])

    # Determine winner based on highest score
    winner = max(players, key=lambda p: p.score) if players else None

    # Cleanup AI processes
    enders = (player.stop_game() for player in players if isinstance(player, AI))
    await asyncio.gather(*enders)

    return players, winner, errors


async def main(raw_args: str | None = None, ifunc: InputFunction | None = None, ofunc: OutputFunction | None = None, discord=False):
    """
    Entry point for the game application.
    Parses arguments, sets up players, and runs the game loop.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("prog", nargs="*", help="AI program to play the game ('user' to play yourself)")
    parser.add_argument("-s", "--silent", action="store_true", help="only show the result of the game")
    parser.add_argument("-n", "--nodebug", action="store_true", help="do not print the debug output of the programs")
    parser.add_argument("--seed", type=int, default=42, help="random seed for piece sequence (default: 42)")
    parser.add_argument("--runs", type=int, default=1, help="number of runs to average over (default: 1)")

    args = parser.parse_args(raw_args)

    Player.ofunc = ofunc
    players = []
    ai_only = True
    pattern = re.compile(r"^\<\@[0-9]{18}\>$")
    
    # Initialize players based on arguments
    for i, name in enumerate(args.prog):
        if name == "user":
            players.append(Human(i))
            ai_only = False
        elif pattern.match(name):
            # Discord user ID pattern
            players.append(Human(i, name, ifunc))
            ai_only = False
        else:
            players.append(AI(i, name, discord))

    scores_per_ai = {player.name: [] for player in players if isinstance(player, AI)} # type: ignore

    winner: Player | None = None
    errors: dict[Player, str | None] = {}
    players_run: list[Human | AI] = []
    origin_stdout = sys.stdout

    # Main game loop (supports multiple runs for statistics)
    for run in range(args.runs):
        seed = args.seed + run
        for player in players:
            player.reset()
            
        temp_silent = args.silent or args.runs > 1
        origin_stdout = sys.stdout
        
        # Suppress output if requested or running multiple simulations
        if temp_silent:
            if not ai_only:
                output = StringIO("Game cannot be silent since humans are playing")
                tmp = output.getvalue()
                await Player.print(output)
                raise Exception(tmp)
            if discord:
                Player.ofunc = None
            else:
                sys.stdout = open(os.devnull, "w", encoding="utf-8")

        players_run, winner, errors = await game(players, not args.nodebug, seed=seed)

        # Restore output
        if temp_silent:
            sys.stdout = origin_stdout
            Player.ofunc = ofunc

        # Record scores
        for player in players_run:
            if isinstance(player, AI) and player.name:
                scores_per_ai[player.name].append(player.score)

    if args.silent:
        sys.stdout = origin_stdout
        Player.ofunc = ofunc

    # Display results
    if args.runs > 1:
        await Player.print(f"\n=== AVERAGE RESULTS OVER {args.runs} RUNS ===")
        for ai_name, scores in scores_per_ai.items():
            avg = statistics.mean(scores)
            std = statistics.stdev(scores) if len(scores) > 1 else 0
            await Player.print(f"{ai_name}: Average {avg:.2f} ± {std:.2f}")
    else:
        await Player.print("\n=== FINAL RESULTS ===")
        for player in players:
            board_display = render_board(player.board, str(player))
            await Player.print(board_display)
            await Player.print(f"{player} - Final Score: {player.score} | Pieces Placed: {player.pieces_placed}")

        sorted_players = sorted(players, key=lambda p: p.score, reverse=True)

        if winner:
            if discord and winner.name and winner.name.startswith("ai_"):
                winner.name = winner.name[3:]

            await Player.print("\nFinal Rankings:")
            for i, player in enumerate(sorted_players, 1):
                await Player.print(f"  {i}. {player} - {player.score} points ({player.pieces_placed} pieces)")
        else:
            await Player.print("\n It's a draw!")

    return players, winner, errors


if __name__ == "__main__":
    asyncio.run(main())
