"""
Figure 2 -- F1 Detection-Action Gap
Two-panel figure for the EMNLP paper.

Run:
    python scripts/figure2_f1_gap.py

Outputs:
    paper/figure2_f1_gap.pdf
    paper/figure2_f1_gap.png

Data provenance (all from agent/logs/v2/dr_judge_f1.py output, 2026-05-24):
  Left panel  -- LLM-judge primary DR (GPT-4o-mini), 4-model pool, reached_trap=1.
  Right panel -- per-model + Pooled-of-4 F1 gap at C3, reached_trap=1.
  CI half-widths: 1.96 * sqrt(se_DR1^2 + se_DR0^2), propagated from
  cell-level proportions. Replace with GLMM Wald CIs from paper_tables.ipynb
  when available.

Model pool: Claude Haiku 4.5 (5 seeds), Gemini 3 Flash (5 seeds),
            Llama 4 Scout (5 seeds), GPT-5 mini (5 seeds).
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D

os.makedirs("paper", exist_ok=True)

# ---- Colour palette -------------------------------------------------------
COL_DR1    = "#1a365d"   # dark navy  -- DR=1 bars
COL_DR0    = "#bee3f8"   # pale blue  -- DR=0 bars
COL_HL     = "#c53030"   # red        -- C3 callout + powered Pooled row
COL_UNPWR  = "#2b6cb0"   # blue       -- underpowered per-model rows
COL_GRID   = "#e8edf2"
COL_SPINE  = "#cbd5e0"

plt.rcParams.update({
    "font.family":      "sans-serif",
    "axes.titlepad":    10,
    "axes.labelcolor":  "#2d3748",
    "xtick.color":      "#4a5568",
    "ytick.color":      "#4a5568",
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.8),
                                gridspec_kw={"width_ratios": [1.1, 1]})
fig.subplots_adjust(wspace=0.40, top=0.88, bottom=0.18)

# =============================================================================
# LEFT PANEL -- grouped bar chart: PLR_crit by DR x condition
# Pooled-of-4 (Haiku 4.5 + Gemini 3 Flash + Llama 4 Scout + GPT-5 mini)
# LLM-judge primary DR (GPT-4o-mini), reached_trap = True
# =============================================================================

conditions = ["C0",  "C1",  "C2",  "C3" ]
dr1_vals   = [ 6.8,  22.9,  30.0,  35.9]   # PLR_crit % for DR=1 group
dr0_vals   = [82.5,  74.0,  69.4,  66.1]   # PLR_crit % for DR=0 group
n_dr1      = [  88,   140,   257,   462]   # n(DR=1) per condition

x     = np.arange(4)
width = 0.34

ax1.bar(x - width/2, dr1_vals, width,
        label="DR=1  (judge-confirmed detection)",
        color=COL_DR1, zorder=3, linewidth=0)
ax1.bar(x + width/2, dr0_vals, width,
        label="DR=0  (no detection)",
        color=COL_DR0, edgecolor="#90cdf4", linewidth=0.6, zorder=3)

# ---- Axis formatting -------------------------------------------------------
ax1.set_ylim(0, 128)
ax1.set_ylabel("PLR_crit (%)", fontsize=11, labelpad=6)
ax1.set_xticks(x)
ax1.set_xticklabels(conditions, fontsize=12, fontweight="bold")
ax1.yaxis.set_major_locator(ticker.MultipleLocator(20))
ax1.yaxis.grid(True, color=COL_GRID, zorder=0, linewidth=0.9)
ax1.set_axisbelow(True)
for sp in ["top", "right"]:
    ax1.spines[sp].set_visible(False)
for sp in ["left", "bottom"]:
    ax1.spines[sp].set_color(COL_SPINE)

ax1.legend(fontsize=8.5, loc="upper left", framealpha=0.95,
           edgecolor=COL_SPINE, fancybox=False, borderpad=0.7)

# ---- n_DR=1 labels below condition labels ----------------------------------
for xi, n in zip(x, n_dr1):
    ax1.text(xi, -11, f"$n_{{\\rm DR=1}}={n}$",
             ha="center", va="top", fontsize=8, color="#555")

# ---- Gap annotation on C3 (double-headed arrow) ----------------------------
c3x       = x[3]
y_top_dr1 = dr1_vals[3]   # 35.9
y_top_dr0 = dr0_vals[3]   # 66.1
arr_x     = c3x + width/2 + 0.13

ax1.annotate("",
    xy=(arr_x, y_top_dr0), xytext=(arr_x, y_top_dr1),
    arrowprops=dict(arrowstyle="<->", color=COL_HL, lw=2.0, mutation_scale=14))
ax1.text(arr_x + 0.08, (y_top_dr1 + y_top_dr0) / 2,
         "30.2 pp", color=COL_HL, fontsize=10, fontweight="bold", va="center")

# ---- Bracket + "primary F1" label above C3 ---------------------------------
bk_y  = 115
bk_x0 = c3x - width/2 - 0.04
bk_x1 = c3x + width/2 + 0.04
tdrop = 3.0

for bx in [bk_x0, bk_x1]:
    ax1.plot([bx, bx], [bk_y - tdrop, bk_y],
             color=COL_HL, lw=1.6, clip_on=False, zorder=5)
ax1.plot([bk_x0, bk_x1], [bk_y, bk_y],
         color=COL_HL, lw=1.6, clip_on=False, zorder=5)
ax1.text(c3x, bk_y + 1.8,
         "primary F1  (analysis-plan S4)",
         ha="center", va="bottom", fontsize=8.5,
         color=COL_HL, fontweight="bold", clip_on=False)

ax1.set_title("Detection-Action Gap Across Conditions",
              fontsize=11, fontweight="bold")
ax1.text(0.5, -0.205,
    "Pooled: Haiku 4.5 · Gemini 3 Flash · Llama 4 Scout · GPT-5 mini"
    "  |  reached_trap = True",
    ha="center", va="center", transform=ax1.transAxes,
    fontsize=8, color="#666", style="italic")

# =============================================================================
# RIGHT PANEL -- forest / dot plot: per-model F1 gap at C3
# LLM-judge primary DR (GPT-4o-mini), reached_trap = True
# =============================================================================

# Rows ordered top-to-bottom by gap size (Llama largest -> Gemini smallest)
# y=4 Llama, y=3 Pooled-of-4, y=2 Haiku, y=1 GPT-5 mini, y=0 Gemini
model_labels = [
    "Llama 4 Scout",
    "Pooled-of-4",
    "Claude Haiku 4.5",
    "GPT-5 mini",
    "Gemini 3 Flash",
]
gaps    = [38.3, 30.2, 21.1, 19.4, 17.2]
n_vals  = [  70,  462,  122,  167,  103]
ci_h    = [12.2,   5.2,  9.5,  9.9, 10.9]   # 1.96*sqrt(se_DR1^2+se_DR0^2)
powered = [False, True, False, False, False]  # Pooled-of-4 is the only primary cell

y_pos = [4, 3, 2, 1, 0]

# Light alternating row bands
for yi in y_pos:
    ax2.axhspan(yi - 0.45, yi + 0.45,
                color="#f7fafc" if yi % 2 == 0 else "white", zorder=0)

ax2.axvline(0, color=COL_SPINE, lw=0.9, zorder=1)

for yi, gap, n, ci, pwr in zip(y_pos, gaps, n_vals, ci_h, powered):
    col = COL_HL if pwr else COL_UNPWR
    sym = "star" if pwr else "circle"

    # Error bar
    ax2.errorbar(gap, yi, xerr=ci, fmt="none",
                 color=col, capsize=5, capthick=1.8, lw=1.8, zorder=3)

    # Marker
    if pwr:
        ax2.plot(gap, yi, marker="*", color=COL_HL, markersize=17, zorder=4,
                 markeredgecolor="white", markeredgewidth=0.4)
    else:
        ax2.plot(gap, yi, marker="o", color=COL_UNPWR, markersize=10, zorder=4,
                 markeredgecolor="white", markeredgewidth=0.8)

    # n label to right
    sym_char = "★" if pwr else "○"   # filled star / open circle
    ax2.text(gap + ci + 1.8, yi,
             f"{sym_char}  n={n}",
             va="center", ha="left", fontsize=9,
             color=col, fontweight="bold" if pwr else "normal")

# ---- Axis formatting -------------------------------------------------------
ax2.set_xlim(-2, 68)
ax2.set_ylim(-0.65, 4.65)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(model_labels, fontsize=10)
ax2.set_xlabel("Detection-Action Gap (pp)", fontsize=11, labelpad=6)
ax2.xaxis.set_major_locator(ticker.MultipleLocator(10))
ax2.xaxis.grid(True, color=COL_GRID, zorder=0, linewidth=0.9)
ax2.set_axisbelow(True)
for sp in ["top", "right"]:
    ax2.spines[sp].set_visible(False)
for sp in ["left", "bottom"]:
    ax2.spines[sp].set_color(COL_SPINE)

ax2.set_title("Per-Model F1 Gap at C3",
              fontsize=11, fontweight="bold")
ax2.text(0.5, -0.145,
    "reached_trap = True  |  ★ clears n ≥ 200 power guard (analysis-plan S8)",
    ha="center", va="center", transform=ax2.transAxes,
    fontsize=8, color="#666", style="italic")

# ---- Legend with actual dot/star markers -----------------------------------
legend_elems = [
    Line2D([0], [0], marker="*", color="w", markerfacecolor=COL_HL,
           markersize=10, label="★  n ≥ 200 — primary inference"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=COL_UNPWR,
           markersize=7,  label="○  n < 200 — descriptive-with-CI"),
]
ax2.legend(handles=legend_elems, fontsize=7.5,
           loc="lower right",
           framealpha=0.93, edgecolor=COL_SPINE, fancybox=False,
           borderpad=0.35, labelspacing=0.25, handletextpad=0.4,
           handlelength=1.2)

# =============================================================================
# Overall title
# =============================================================================
fig.suptitle("Figure 2 -- F1: Detection-Action Gap",
             fontsize=12, fontweight="bold", y=0.98)

plt.savefig("paper/figure2_f1_gap.pdf", bbox_inches="tight", dpi=300)
plt.savefig("paper/figure2_f1_gap.png", bbox_inches="tight", dpi=300)
print("Saved -> paper/figure2_f1_gap.pdf  +  .png")
plt.show()
