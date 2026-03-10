from dataclasses import dataclass

@dataclass
class Piece:
    name: str          # "Pawn", "Rook", etc.
    piece_type: str    # "pawn", "rook", etc.
    char: str
    pos: tuple[int, int]  # (row, col)
    color: str         # orange(\033[31m), blue(\033[34m)
