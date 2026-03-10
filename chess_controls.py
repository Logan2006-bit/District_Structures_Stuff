# chess_controls.py
FILES = "abcdefgh"
RANKS = "12345678"

ORANGE = "orange"
BLUE = "blue"

# ---------------------------
# Coordinate helpers
# ---------------------------

def square_to_rc(square: str) -> tuple[int, int]:
    square = square.strip().lower()
    if len(square) != 2 or square[0] not in FILES or square[1] not in RANKS:
        raise ValueError("Square must look like e2, a1, h8, etc.")

    col = FILES.index(square[0])     # a->0 ... h->7
    rank = int(square[1])            # 1..8
    row = 8 - rank                   # rank 8 -> row 0, rank 1 -> row 7
    return row, col

def rc_to_square(row: int, col: int) -> str:
    return f"{FILES[col]}{8 - row}"

def is_on_board(row: int, col: int) -> bool:
    return 0 <= row < 8 and 0 <= col < 8

# ---------------------------
# Input
# ---------------------------

def prompt_move(turn: str | None = None) -> tuple[tuple[int, int], tuple[int, int]] | None:
    prefix = f"[{turn}] " if turn else ""
    raw = input(f"{prefix}Move (from to) like 'e2 e4' (or 'quit'): ").strip().lower()

    if raw in {"q", "quit", "exit"}:
        return None

    parts = raw.split()
    if len(parts) != 2:
        print("Please enter exactly two squares, like: e2 e4\n")
        return prompt_move(turn)

    from_sq, to_sq = parts
    try:
        return square_to_rc(from_sq), square_to_rc(to_sq)
    except ValueError as e:
        print(f"{e}\n")
        return prompt_move(turn)

# ---------------------------
# Board / piece lookup
# ---------------------------

def find_piece_at(pieces: list, pos: tuple[int, int]):
    for piece in pieces:
        if piece.pos == pos:
            return piece
    return None

def is_enemy(a, b) -> bool:
    return a is not None and b is not None and a.color != b.color

def is_friend(a, b) -> bool:
    return a is not None and b is not None and a.color == b.color

# ---------------------------
# Legal move generation
# ---------------------------

def legal_moves(piece, pieces: list) -> set[tuple[int, int]]:
    """
    Returns a set of destination squares (row,col) that are legal
    by *movement rules + blocking + captures*.
    (No check rules yet.)
    """
    ptype = piece.piece_type.lower()
    moves: set[tuple[int, int]] = set()

    if ptype == "pawn":
        moves |= _pawn_moves(piece, pieces)
    elif ptype == "rook":
        moves |= _sliding_moves(piece, pieces, directions=[(1,0),(-1,0),(0,1),(0,-1)])
    elif ptype == "bishop":
        moves |= _sliding_moves(piece, pieces, directions=[(1,1),(1,-1),(-1,1),(-1,-1)])
    elif ptype == "queen":
        moves |= _sliding_moves(piece, pieces, directions=[
            (1,0),(-1,0),(0,1),(0,-1),
            (1,1),(1,-1),(-1,1),(-1,-1)
        ])
    elif ptype == "knight":
        moves |= _knight_moves(piece, pieces)
    elif ptype == "king":
        moves |= _king_moves(piece, pieces)
    else:
        # Unknown piece type (shouldn't happen)
        pass

    return moves

def _pawn_moves(piece, pieces: list) -> set[tuple[int, int]]:
    r, c = piece.pos
    moves: set[tuple[int, int]] = set()

    # Orange starts on rank 2 (row 6) and moves "up" (row - 1)
    # Blue starts on rank 7 (row 1) and moves "down" (row + 1)
    if piece.color == ORANGE:
        direction = -1
        start_row = 6
    else:
        direction = +1
        start_row = 1

    # 1-step forward
    one = (r + direction, c)
    if is_on_board(*one) and find_piece_at(pieces, one) is None:
        moves.add(one)

        # 2-step forward (only if 1-step is clear)
        two = (r + 2*direction, c)
        if r == start_row and is_on_board(*two) and find_piece_at(pieces, two) is None:
            moves.add(two)

    # Diagonal captures
    for dc in (-1, +1):
        diag = (r + direction, c + dc)
        if not is_on_board(*diag):
            continue
        target = find_piece_at(pieces, diag)
        if target is not None and target.color != piece.color:
            moves.add(diag)

    return moves

def _sliding_moves(piece, pieces: list, directions: list[tuple[int,int]]) -> set[tuple[int, int]]:
    r, c = piece.pos
    moves: set[tuple[int, int]] = set()

    for dr, dc in directions:
        rr, cc = r + dr, c + dc
        while is_on_board(rr, cc):
            occupant = find_piece_at(pieces, (rr, cc))
            if occupant is None:
                moves.add((rr, cc))
            else:
                # blocked: can capture enemy, but cannot move past
                if occupant.color != piece.color:
                    moves.add((rr, cc))
                break
            rr += dr
            cc += dc

    return moves

def _knight_moves(piece, pieces: list) -> set[tuple[int, int]]:
    r, c = piece.pos
    moves: set[tuple[int, int]] = set()

    jumps = [
        (-2,-1),(-2,+1),
        (-1,-2),(-1,+2),
        (+1,-2),(+1,+2),
        (+2,-1),(+2,+1),
    ]

    for dr, dc in jumps:
        rr, cc = r + dr, c + dc
        if not is_on_board(rr, cc):
            continue
        occupant = find_piece_at(pieces, (rr, cc))
        if occupant is None or occupant.color != piece.color:
            moves.add((rr, cc))

    return moves

def _king_moves(piece, pieces: list) -> set[tuple[int, int]]:
    r, c = piece.pos
    moves: set[tuple[int, int]] = set()

    for dr in (-1, 0, +1):
        for dc in (-1, 0, +1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if not is_on_board(rr, cc):
                continue
            occupant = find_piece_at(pieces, (rr, cc))
            if occupant is None or occupant.color != piece.color:
                moves.add((rr, cc))

    return moves

# ---------------------------
# Apply move (turn + legality + captures)
# ---------------------------

def apply_move(pieces: list, from_rc: tuple[int, int], to_rc: tuple[int, int], turn: str):
    piece = find_piece_at(pieces, from_rc)
    if piece is None:
        print("No piece at that square.\n")
        return None

    if piece.color != turn:
        print(f"That's not your piece. It's {turn}'s turn.\n")
        return None

    if to_rc == from_rc:
        print("You didn't move anywhere.\n")
        return None

    if not is_on_board(*to_rc):
        print("Destination is off the board.\n")
        return None

    moves = legal_moves(piece, pieces)
    if to_rc not in moves:
        print("Illegal move for that piece.\n")
        return None

    # Capture if enemy occupies destination
    target = find_piece_at(pieces, to_rc)
    if target is not None:
        if target.color == piece.color:
            print("You can't capture your own piece.\n")
            return None
        pieces.remove(target)

    piece.pos = to_rc
    return piece

# --- ADD TO chess_controls.py (bottom) ---

def all_legal_moves_for_color(pieces: list, color: str) -> list[tuple[tuple[int,int], tuple[int,int]]]:
    """
    Returns a list of (from_rc, to_rc) moves for the given color, using legal_moves().
    """
    moves: list[tuple[tuple[int,int], tuple[int,int]]] = []
    for p in pieces:
        if p.color != color:
            continue
        for dst in legal_moves(p, pieces):
            moves.append((p.pos, dst))
    return moves

def has_king(pieces: list, color: str) -> bool:
    return any(p.color == color and p.piece_type.lower() == "king" for p in pieces)
