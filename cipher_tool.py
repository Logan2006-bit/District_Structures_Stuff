#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple


# ---------------------------
# Helpers: normalization + Caesar
# ---------------------------

def normalize(text: str) -> str:
    """
    Uppercase, remove punctuation, convert spaces to '_'.
    Keep only A-Z and underscore.
    """
    out = []
    for ch in text.upper():
        if "A" <= ch <= "Z":
            out.append(ch)
        elif ch.isspace():
            out.append("_")
        elif ch == "_":
            out.append("_")
        else:
            # drop punctuation and everything else
            pass
    # collapse multiple underscores if you want; comment out if not desired
    # norm = "".join(out)
    # while "__" in norm:
    #     norm = norm.replace("__", "_")
    # return norm
    return "".join(out)


def caesar_shift(s: str, shift: int) -> str:
    """Shift A-Z; keep '_' unchanged."""
    out = []
    for ch in s:
        if "A" <= ch <= "Z":
            x = ord(ch) - ord("A")
            y = (x + shift) % 26
            out.append(chr(y + ord("A")))
        else:
            out.append(ch)
    return "".join(out)


def caesar_unshift(s: str, shift: int) -> str:
    """Reverse shift for A-Z; keep '_' and '0' unchanged."""
    out = []
    for ch in s:
        if "A" <= ch <= "Z":
            x = ord(ch) - ord("A")
            y = (x - shift) % 26
            out.append(chr(y + ord("A")))
        else:
            out.append(ch)
    return "".join(out)


def strip_trailing_zeros(s: str) -> str:
    return s.rstrip("0")


def pretty(s: str) -> str:
    return s.replace("_", " ")


# ---------------------------
# Layer 1+2: track mux into 6-char blocks
# ---------------------------

def mux_three_tracks(
    A: str, B: str, C: str,
    pad: str = "0"
) -> str:
    """
    Build 6-char blocks with positions:
      A -> 1 & 4
      B -> 2 & 5
      C -> 3 & 6
    If a track runs out, pad with '0'.
    """
    ia = ib = ic = 0
    out = []

    # Each block consumes 2 chars per track (if available)
    # Continue until all three tracks are fully consumed.
    while ia < len(A) or ib < len(B) or ic < len(C):
        # fetch next two from each, pad if missing
        a1 = A[ia] if ia < len(A) else pad
        ia += 1 if ia < len(A) else 0
        a2 = A[ia] if ia < len(A) else pad
        ia += 1 if ia < len(A) else 0

        b1 = B[ib] if ib < len(B) else pad
        ib += 1 if ib < len(B) else 0
        b2 = B[ib] if ib < len(B) else pad
        ib += 1 if ib < len(B) else 0

        c1 = C[ic] if ic < len(C) else pad
        ic += 1 if ic < len(C) else 0
        c2 = C[ic] if ic < len(C) else pad
        ic += 1 if ic < len(C) else 0

        # block = [A][B][C][A][B][C]
        out.extend([a1, b1, c1, a2, b2, c2])

    return "".join(out)


def split_blocks(s: str, n: int) -> List[str]:
    if len(s) % n != 0:
        raise ValueError(f"Length {len(s)} not divisible by {n}.")
    return [s[i:i+n] for i in range(0, len(s), n)]


def extract_tracks(cipher_base: str) -> Tuple[str, str, str]:
    blocks = split_blocks(cipher_base, 6)
    A = []
    B = []
    C = []
    for b in blocks:
        A.append(b[0]); A.append(b[3])
        B.append(b[1]); B.append(b[4])
        C.append(b[2]); C.append(b[5])
    return "".join(A), "".join(B), "".join(C)


# ---------------------------
# Layer 3: 20 chunks x 15 + pair swap
# ---------------------------

def chunkify(s: str, chunk_len: int) -> List[str]:
    if len(s) % chunk_len != 0:
        raise ValueError(f"Length {len(s)} not divisible by chunk_len={chunk_len}.")
    return [s[i:i+chunk_len] for i in range(0, len(s), chunk_len)]


def pair_swap_chunks(chunks: List[str]) -> List[str]:
    if len(chunks) % 2 != 0:
        raise ValueError("Need even number of chunks for pair-swap.")
    out = chunks[:]
    for i in range(0, len(out), 2):
        out[i], out[i+1] = out[i+1], out[i]
    return out


def apply_chunk_swap(cipher_base: str, num_chunks: int = 20, chunk_len: int = 15) -> str:
    expected = num_chunks * chunk_len
    if len(cipher_base) != expected:
        raise ValueError(f"Base ciphertext must be exactly {expected}, got {len(cipher_base)}.")
    chunks = chunkify(cipher_base, chunk_len)
    swapped = pair_swap_chunks(chunks)
    return "".join(swapped)


def undo_chunk_swap(cipher_final: str, num_chunks: int = 20, chunk_len: int = 15) -> str:
    # pair-swap is its own inverse
    expected = num_chunks * chunk_len
    if len(cipher_final) != expected:
        raise ValueError(f"Final ciphertext must be exactly {expected}, got {len(cipher_final)}.")
    chunks = chunkify(cipher_final, chunk_len)
    restored = pair_swap_chunks(chunks)
    return "".join(restored)


# ---------------------------
# Encode + Decode pipelines
# ---------------------------

def encode_to_ciphertext(
    gandalf: str, twain: str, pratchett: str,
    shift_a: int = 1, shift_b: int = 2, shift_c: int = 3,
    num_chunks: int = 20, chunk_len: int = 15
) -> str:
    A = caesar_shift(normalize(gandalf), shift_a)
    B = caesar_shift(normalize(twain), shift_b)
    C = caesar_shift(normalize(pratchett), shift_c)

    base = mux_three_tracks(A, B, C, pad="0")

    # For your assignment we want EXACTLY 300 so chunk swapping is 20x15.
    target = num_chunks * chunk_len
    if len(base) < target:
        base = base + ("0" * (target - len(base)))
    elif len(base) > target:
        base = base[:target]

    final = apply_chunk_swap(base, num_chunks=num_chunks, chunk_len=chunk_len)
    return final


def decode_from_ciphertext(
    cipher_final: str,
    shift_a: int = 1, shift_b: int = 2, shift_c: int = 3,
    verbose: bool = True
) -> Tuple[str, str, str]:
    # remove whitespace safely
    cipher_final = "".join(ch for ch in cipher_final if not ch.isspace())

    if verbose:
        print(f"Final ciphertext length: {len(cipher_final)}")

    base = undo_chunk_swap(cipher_final, num_chunks=20, chunk_len=15)

    if verbose:
        print("\n[Base restored] length:", len(base))
        print(base[:120] + ("..." if len(base) > 120 else ""))

        print("\n[First 10 blocks of 6]")
        for i, b in enumerate(split_blocks(base, 6)[:10], start=1):
            print(f"B{i:02d}: {b}")

    A_enc, B_enc, C_enc = extract_tracks(base)

    if verbose:
        print("\n[Extracted tracks (encrypted)]")
        print("A:", A_enc[:80] + ("..." if len(A_enc) > 80 else ""))
        print("B:", B_enc[:80] + ("..." if len(B_enc) > 80 else ""))
        print("C:", C_enc[:80] + ("..." if len(C_enc) > 80 else ""))

    A_plain = strip_trailing_zeros(caesar_unshift(A_enc, shift_a))
    B_plain = strip_trailing_zeros(caesar_unshift(B_enc, shift_b))
    C_plain = strip_trailing_zeros(caesar_unshift(C_enc, shift_c))

    return pretty(A_plain), pretty(B_plain), pretty(C_plain)


# ---------------------------
# CLI
# ---------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encode", action="store_true", help="Generate cipher.txt from the three quotes")
    ap.add_argument("--decode", action="store_true", help="Decode cipher.txt (shows steps)")
    ap.add_argument("--file", type=Path, default=Path("cipher.txt"), help="Ciphertext file path (default cipher.txt)")
    ap.add_argument("--quiet", action="store_true", help="Less printing during decode")
    args = ap.parse_args()

    gandalf_q = 'You a bitch,'
    twain_q = 'Hope schools going well,'
    pratch_q = "Funny third thing."

    if args.encode:
        cipher = encode_to_ciphertext(gandalf_q, twain_q, pratch_q)
        args.file.write_text(cipher, encoding="utf-8")
        print(f"Wrote {len(cipher)} characters to {args.file}")

    if args.decode:
        if not args.file.exists():
            raise FileNotFoundError(f"Missing file: {args.file}. Run with --encode first.")
        cipher_final = args.file.read_text(encoding="utf-8")
        A, B, C = decode_from_ciphertext(cipher_final, verbose=not args.quiet)
        print("\n==================== DECODED OUTPUTS ====================")
        print("\n[Track A / Gandalf]\n" + A)
        print("\n[Track B / Mark Twain]\n" + B)
        print("\n[Track C / Terry Pratchett]\n" + C)

    if not args.encode and not args.decode:
        print("Run one of:\n  python cipher_tool.py --encode\n  python cipher_tool.py --decode\n  python cipher_tool.py --encode --decode")

if __name__ == "__main__":
    main()
