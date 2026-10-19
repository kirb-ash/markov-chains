"""Run every experiment through ./sim in parallel and write results/*.csv"""
import subprocess, itertools, csv, os
from concurrent.futures import ThreadPoolExecutor

BASE = ["seq", "stride", "loop", "ptrchase", "noisy", "zipf", "matmul", "phases", "real_matmul", "real_bfs"]
SEEDED = [f"{w}_s{i}" for w in ("zipf", "noisy") for i in range(5)]
CFG = {   # name -> sim args
    "none":            ["-p", "none"],
    "next":            ["-p", "next"],
    "stride":          ["-p", "stride", "-d", "1"],
    "mk-page-k1":      ["-p", "markov", "-s", "page", "-k", "1"],
    "mk-page-k2":      ["-p", "markov", "-s", "page", "-k", "2"],
    "mk-delta-k1":     ["-p", "markov", "-s", "delta", "-k", "1"],
    "mk-delta-k2":     ["-p", "markov", "-s", "delta", "-k", "2"],
    "mk-delta-k3":     ["-p", "markov", "-s", "delta", "-k", "3"],
    "mk-delta-k2-d2":  ["-p", "markov", "-s", "delta", "-k", "2", "-d", "2", "-t", "0"],
    "mk-delta-k2-ad":  ["-p", "markov", "-s", "delta", "-k", "2", "-d", "2", "-a", "1"],
    "mk-page-k1-d2":   ["-p", "markov", "-s", "page", "-k", "1", "-d", "2", "-t", "0"],
    "mk-page-k1-ad":   ["-p", "markov", "-s", "page", "-k", "1", "-d", "2", "-a", "1"],
}
HDR = ["workload", "config", "policy", "state", "k", "deg", "thr", "adapt", "tbits", "frames",
       "refs", "faults", "issued", "useful", "useless"]

def run(job):
    wl, name, extra = job
    args = CFG[name] + extra
    if "-T" not in args: args += ["-T", "16"]
    if "-f" not in args: args += ["-f", "256"]
    out = subprocess.run(["./sim", "-i", f"traces/{wl}.txt"] + args, capture_output=True, text=True, check=True).stdout.strip()
    return [wl, name] + out.split(",")

def go(jobs, path):
    with ThreadPoolExecutor(8) as ex: rows = list(ex.map(run, jobs))
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(HDR); w.writerows(rows)
    print(path, len(rows), "runs")

os.makedirs("results", exist_ok=True)
go([(w, n, []) for w in BASE for n in CFG], "results/main.csv")
go([(w, n, []) for w in SEEDED for n in CFG], "results/seeds.csv")
FS = ["none", "next", "stride", "mk-page-k1", "mk-delta-k2", "mk-delta-k2-ad"]
go([(w, n, ["-f", str(f)]) for w in BASE for n in FS for f in (32, 64, 128, 256, 512, 1024, 2048)], "results/frames.csv")
go([(w, n, ["-T", str(t)]) for w in BASE for n in ("mk-page-k1", "mk-delta-k2") for t in (8, 10, 12, 14, 16, 18)], "results/tablesize.csv")
