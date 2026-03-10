from chess_board import print_board
from chess_controls import prompt_move, apply_move, rc_to_square, has_king
from symbols import load_symbol_sets
from piece_factory import create_piece
import os
import time

from chess_ai import (
    RandomBot, GreedyBot, MinimaxBot, MinimaxConfig, OllamaBot, OllamaConfig
)

def pick_player(color: str):
    print(f"\nChoose player for {color}:")
    print("  1) human")
    print("  2) ai: random")
    print("  3) ai: greedy (captures)")
    print("  4) ai: minimax (depth-based)")
    print("  5) ai: ollama (llama3.2:1b)")
    choice = input("Select 1-5: ").strip()

    if choice == "1":
        return None  # human

    if choice == "2":
        return RandomBot()
    if choice == "3":
        return GreedyBot()
    if choice == "4":
        depth = input("Minimax depth (e.g. 1-4): ").strip()
        depth_i = int(depth) if depth.isdigit() else 2
        randomness = input("Randomness 0.0-1.0 (0=best only): ").strip()
        try:
            rand_f = float(randomness)
        except:
            rand_f = 0.0
        return MinimaxBot(MinimaxConfig(depth=depth_i, randomness=max(0.0, min(1.0, rand_f))))
    if choice == "5":
        temp = input("Ollama temperature (e.g. 0.1-1.0): ").strip()
        try:
            temp_f = float(temp)
        except:
            temp_f = 0.2
        return OllamaBot(OllamaConfig(model="llama3.2:1b", temperature=temp_f, top_p=0.9))

    print("Invalid choice; defaulting to human.")
    return None

def main():
    symbol_sets = load_symbol_sets("things.json")
    style = "emoji"   # or "initial"

    # --- your existing setup (unchanged) ---
    wpieces = [
        create_piece("pawn",   "a2", style, symbol_sets, "orange"),
        create_piece("pawn",   "b2", style, symbol_sets, "orange"),
        create_piece("pawn",   "c2", style, symbol_sets, "orange"),
        create_piece("pawn",   "d2", style, symbol_sets, "orange"),
        create_piece("pawn",   "e2", style, symbol_sets, "orange"),
        create_piece("pawn",   "f2", style, symbol_sets, "orange"),
        create_piece("pawn",   "g2", style, symbol_sets, "orange"),
        create_piece("pawn",   "h2", style, symbol_sets, "orange"),
        create_piece("rook",   "a1", style, symbol_sets, "orange"),
        create_piece("knight", "b1", style, symbol_sets, "orange"),
        create_piece("bishop", "c1", style, symbol_sets, "orange"),
        create_piece("queen",  "d1", style, symbol_sets, "orange"),
        create_piece("king",   "e1", style, symbol_sets, "orange"),
        create_piece("bishop", "f1", style, symbol_sets, "orange"),
        create_piece("knight", "g1", style, symbol_sets, "orange"),
        create_piece("rook",   "h1", style, symbol_sets, "orange"),
    ]

    bpieces = [
        create_piece("pawn",   "a7", style, symbol_sets, "blue"),
        create_piece("pawn",   "b7", style, symbol_sets, "blue"),
        create_piece("pawn",   "c7", style, symbol_sets, "blue"),
        create_piece("pawn",   "d7", style, symbol_sets, "blue"),
        create_piece("pawn",   "e7", style, symbol_sets, "blue"),
        create_piece("pawn",   "f7", style, symbol_sets, "blue"),
        create_piece("pawn",   "g7", style, symbol_sets, "blue"),
        create_piece("pawn",   "h7", style, symbol_sets, "blue"),
        create_piece("rook",   "a8", style, symbol_sets, "blue"),
        create_piece("knight", "b8", style, symbol_sets, "blue"),
        create_piece("bishop", "c8", style, symbol_sets, "blue"),
        create_piece("queen",  "d8", style, symbol_sets, "blue"),
        create_piece("king",   "e8", style, symbol_sets, "blue"),
        create_piece("bishop", "f8", style, symbol_sets, "blue"),
        create_piece("knight", "g8", style, symbol_sets, "blue"),
        create_piece("rook",   "h8", style, symbol_sets, "blue"),
    ]

    all_pieces = wpieces + bpieces

    print("Game setup:")
    orange_player = pick_player("orange")
    blue_player   = pick_player("blue")

    ai_delay = input("\nAI delay seconds (0 for none, e.g. 0.5): ").strip()
    try:
        ai_delay = float(ai_delay)
    except:
        ai_delay = 0.0

    turn = "orange"

    while True:
        os.system("cls")
        print_board(all_pieces)
        print(f"Turn: {turn}\n")

        # Simple win condition: king captured
        if not has_king(all_pieces, "orange"):
            print("Blue wins (orange king captured).")
            break
        if not has_king(all_pieces, "blue"):
            print("Orange wins (blue king captured).")
            break

        bot = orange_player if turn == "orange" else blue_player

        if bot is None:
            move = prompt_move(turn)
            if move is None:
                break
            from_rc, to_rc = move
        else:
            if ai_delay > 0:
                time.sleep(ai_delay)
            from_rc, to_rc = bot.choose_move(all_pieces, turn)
            print(f"{bot.name} plays: {rc_to_square(*from_rc)} {rc_to_square(*to_rc)}")

        moved_piece = apply_move(all_pieces, from_rc, to_rc, turn)
        if moved_piece:
            turn = "blue" if turn == "orange" else "orange"

if __name__ == "__main__":
    main()
