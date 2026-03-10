"""
Gambler's Ruin Simulation
"""

import random
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np


# ─────────────────────────────────────────
#  Base Values
# ─────────────────────────────────────────
STARTING_MONEY  = 50       # Gambler's starting bankroll ($)
TARGET          = 100      # Winning target ($)
WIN_PROBABILITY = 0.49     # Probability of winning each round (try 0.50, 0.49, 0.45)
NUM_SIMULATIONS = 1_000    # Total number of games to simulate
PATHS_TO_PLOT   = 75       # How many individual paths to draw on the graph


# ─────────────────────────────────────────
#  Core simulation
# ─────────────────────────────────────────
def simulate_game(start: int, target: int, p: float) -> tuple[bool, list[int]]:
    """
    Simulate one game of Gambler's Ruin.

    Returns:
        ruined  – True if the gambler went broke, False if they hit the target
        history – List of bankroll values each round
    """
    bankroll = start
    history  = [bankroll]

    while 0 < bankroll < target:
        if random.random() < p:
            bankroll += 1
        else:
            bankroll -= 1
        history.append(bankroll)

    return bankroll == 0, history


def theoretical_ruin_probability(start: int, target: int, p: float) -> float:
    """
    Exact closed-form probability of ruin.

    For p ≠ 0.5:  P(ruin) = [1 - (p/q)^k] / [1 - (p/q)^N]
    For p = 0.5:  P(ruin) = 1 - k/N
    """
    q = 1 - p
    k, N = start, target

    if abs(p - 0.5) < 1e-10:          # fair game
        return 1 - k / N
    else:
        ratio = p / q
        return (1 - ratio**k) / (1 - ratio**N)


# ─────────────────────────────────────────
#  Run
# ─────────────────────────────────────────
WIN_PROBABILITY = float(input("Input Probability of Winning Each Round (e.g. 0.49): "))
print("=" * 52)
print("        GAMBLER'S RUIN SIMULATION")
print("=" * 52)
print(f"  Starting bankroll : ${STARTING_MONEY}")
print(f"  Target            : ${TARGET}")
print(f"  Win probability   : {WIN_PROBABILITY}")
print(f"  Simulations       : {NUM_SIMULATIONS:,}")
print("=" * 52)
print("Running simulations...", end=" ", flush=True)

all_histories  = []
ruin_count     = 0
game_lengths   = []

for _ in range(NUM_SIMULATIONS):
    ruined, history = simulate_game(STARTING_MONEY, TARGET, WIN_PROBABILITY)
    all_histories.append((ruined, history))
    if ruined:
        ruin_count += 1
    game_lengths.append(len(history) - 1)

print("done!\n")

simulated_ruin = ruin_count / NUM_SIMULATIONS
theory_ruin    = theoretical_ruin_probability(STARTING_MONEY, TARGET, WIN_PROBABILITY)

print(f"  Simulated ruin probability  : {simulated_ruin:.4f}  ({ruin_count:,} / {NUM_SIMULATIONS:,})")
print(f"  Theoretical ruin probability: {theory_ruin:.4f}")
print(f"  Average game length         : {np.mean(game_lengths):.1f} rounds")
print(f"  Longest game                : {max(game_lengths):,} rounds")
print()


# ─────────────────────────────────────────
#  Plotting
# ─────────────────────────────────────────
plt.style.use("dark_background")

fig = plt.figure(figsize=(16, 10), facecolor="#060606")
fig.suptitle(
    f"Gambler's Ruin  |  Start=${STARTING_MONEY}  Target=${TARGET}  p={WIN_PROBABILITY}",
    fontsize=16, fontweight="bold", color="white", y=0.98
)

gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.32,
                       left=0.07, right=0.96, top=0.92, bottom=0.08)

ax_paths = fig.add_subplot(gs[:, 0])   # left column: bankroll paths (tall)
ax_bar   = fig.add_subplot(gs[0, 1])   # top-right:   ruin probability bar
ax_hist  = fig.add_subplot(gs[1, 1])   # bottom-right: game length histogram

RUIN_COLOR   = "#ff4d6d"
WIN_COLOR    = "#4ecca3"
THEORY_COLOR = "#f9c74f"
GRID_COLOR   = "#2a2a2a"


# ── Panel 1: Bankroll paths ──────────────────────────────────────────────────
sample = random.sample(all_histories, min(PATHS_TO_PLOT, len(all_histories)))

for ruined, history in sample:
    color = RUIN_COLOR if ruined else WIN_COLOR
    ax_paths.plot(history, color=color, alpha=0.25, linewidth=0.7)

# Draw one bold example path for each outcome
for target_ruin in (True, False):
    candidates = [(r, h) for r, h in sample if r == target_ruin]
    if candidates:
        _, bold_h = max(candidates, key=lambda x: len(x[1]))
        color  = RUIN_COLOR if target_ruin else WIN_COLOR
        label  = "Went broke" if target_ruin else "Hit target"
        ax_paths.plot(bold_h, color=color, alpha=0.9, linewidth=1.8, label=label)

ax_paths.axhline(0,             color=RUIN_COLOR,   linestyle="--", linewidth=1.2, alpha=0.6)
ax_paths.axhline(TARGET,        color=WIN_COLOR,    linestyle="--", linewidth=1.2, alpha=0.6)
ax_paths.axhline(STARTING_MONEY,color="white",      linestyle=":",  linewidth=0.8, alpha=0.4)

ax_paths.set_facecolor("#111111")
ax_paths.set_xlabel("Round",    color="white", fontsize=11)
ax_paths.set_ylabel("Bankroll ($)", color="white", fontsize=11)
ax_paths.set_title(f"Bankroll Over Time\n({PATHS_TO_PLOT} sample paths)", color="white", fontsize=12)
ax_paths.tick_params(colors="white")
ax_paths.grid(True, color=GRID_COLOR, linewidth=0.5)
ax_paths.set_ylim(-5, TARGET + 10)
ax_paths.legend(fontsize=10, loc="upper right",
                facecolor="#1e1e1e", edgecolor="#444", labelcolor="white")
ax_paths.spines[:].set_color("#333")


# ── Panel 2: Ruin probability comparison ────────────────────────────────────
categories = ["Simulated", "Theoretical"]
values     = [simulated_ruin, theory_ruin]
colors     = [RUIN_COLOR, THEORY_COLOR]

bars = ax_bar.bar(categories, values, color=colors, width=0.4,
                  edgecolor="white", linewidth=0.6)
for bar, val in zip(bars, values):
    ax_bar.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{val:.4f}", ha="center", va="bottom",
                color="white", fontsize=12, fontweight="bold")

ax_bar.set_facecolor("#111111")
ax_bar.set_ylim(0, 1.12)
ax_bar.set_title("Ruin Probability", color="white", fontsize=12)
ax_bar.set_ylabel("Probability",     color="white", fontsize=11)
ax_bar.tick_params(colors="white")
ax_bar.grid(True, axis="y", color=GRID_COLOR, linewidth=0.5)
ax_bar.spines[:].set_color("#333")


# ── Panel 3: Game length histogram ──────────────────────────────────────────
ax_hist.hist(game_lengths, bins=50, color="#7b8cde", edgecolor="#0d0d0d",
             linewidth=0.4, alpha=0.85)
ax_hist.axvline(np.mean(game_lengths), color=THEORY_COLOR, linestyle="--",
                linewidth=1.8, label=f"Mean: {np.mean(game_lengths):.0f}")

ax_hist.set_facecolor("#111111")
ax_hist.set_title("Distribution of Game Lengths", color="white", fontsize=12)
ax_hist.set_xlabel("Rounds Played",  color="white", fontsize=11)
ax_hist.set_ylabel("# of Games",     color="white", fontsize=11)
ax_hist.tick_params(colors="white")
ax_hist.grid(True, color=GRID_COLOR, linewidth=0.5)
ax_hist.legend(fontsize=10, facecolor="#1e1e1e",
               edgecolor="#444", labelcolor="white")
ax_hist.spines[:].set_color("#333")


plt.savefig("gamblers_ruin.png",
            dpi=150, bbox_inches="tight", facecolor="#0d0d0d")
print("Graph saved → gamblers_ruin.png  (saved in the same folder as this script)")
plt.show()
