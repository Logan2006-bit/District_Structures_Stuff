from __future__ import annotations

import copy
import json
import random
import re
import urllib.request
from dataclasses import dataclass
from typing import Optional

from chess_controls import (
    all_legal_moves_for_color,
    apply_move,
    rc_to_square,
    square_to_rc,
)

PIECE_VALUE = {
    "pawn": 1,
    "knight": 3,
    "bishop": 3,
    "rook": 5,
    "queen": 9,
    "king": 1000,  # huge so trades around king matter
}

def material_score(pieces: list, for_color: str) -> int:
    """
    Positive means advantage for for_color.
    """
    score = 0
    for p in pieces:
        val = PIECE_VALUE.get(p.piece_type.lower(), 0)
        score += val if p.color == for_color else -val
    return score

def move_to_uci(from_rc: tuple[int,int], to_rc: tuple[int,int]) -> str:
    return f"{rc_to_square(*from_rc)} {rc_to_square(*to_rc)}"

def parse_move_from_text(text: str) -> Optional[tuple[str, str]]:
    """
    Extracts something like 'e2 e4' from model output.
    """
    m = re.search(r"\b([a-h][1-8])\s+([a-h][1-8])\b", text.lower())
    if not m:
        return None
    return m.group(1), m.group(2)

class BaseBot:
    name = "BaseBot"
    def choose_move(self, pieces: list, color: str) -> tuple[tuple[int,int], tuple[int,int]]:
        raise NotImplementedError

class RandomBot(BaseBot):
    name = "RandomBot"
    def choose_move(self, pieces: list, color: str):
        moves = all_legal_moves_for_color(pieces, color)
        if not moves:
            raise RuntimeError("No legal moves available.")
        return random.choice(moves)

class GreedyBot(BaseBot):
    name = "GreedyBot"
    def choose_move(self, pieces: list, color: str):
        moves = all_legal_moves_for_color(pieces, color)
        if not moves:
            raise RuntimeError("No legal moves available.")

        # Prefer captures of highest-value piece; otherwise random.
        best = []
        best_gain = -10**9
        for fr, to in moves:
            target = next((p for p in pieces if p.pos == to), None)
            gain = 0
            if target is not None and target.color != color:
                gain = PIECE_VALUE.get(target.piece_type.lower(), 0)
            if gain > best_gain:
                best_gain = gain
                best = [(fr, to)]
            elif gain == best_gain:
                best.append((fr, to))

        return random.choice(best)

@dataclass
class MinimaxConfig:
    depth: int = 2
    randomness: float = 0.0  # 0 = deterministic best, 0.1 = a little variety

class MinimaxBot(BaseBot):
    name = "MinimaxBot"
    def __init__(self, config: MinimaxConfig | None = None):
        self.cfg = config or MinimaxConfig()

    def choose_move(self, pieces: list, color: str):
        moves = all_legal_moves_for_color(pieces, color)
        if not moves:
            raise RuntimeError("No legal moves available.")

        scored: list[tuple[int, tuple[tuple[int,int], tuple[int,int]]]] = []
        for fr, to in moves:
            sim = copy.deepcopy(pieces)
            ok = apply_move(sim, fr, to, color)
            if not ok:
                continue
            score = self._minimax(sim, self.cfg.depth - 1, self._other(color), color)
            scored.append((score, (fr, to)))

        if not scored:
            return random.choice(moves)

        scored.sort(key=lambda x: x[0], reverse=True)

        # Optional “skill knob”: add a little randomness so lower skill plays worse
        if self.cfg.randomness > 0 and len(scored) > 1:
            k = max(1, int(len(scored) * self.cfg.randomness))
            return random.choice([m for _, m in scored[:k]])

        return scored[0][1]

    def _minimax(self, pieces: list, depth: int, side_to_move: str, maximizing_color: str) -> int:
        if depth <= 0:
            return material_score(pieces, maximizing_color)

        moves = all_legal_moves_for_color(pieces, side_to_move)
        if not moves:
            return material_score(pieces, maximizing_color)

        if side_to_move == maximizing_color:
            best = -10**9
            for fr, to in moves:
                sim = copy.deepcopy(pieces)
                if not apply_move(sim, fr, to, side_to_move):
                    continue
                best = max(best, self._minimax(sim, depth - 1, self._other(side_to_move), maximizing_color))
            return best
        else:
            best = 10**9
            for fr, to in moves:
                sim = copy.deepcopy(pieces)
                if not apply_move(sim, fr, to, side_to_move):
                    continue
                best = min(best, self._minimax(sim, depth - 1, self._other(side_to_move), maximizing_color))
            return best

    def _other(self, c: str) -> str:
        return "blue" if c == "orange" else "orange"

@dataclass
class OllamaConfig:
    model: str = "llama3.2:1b"
    temperature: float = 0.2
    top_p: float = 0.9

class OllamaBot(BaseBot):
    name = "OllamaBot"
    def __init__(self, config: OllamaConfig | None = None):
        self.cfg = config or OllamaConfig()

    def choose_move(self, pieces: list, color: str):
        legal = all_legal_moves_for_color(pieces, color)
        if not legal:
            raise RuntimeError("No legal moves available.")

        legal_str = "\n".join(f"- {move_to_uci(fr, to)}" for fr, to in legal)

        # Give the model a constrained job: pick ONE from the list.
        prompt = f"""
You are a chess move selector.
Return EXACTLY ONE move in the format: e2 e4
Only choose from the LEGAL MOVES list below.

Side to move: {color}

LEGAL MOVES:
{legal_str}
""".strip()

        text = self._ollama_generate(prompt)
        parsed = parse_move_from_text(text)
        if parsed:
            frm_sq, to_sq = parsed
            try:
                fr = square_to_rc(frm_sq)
                to = square_to_rc(to_sq)
                if (fr, to) in legal:
                    return (fr, to)
            except Exception:
                pass

        # Fallback if model outputs garbage:
        return random.choice(legal)

    def _ollama_generate(self, prompt: str) -> str:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.cfg.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.cfg.temperature,
                "top_p": self.cfg.top_p,
            },
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")
