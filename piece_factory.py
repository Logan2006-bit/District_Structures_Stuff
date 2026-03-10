from chess_pieces import Piece
from chess_controls import square_to_rc
from symbols import get_piece_char

def create_piece(piece_type, square, style, symbol_sets, color):
    char = get_piece_char(piece_type, style, symbol_sets)
    return Piece(
        name=piece_type.title(),
        piece_type=piece_type,
        char=char,
        pos=square_to_rc(square),
        color=color
    )

