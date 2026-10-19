"""Entropy analysis + all paper figures. Reads results/*.csv and traces/*.txt, writes figures/*.png and results/summary.csv."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict
from math import log2

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
COL = {"none": "#8a8985", "next": "#2a78d6", "stride": "#eb6834", "mk-page-k1": "#1baf7a", "mk-delta-k2": "#6250d6",
       "mk-page-k2": "#e87ba4", "mk-delta-k1": "#2a78d6", "mk-delta-k3": "#eda100"}
LBL = {"none": "no prefetch", "next": "next-page", "stride": "stride", "mk-page-k1": "Markov (page, k=1)",
       "mk-delta-k2": "Markov (delta, k=2)", "mk-delta-k2-d2": "aggressive", "mk-delta-k2-ad": "adaptive throttle",
       "mk-page-k1-d2": "aggressive", "mk-page-k1-ad": "adaptive throttle"}
MK = {"none": "o", "next": "s", "stride": "^", "mk-page-k1": "D", "mk-delta-k2": "v"}
BASE = ["seq", "stride", "loop", "ptrchase", "matmul", "noisy", "zipf", "phases", "real_matmul", "real_bfs"]
REAL = ["real_matmul", "real_bfs"]

def style(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9); ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    ax.xaxis.label.set_color(MUTED); ax.yaxis.label.set_color(MUTED); ax.title.set_color(INK)

def load(p):
    d = pd.read_csv(p); d["fr"] = d.faults / d.refs; d["wasted"] = (d.issued - d.useful) / d.refs; return d

main, seeds, frames, tsz = load("results/main.csv"), load("results/seeds.csv"), load("results/frames.csv"), load("results/tablesize.csv")

# ---------- Fig 1: fault rate by policy ----------
cfgs = ["none", "next", "stride", "mk-page-k1", "mk-delta-k2"]
fig, ax = plt.subplots(figsize=(11, 3.9)); w = 0.16; x = np.arange(len(BASE))
for i, c in enumerate(cfgs):
    v = [main[(main.workload == b) & (main.config == c)].fr.iloc[0] for b in BASE]
    ax.bar(x + (i - 2) * (w + 0.01), v, w, color=COL[c], label=LBL[c], hatch=["", "", "//", "", "xx"][i], edgecolor="white", lw=0.6)
ax.set_xticks(x); ax.set_xticklabels(BASE, fontsize=8); ax.set_ylabel("page-fault rate (faults / reference)"); ax.set_ylim(0, 1.05)
ax.set_title("Fault rate by policy (256 frames, LRU)", loc="left", fontsize=11)
ax.legend(ncol=5, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12)); style(ax)
fig.savefig("figures/fig1_policies.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------- Fig 2: frame sweep (small multiples) ----------
fig, axs = plt.subplots(2, 5, figsize=(13.5, 5), sharey=True)
for ax, b in zip(axs.flat, BASE):
    for c in cfgs:
        d = frames[(frames.workload == b) & (frames.config == c)].sort_values("frames")
        ax.plot(d.frames, d.fr, color=COL[c], marker=MK[c], ms=4, lw=1.5, label=LBL[c])
    ax.set_xscale("log", base=2); ax.set_title(b, fontsize=10, loc="left"); style(ax); ax.set_ylim(-0.02, 1.15)
for ax in axs[1]: ax.set_xlabel("frames")
for ax in axs[:, 0]: ax.set_ylabel("fault rate")
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h, l, ncol=5, frameon=False, fontsize=9, loc="lower center", bbox_to_anchor=(0.5, -0.03))
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig("figures/fig2_frames.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------- Fig 3: adaptive throttle ----------
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
for ax, (a, b_), ttl in zip(axs, [("mk-page-k1-d2", "mk-page-k1-ad"), ("mk-delta-k2-d2", "mk-delta-k2-ad")], ["page state, k=1, degree 2", "delta state, k=2, degree 2"]):
    for j, (c, col, hz) in enumerate([(a, "#eb6834", "//"), (b_, "#2a78d6", "")]):
        v = [main[(main.workload == wl) & (main.config == c)].wasted.iloc[0] for wl in BASE]
        ax.bar(np.arange(len(BASE)) + (j - 0.5) * 0.38, v, 0.36, color=col, hatch=hz, edgecolor="white", label=LBL[c])
    ax.set_xticks(range(len(BASE))); ax.set_xticklabels(BASE, rotation=30, ha="right"); ax.set_title(ttl, loc="left", fontsize=10); style(ax)
axs[0].set_ylabel("wasted prefetches per reference"); axs[0].legend(frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig("figures/fig3_throttle.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------- Fig 4: order / state heatmap ----------
oc = ["none", "next", "mk-page-k1", "mk-page-k2", "mk-delta-k1", "mk-delta-k2", "mk-delta-k3"]
M = np.array([[main[(main.workload == b) & (main.config == c)].fr.iloc[0] for c in oc] for b in BASE])
fig, ax = plt.subplots(figsize=(8, 5)); im = ax.imshow(M, cmap="Blues", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(oc))); ax.set_xticklabels(["none", "next", "page k1", "page k2", "delta k1", "delta k2", "delta k3"], fontsize=9, color=MUTED)
ax.set_yticks(range(len(BASE))); ax.set_yticklabels(BASE, fontsize=9, color=MUTED)
for i in range(M.shape[0]):
    for j in range(M.shape[1]): ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=8, color="white" if M[i, j] > 0.55 else INK)
for s in ax.spines.values(): s.set_visible(False)
ax.set_title("Fault rate by predictor state and order (darker = more faults)", loc="left", fontsize=11, color=INK)
fig.savefig("figures/fig4_order.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------- Fig 5: table size ----------
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
sel = [("seq", "#2a78d6", "o"), ("loop", "#eb6834", "s"), ("ptrchase", "#1baf7a", "^"), ("noisy", "#6250d6", "v")]
for ax, c, ttl in zip(axs, ["mk-page-k1", "mk-delta-k2"], ["page state (one entry per page)", "delta state (one entry per delta pattern)"]):
    for wl, col, m in sel:
        d = tsz[(tsz.workload == wl) & (tsz.config == c)].sort_values("tbits")
        ax.plot(d.tbits, d.fr, color=col, marker=m, ms=5, lw=1.5, label=wl)
    ax.set_title(ttl, loc="left", fontsize=10); ax.set_xlabel("table size (log2 entries)"); style(ax)
axs[0].set_ylabel("fault rate"); axs[0].legend(frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig("figures/fig5_tablesize.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------- Entropy: prequential conditional entropy of each trace ----------
def preq(seq, k, lam=0.5):
    V = len(set(seq)); uni = defaultdict(int); cc = defaultdict(int); pc = defaultdict(int); bits = 0.0
    for t, y in enumerate(seq):
        pu = (uni[y] + 1) / (t + V)
        if t >= k:
            ctx = tuple(seq[t - k:t]); p = (pc[(ctx, y)] + lam * pu) / (cc[ctx] + lam)
            cc[ctx] += 1; pc[(ctx, y)] += 1
        else: p = pu
        uni[y] += 1; bits -= log2(p)
    return bits / len(seq)

rows = []
names = BASE + [f"{w}_s{i}" for w in ("zipf", "noisy") for i in range(5)]
for nm in names:
    pg = np.loadtxt(f"traces/{nm}.txt", dtype=int).tolist(); dl = np.diff(pg).tolist()
    H = {"page_k1": preq(pg, 1), "page_k2": preq(pg, 2), "delta_k1": preq(dl, 1), "delta_k2": preq(dl, 2)}
    src = main if nm in BASE else seeds
    g = src[(src.workload == nm)].set_index("config")
    best_cfg = g.loc[["mk-page-k1", "mk-page-k2", "mk-delta-k1", "mk-delta-k2", "mk-delta-k3"]].fr.idxmin()
    rows.append(dict(workload=nm, **H, H_min=min(H.values()), best_cfg=best_cfg, fr_none=g.loc["none"].fr,
                     fr_best=g.loc[best_cfg].fr, fr_next=g.loc["next"].fr))
E = pd.DataFrame(rows); E["reduction"] = 1 - E.fr_best / E.fr_none; E.to_csv("results/summary.csv", index=False)
rho = E.H_min.rank().corr(E.reduction.rank())
rho_main = E[E.workload.isin(BASE)].H_min.rank().corr(E[E.workload.isin(BASE)].reduction.rank())
print(E.round(3).to_string()); print(f"\nSpearman(H_min, reduction): all {len(E)} traces {rho:.3f}; {len(BASE)} distinct workloads {rho_main:.3f}")

# ---------- Fig 6: entropy vs benefit ----------
fig, ax = plt.subplots(figsize=(7, 4.8))
sd = E[~E.workload.isin(BASE)]; bs = E[E.workload.isin(BASE) & ~E.workload.isin(REAL)]; rl = E[E.workload.isin(REAL)]
ax.scatter(sd.H_min, sd.reduction, s=18, color="#8a8985", label="seeded repeats (zipf, noisy)")
ax.scatter(bs.H_min, bs.reduction, s=48, color="#2a78d6", edgecolor="white", lw=1.2, label="synthetic workloads", zorder=3)
ax.scatter(rl.H_min, rl.reduction, s=56, color="#eb6834", marker="D", edgecolor="white", lw=1.2, label="real traces (valgrind)", zorder=3)
off = {"seq": (6, 10), "stride": (8, -2), "loop": (8, -14), "ptrchase": (8, -22), "matmul": (-6, 14), "noisy": (-4, 10),
       "zipf": (-30, 10), "phases": (6, 8), "real_matmul": (8, 6), "real_bfs": (-62, -16)}
for _, r in pd.concat([bs, rl]).iterrows():
    ax.annotate(r.workload, (r.H_min, r.reduction), xytext=off.get(r.workload, (6, 6)), textcoords="offset points", fontsize=8, color=INK,
                arrowprops=dict(arrowstyle="-", color=GRID, lw=0.8))
ax.set_xscale("symlog", linthresh=0.1); ax.set_xlim(-0.005, 30)
ax.set_xticks([0.01, 0.1, 1, 10]); ax.set_xticklabels(["0.01", "0.1", "1", "10"])
ax.axhline(0, color=GRID, lw=1)
ax.set_xlabel("prequential conditional entropy, best of 4 models (bits / reference, symlog)"); ax.set_ylabel("fault reduction of best Markov predictor\n(negative = worse than no prefetch)")
ax.set_title(f"Entropy predicts prefetch benefit (Spearman {rho:.2f}, n={len(E)})", loc="left", fontsize=10); style(ax)
ax.legend(frameon=False, fontsize=8, loc="lower left")
fig.savefig("figures/fig6_entropy.png", dpi=200, bbox_inches="tight"); plt.close(fig)
