"""SWING multi-criteria evaluation of investment alternatives with a deterministic sensitivity analysis.

SWING weighting
  1. Imagine every criterion at its worst level (0 on the 0-10 scale).
  2. The criterion whose swing from worst to best matters most gets 100 points.
  3. Every other swing is rated relative to it (e.g. 90 points).
  4. weight_i = points_i / sum(points)
  5. score = 100 * sum_i weight_i * (value_i - worst) / (best - worst)        (0-100 scale)

Base case: every value at the midpoint of its expert range.

Sensitivity (deterministic, no random sampling)
  (b) Tornado per investment: its score when ALL its values are at the lower bounds of the expert
      ranges (pessimistic) or at the upper bounds (optimistic), while every other investment keeps
      its base score. The rank shown is the rank it would then take against the base scores in (a).
  Weight check: each criterion's swing points -20% and +20%, all values at midpoints; reports
      whether the ranking changes.

Usage: python swing_analysis.py [--inputs swing_inputs.json]
Outputs: results/swing_worked_example.md/.csv, results/swing_sensitivity.csv,
         results/figures/fig_swing.png (300 dpi) and .pdf
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
INK, INK2, MUTED, GRID = "#1a1a19", "#3d3d3a", "#5c5c57", "#e6e5e0"
# categorical palette, fixed order (validated with the dataviz palette validator)
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]


def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    crit = list(d["criteria_swing_points"])
    pts = np.array([d["criteria_swing_points"][c] for c in crit], float)
    alts = list(d["investments"])
    lo = np.array([[d["investments"][a][c][0] for c in crit] for a in alts], float)
    hi = np.array([[d["investments"][a][c][1] for c in crit] for a in alts], float)
    sc = d["scale"]
    return crit, pts, alts, lo, hi, float(sc["worst"]), float(sc["best"])


def scores(values, w, worst, best):
    return 100 * ((values - worst) / (best - worst)) @ w


def rank_of(s, a):
    """1-based rank of item a in score vector s (ties share the better rank)."""
    return int(np.sum(s > s[a])) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default=str(HERE / "swing_inputs.json"))
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    crit, pts, alts, lo, hi, worst, best = load(args.inputs)
    A, C = lo.shape
    w = pts / pts.sum()
    mid = (lo + hi) / 2
    base = scores(mid, w, worst, best)
    base_rank = [rank_of(base, a) for a in range(A)]
    order = sorted(range(A), key=lambda a: -base[a])
    contrib = 100 * (mid - worst) / (best - worst) * w  # A x C, sums to base

    # ---------------- worked example
    md = ["| Criterion | Swing points | Weight | " + " | ".join(alts) + " |", "|---|---|---|" + "---|" * A]
    for j, c in enumerate(crit):
        md.append(f"| {c} | {pts[j]:g} | {w[j]:.3f} | " +
                  " | ".join(f"{mid[a, j]:g} [{lo[a, j]:g}–{hi[a, j]:g}]" for a in range(A)) + " |")
    md.append(f"| **Score (0–100)** | {pts.sum():g} | 1.000 | " + " | ".join(f"**{base[a]:.1f}**" for a in range(A)) + " |")
    md.append("| **Rank** | | | " + " | ".join(f"**{base_rank[a]}**" for a in range(A)) + " |")
    (OUT / "swing_worked_example.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with open(OUT / "swing_worked_example.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["criterion", "swing_points", "weight"] + alts)
        for j, c in enumerate(crit):
            wr.writerow([c, f"{pts[j]:g}", f"{w[j]:.4f}"] + [f"{mid[a, j]:g}" for a in range(A)])
        wr.writerow(["score", f"{pts.sum():g}", "1"] + [f"{base[a]:.2f}" for a in range(A)])
        wr.writerow(["rank", "", ""] + base_rank)

    # ---------------- tornado per investment (others at base)
    tor = []
    for a in range(A):
        res = []
        for side in (lo, hi):
            v = mid.copy(); v[a] = side[a]
            s = scores(v, w, worst, best)
            res.append((s[a], rank_of(s, a)))
        tor.append((a, res[0], res[1]))
    tor.sort(key=lambda t: t[2][0] - t[1][0])          # widest at the top

    # ---------------- weight check (deterministic)
    wchk = []
    for j, c in enumerate(crit):
        row = [c]
        for f in (0.8, 1.2):
            p2 = pts.copy(); p2[j] *= f
            s = scores(mid, p2 / p2.sum(), worst, best)
            r = sorted(range(A), key=lambda a: -s[a])
            row.append((f, [alts[a] for a in r], r == order, s))
        wchk.append(row)

    # ---------------- figure
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8.5, "axes.labelsize": 7.5,
        "xtick.labelsize": 7, "ytick.labelsize": 7.5, "axes.edgecolor": "#8a8a85", "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    })
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.4, 3.6), sharey=False, gridspec_kw=dict(wspace=0.12))

    def title(ax, letter, head, sub):
        ax.set_title(f"({letter}) {head}", loc="left", fontweight="bold", color=INK, pad=20)
        ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=6.8, color=MUTED, va="bottom", ha="left")

    XMAX = max(t[2][0] for t in tor) + 14
    ax_a.set_axisbelow(True); ax_b.set_axisbelow(True)
    ylab = [f"{alts[a]}" for a in order]
    # (a) stacked contributions
    for i, a in enumerate(order):
        left = 0.0
        for j in range(C):
            ax_a.barh(i, contrib[a, j], left=left, color=CAT[j], edgecolor="white", lw=0.8, height=0.6)
            left += contrib[a, j]
        ax_a.text(left + 1, i, f"{base[a]:.1f}  (rank {base_rank[a]})", va="center", fontsize=7, color=INK, fontweight="bold")
    ax_a.set_yticks(range(A)); ax_a.set_yticklabels(ylab); ax_a.invert_yaxis()
    ax_a.set_xlim(0, XMAX)
    ax_a.set_xlabel("SWING score (0–100), expert midpoints")
    ax_a.grid(axis="x", color=GRID, lw=0.6)
    ax_a.legend(handles=[Patch(color=CAT[j], label=f"{c} ({w[j]:.2f})") for j, c in enumerate(crit)],
                title="Criterion (weight)", ncol=2, loc="upper center", bbox_to_anchor=(0.45, -0.2),
                frameon=False, fontsize=6.3, title_fontsize=6.5, handlelength=1, columnspacing=1)
    title(ax_a, "a", "SWING scores and ranking", "Bar segments: weight × value for each criterion")

    # (b) tornado on the same rows/order as (a)
    LOW, HIGH = "#86b6ef", "#104281"
    for i, a in enumerate(order):
        t = next(t for t in tor if t[0] == a)
        (ls, lr), (hs, hr) = t[1], t[2]
        ax_b.barh(i, base[a] - ls, left=ls, height=0.6, color=LOW, edgecolor="white", lw=0.5)
        ax_b.barh(i, hs - base[a], left=base[a], height=0.6, color=HIGH, edgecolor="white", lw=0.5)
        ax_b.plot([base[a]] * 2, [i - 0.36, i + 0.36], color=INK, lw=1.2)
        ax_b.text(ls - 0.8, i, f"{ls:.1f} · rank {lr}", va="center", ha="right", fontsize=6.4, color=MUTED)
        ax_b.text(hs + 0.8, i, f"{hs:.1f} · rank {hr}", va="center", ha="left", fontsize=6.4, color=MUTED)
    ax_b.set_yticks(range(A)); ax_b.set_yticklabels([]); ax_b.invert_yaxis()
    ax_b.set_xlim(0, XMAX)
    ax_b.set_xlabel("SWING score (0–100)")
    ax_b.grid(axis="x", color=GRID, lw=0.6)
    ax_b.legend(handles=[Patch(color=LOW, label="All its values at the lower bounds (pessimistic)"),
                         Patch(color=HIGH, label="All its values at the upper bounds (optimistic)"),
                         plt.Line2D([], [], color=INK, lw=1.2, label="Base score from (a)")],
                loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=1, fontsize=6.3, frameon=False, handlelength=1.2)
    title(ax_b, "b", "Tornado: how far can each investment move?",
          "One investment at a time; the others keep their base scores")

    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "figures" / "fig_swing.png", dpi=300, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(OUT / "figures" / "fig_swing.pdf", bbox_inches="tight", pad_inches=0.05)

    with open(OUT / "swing_sensitivity.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["investment", "base_score", "base_rank", "pessimistic_score", "pessimistic_rank",
                     "optimistic_score", "optimistic_rank"])
        for a in order:
            t = next(t for t in tor if t[0] == a)
            wr.writerow([alts[a], f"{base[a]:.1f}", base_rank[a], f"{t[1][0]:.1f}", t[1][1], f"{t[2][0]:.1f}", t[2][1]])
        wr.writerow([])
        wr.writerow(["criterion", "points_-20%_ranking", "unchanged", "points_+20%_ranking", "unchanged"])
        for c, lo_r, hi_r in wchk:
            wr.writerow([c, " > ".join(lo_r[1]), lo_r[2], " > ".join(hi_r[1]), hi_r[2]])

    print("weights:", ", ".join(f"{c} {w[j]:.3f}" for j, c in enumerate(crit)))
    print("base:", " > ".join(f"{alts[a]} {base[a]:.1f}" for a in order))
    for a in order:
        t = next(t for t in tor if t[0] == a)
        print(f"  {alts[a]:<28} pessimistic {t[1][0]:.1f} (rank {t[1][1]})   optimistic {t[2][0]:.1f} (rank {t[2][1]})")
    for c, lo_r, hi_r in wchk:
        print(f"  weight {c:<20} -20%: {'same' if lo_r[2] else ' > '.join(lo_r[1])}   "
              f"+20%: {'same' if hi_r[2] else ' > '.join(hi_r[1])}")
        for f, rk, same, s in (lo_r, hi_r):
            print("      ", f, " ".join(f"{alts[a][:12]}={s[a]:.2f}" for a in range(A)))


if __name__ == "__main__":
    main()
