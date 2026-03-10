from colors import colorize
FILES = "abcdefgh"

def make_board() -> list[list[str]]:
    return [["." for _ in range(8)] for _ in range(8)]

def render_board(pieces: list) -> str:
    board = [["." for _ in range(8)] for _ in range(8)]

    for piece in pieces:
        r, c = piece.pos
        board[r][c] = colorize(piece.char, piece.color)

    lines = []
    lines.append("  a b c d e f g h")
    for r in range(8):
        lines.append(f"{8 - r} " + " ".join(board[r]))
    return "\n".join(lines)

def print_board(pieces: list) -> None:
    print(render_board(pieces))
    print()
