import json
from pathlib import Path

PIECE_ORDER = ["pawn", "rook", "king", "queen", "bishop", "knight"]

def load_symbol_sets(things_path: str = "things.json") -> dict[str, dict[str, str]]:
    
    data = json.loads(Path(things_path).read_text(encoding="utf-8"))

    initials = data["pieces_initial"]
    emojis   = data["pieces_emoji"]

    if len(initials) != 6 or len(emojis) != 6:
        raise ValueError("Expected 6 entries each in pieces_initial and pieces_emoji.")

    return {
        "initial": dict(zip(PIECE_ORDER, initials)),
        "emoji": dict(zip(PIECE_ORDER, emojis)),
    }

def get_piece_char(piece_type: str, style: str, symbol_sets: dict[str, dict[str, str]]) -> str:
    piece_type = piece_type.strip().lower()
    style = style.strip().lower()

    if style not in symbol_sets:
        raise ValueError(f"Unknown style '{style}'. Use one of: {list(symbol_sets.keys())}")

    if piece_type not in symbol_sets[style]:
        raise ValueError(f"Unknown piece type '{piece_type}'. Use one of: {list(symbol_sets[style].keys())}")

    return symbol_sets[style][piece_type]
