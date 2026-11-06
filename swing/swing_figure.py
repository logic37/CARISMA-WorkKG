"""SWING evaluation with interval (ambiguous) values: scores, ranking and criterion sensitivity.

Values are expert ranges [low, high] on a 0-10 scale, as in interval SMART/SWING.

(a) SWING scores and ranking at the midpoints of the ranges; bar segments = weight x value.
(b) Tornado per criterion: how far the ambiguity in ONE criterion's ranges can move the decision.
    Worst case for the top investment: its value on that criterion at the lower bound, every other
    investment's at the upper bound. Best case: the reverse. All other criteria stay at midpoints.
    Each bar shows the top investment's lead over the strongest rival in that case; below 0 a
    different investment would rank first.
Also prints each investment's score interval (all values at lower / upper bounds) and checks
interval dominance (A dominates B when A's lowest score exceeds B's highest).

Usage: python swing_figure.py [--inputs swing_inputs.json]
Outputs: results/figures/fig_swing_final.png (300 dpi) and .pdf, results/swing_criteria_ranges.csv
"""
import argparse
import csv

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from swing_analysis import HERE, OUT, INK, INK2, MUTED, GRID, CAT, load, scores, rank_of

SHORT = {"Hire OT security engineer": "Hire", "Train OT staff": "Train", "Improve processes": "Process",
         "Outsource monitoring (MSSP)": "MSSP"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default=str(HERE / "swing_inputs.json"))
    args = ap.parse_args()

    crit, pts, alts, lo, hi, worst, best = load(args.inputs)
    A, C = lo.shape
    w = pts / pts.sum()
    mid = (lo + hi) / 2
    base = scores(mid, w, worst, best)
    order = sorted(range(A), key=lambda a: -base[a])
    top = order[0]
    base_rank = [rank_of(base, a) for a in range(A)]
    contrib = 100 * (mid - worst) / (best - worst) * w
    base_lead = base[top] - base[order[1]]
    sh = lambda a: SHORT.get(alts[a], alts[a])

    # ---------------- (b) criterion ranges
    rows = []
    for j, c in enumerate(crit):
        cases = []
        for kind in ("worst", "best"):
            v = mid.copy()
            if kind == "worst":
                v[:, j] = hi[:, j]; v[top, j] = lo[top, j]
            else:
                v[:, j] = lo[:, j]; v[top, j] = hi[top, j]
            s = scores(v, w, worst, best)
            rival = max((a for a in range(A) if a != top), key=lambda a: s[a])
            cases.append(dict(lead=s[top] - s[rival], rival=rival, leader=int(np.argmax(s)), s=s))
        rows.append(dict(j=j, c=c, cases=cases, width=cases[1]["lead"] - cases[0]["lead"]))
    rows.sort(key=lambda r: -r["width"])

    # interval scores and dominance
    s_lo = scores(lo, w, worst, best)
    s_hi = scores(hi, w, worst, best)
    dom = [(alts[a], alts[b]) for a in range(A) for b in range(A) if a != b and s_lo[a] > s_hi[b]]

    # ---------------- figure
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8.5, "axes.labelsize": 7.5,
        "xtick.labelsize": 7, "ytick.labelsize": 7.5, "axes.edgecolor": "#8a8a85", "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    })
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.6, 3.6), gridspec_kw=dict(wspace=0.75))
    for ax in (ax_a, ax_b):
        ax.set_axisbelow(True)

    def title(ax, letter, head, sub):
        ax.set_title(f"({letter}) {head}", loc="left", fontweight="bold", color=INK, pad=20)
        ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=6.8, color=MUTED, va="bottom", ha="left")

    # (a) stacked SWING scores
    for i, a in enumerate(order):
        left = 0.0
        for j in range(C):
            ax_a.barh(i, contrib[a, j], left=left, color=CAT[j], edgecolor="white", lw=0.8, height=0.6)
            left += contrib[a, j]
        ax_a.text(left + 1, i, f"{base[a]:.1f}  (rank {base_rank[a]})", va="center", fontsize=7, color=INK, fontweight="bold")
    ax_a.set_yticks(range(A)); ax_a.set_yticklabels([alts[a] for a in order]); ax_a.invert_yaxis()
    ax_a.set_xlim(0, max(base) + 20)
    ax_a.set_xlabel("SWING score (0–100), midpoints of the expert ranges")
    ax_a.grid(axis="x", color=GRID, lw=0.6)
    ax_a.legend(handles=[Patch(color=CAT[j], label=f"{c} ({w[j]:.2f})") for j, c in enumerate(crit)],
                title="Criterion (weight)", ncol=2, loc="upper center", bbox_to_anchor=(0.38, -0.2),
                frameon=False, fontsize=6.3, title_fontsize=6.5, handlelength=1, columnspacing=1)
    title(ax_a, "a", "SWING scores and ranking", "Bar segments: weight × value for each criterion")

    # (b) tornado per criterion
    LOW, HIGH = "#86b6ef", "#104281"
    n = len(rows)
    for i, r in enumerate(rows):
        wc, bc = r["cases"]
        ax_b.barh(i, wc["lead"] - base_lead, left=base_lead, height=0.55, color=LOW, edgecolor="white", lw=0.5)
        ax_b.barh(i, bc["lead"] - base_lead, left=base_lead, height=0.55, color=HIGH, edgecolor="white", lw=0.5)
        if wc["lead"] < 0:
            wl = f"{sh(wc['leader'])} first"
            col = "#8a3a12"
        else:
            wl = f"vs {sh(wc['rival'])}"
            col = MUTED
        ax_b.text(wc["lead"] - 0.25, i, f"{wc['lead']:+.1f} {wl}".replace("-", "−"), va="center", ha="right", fontsize=6.2, color=col,
                  bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"), zorder=5)
        ax_b.text(bc["lead"] + 0.25, i, f"+{bc['lead']:.1f}", va="center", ha="left", fontsize=6.2, color=MUTED)
    ax_b.axvline(base_lead, color=INK, lw=0.9)
    ax_b.axvline(0, color="#b4541e", lw=0.9, ls=(0, (3, 2)))
    ax_b.text(-0.2, -0.75, "new leader ←", fontsize=6, color="#8a3a12", ha="right", va="center")
    ax_b.set_yticks(range(n)); ax_b.set_yticklabels([r["c"] for r in rows])
    ax_b.set_ylim(n - 0.5, -1.0)
    lo_x = min(r["cases"][0]["lead"] for r in rows); hi_x = max(r["cases"][1]["lead"] for r in rows)
    ax_b.set_xlim(min(lo_x, 0) - 9.5, hi_x + 3)
    ax_b.set_xlabel(f"Lead of “{sh(top)}” over its strongest rival (score points; now {base_lead:.1f})")
    ax_b.grid(axis="x", color=GRID, lw=0.6)
    ax_b.legend(handles=[Patch(color=LOW, label=f"Worst case for {sh(top)} on this criterion"),
                         Patch(color=HIGH, label=f"Best case for {sh(top)} on this criterion")],
                loc="upper center", bbox_to_anchor=(0.3, -0.2), ncol=1, fontsize=6.3, frameon=False, handlelength=1)
    title(ax_b, "b", "Criterion sensitivity to the expert ranges",
          "One criterion's ranges at a time; the others at midpoints")

    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "figures" / "fig_swing_final.png", dpi=300, bbox_inches="tight", pad_inches=0.05)
    fig.savefig(OUT / "figures" / "fig_swing_final.pdf", bbox_inches="tight", pad_inches=0.05)

    with open(OUT / "swing_criteria_ranges.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["criterion", "worst_case_lead", "worst_case_rival_or_new_leader", "best_case_lead", "best_case_rival"])
        for r in rows:
            wc, bc = r["cases"]
            wr.writerow([r["c"], f"{wc['lead']:.2f}", alts[wc["leader"]] if wc["lead"] < 0 else alts[wc["rival"]],
                         f"{bc['lead']:.2f}", alts[bc["rival"]]])
        wr.writerow([])
        wr.writerow(["investment", "score_all_lower_bounds", "score_midpoints", "score_all_upper_bounds"])
        for a in order:
            wr.writerow([alts[a], f"{s_lo[a]:.1f}", f"{base[a]:.1f}", f"{s_hi[a]:.1f}"])

    print(f"top {alts[top]} lead {base_lead:.2f}")
    for r in rows:
        wc, bc = r["cases"]
        print(f"  {r['c']:<20} worst {wc['lead']:+.2f} ({'NEW LEADER ' + alts[wc['leader']] if wc['lead'] < 0 else 'rival ' + alts[wc['rival']]})"
              f"   best {bc['lead']:+.2f} (rival {alts[bc['rival']]})")
    print("score intervals:", "; ".join(f"{alts[a]} [{s_lo[a]:.1f}, {s_hi[a]:.1f}]" for a in order))
    print("interval dominance:", dom or "none")


if __name__ == "__main__":
    main()
