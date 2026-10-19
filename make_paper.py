"""Fill paper/template.md with numbers computed from results/*.csv -> paper/paper.md (so no number is typed by hand)."""
import pandas as pd
def load(p):
    d = pd.read_csv(p); d["fr"] = d.faults / d.refs; d["wasted"] = (d.issued - d.useful) / d.refs; d["acc"] = d.useful / d.issued.where(d.issued > 0); return d
m, s, t, e = load("results/main.csv"), load("results/seeds.csv"), load("results/tablesize.csv"), pd.read_csv("results/summary.csv")
g = lambda wl, c, col="fr": m[(m.workload == wl) & (m.config == c)][col].iloc[0]
WL = ["seq", "stride", "loop", "ptrchase", "matmul", "noisy", "zipf", "phases", "real_matmul", "real_bfs"]
C1 = [("none", "none"), ("next", "next-page"), ("stride", "stride"), ("mk-page-k1", "Markov page k=1"), ("mk-page-k2", "Markov page k=2"),
      ("mk-delta-k1", "Markov delta k=1"), ("mk-delta-k2", "Markov delta k=2"), ("mk-delta-k3", "Markov delta k=3")]
t1 = "| workload | " + " | ".join(n for _, n in C1) + " |\n|---|" + "---|" * len(C1) + "\n"
for w in WL:
    vals = [g(w, c) for c, _ in C1]; lo = min(vals)
    t1 += f"| {w} | " + " | ".join((f"**{v:.3f}**" if abs(v - lo) < 1e-9 else f"{v:.3f}") for v in vals) + " |\n"
t2 = "| workload | aggressive: wasted/ref | adaptive: wasted/ref | aggressive: fault rate | adaptive: fault rate |\n|---|---|---|---|---|\n"
for w in WL:
    t2 += f"| {w} | {g(w,'mk-page-k1-d2','wasted'):.3f} | {g(w,'mk-page-k1-ad','wasted'):.3f} | {g(w,'mk-page-k1-d2'):.3f} | {g(w,'mk-page-k1-ad'):.3f} |\n"
t3 = "| workload | best model entropy (bits/ref) | best Markov config | fault rate: none | fault rate: best Markov | reduction |\n|---|---|---|---|---|---|\n"
for _, r in e[e.workload.isin(WL)].iterrows():
    t3 += f"| {r.workload} | {r.H_min:.3f} | {r.best_cfg} | {r.fr_none:.3f} | {r.fr_best:.3f} | {r.reduction:.3f} |\n"
sd = s[s.config == "none"].groupby(s.workload.str.split("_").str[0]).fr.agg(["mean", "std"])
rk = e.H_min.rank().corr(e.reduction.rank()); rk10 = e[e.workload.isin(WL)].H_min.rank().corr(e[e.workload.isin(WL)].reduction.rank())
tb = lambda wl, c, b: t[(t.workload == wl) & (t.config == c) & (t.tbits == b)].fr.iloc[0]
N = dict(T1=t1, T2=t2, T3=t3, RHO=f"{rk:.2f}", RHO10=f"{rk10:.2f}", NTR=str(len(e)),
         ZN=f"{g('zipf','none'):.3f}", ZX=f"{g('zipf','next'):.3f}",
         ZWA=f"{g('zipf','mk-page-k1-d2','wasted'):.3f}", ZWD=f"{g('zipf','mk-page-k1-ad','wasted'):.3f}",
         NWA=f"{g('noisy','mk-page-k1-d2','wasted'):.3f}", NWD=f"{g('noisy','mk-page-k1-ad','wasted'):.3f}",
         SEQP=f"{g('seq','mk-page-k1'):.3f}", SEQD=f"{g('seq','mk-delta-k1'):.3f}",
         SEQ16=f"{tb('seq','mk-page-k1',16):.3f}", SEQ18=f"{tb('seq','mk-page-k1',18):.3f}", SEQ8D=f"{tb('seq','mk-delta-k2',8):.3f}",
         MMP1=f"{g('matmul','mk-page-k1'):.3f}", MMP2=f"{g('matmul','mk-page-k2'):.3f}",
         RMN=f"{g('real_matmul','none'):.3f}", RMX=f"{g('real_matmul','next'):.3f}", RMD=f"{g('real_matmul','mk-delta-k1'):.3f}",
         RBN=f"{g('real_bfs','none'):.3f}", RBX=f"{g('real_bfs','next'):.3f}", RBM=f"{g('real_bfs','mk-delta-k2'):.3f}",
         RBAD=f"{g('real_bfs','mk-delta-k2-ad'):.3f}", RBAG=f"{g('real_bfs','mk-delta-k2-d2'):.3f}",
         NZS=f"{sd.loc['noisy','std']:.4f}", ZZS=f"{sd.loc['zipf','std']:.4f}")
txt = open("paper/template.md").read()
for k, v in N.items(): txt = txt.replace("{{" + k + "}}", v)
assert "{{" not in txt, [l for l in txt.splitlines() if "{{" in l]
open("paper/paper.md", "w").write(txt); print("paper/paper.md written")
