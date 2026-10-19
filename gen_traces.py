"""Generate synthetic page-reference traces (one page number per line) into traces/."""
import numpy as np, os
rng = np.random.default_rng(1)
N = 200_000
os.makedirs("traces", exist_ok=True)

def cyc(order, n=N):            # repeat a page order cyclically
    return np.resize(np.asarray(order), n)

def zipf(n, pages=20000, space=100000, off=0):
    p = 1 / np.arange(1, pages + 1); p /= p.sum()
    mapping = rng.permutation(space)[:pages] + off
    return mapping[rng.choice(pages, n, p=p)]

def seq(n=N, off=0):    return np.arange(n) % 30000 + off
def stride(n=N, off=0): return (np.arange(n) * 7) % 50000 + off

def noisy():
    base = cyc(rng.choice(100000, 2000, replace=False))
    m = rng.random(N) < 0.10
    base[m] = rng.integers(0, 100000, m.sum())
    return base

def matmul(n=1024, iters=100_000):   # naive i-j-k loop, doubles: A row-major, B column walk
    idx = np.arange(iters); k = idx % n; j = (idx // n) % n; i = idx // (n * n)
    a = (i * n + k) * 8 // 4096; b = n * n * 8 // 4096 + (k * n + j) * 8 // 4096
    t = np.empty(2 * iters, dtype=np.int64); t[0::2] = a; t[1::2] = b
    return t[np.r_[True, np.diff(t) != 0]]   # collapse consecutive same-page refs

def phases():
    q = N // 4
    return np.concatenate([seq(q, 200000), zipf(q, 20000, 100000, 0),
                           cyc(rng.choice(100000, 5000, replace=False) + 500000, q), stride(q, 700000)])

W = {"seq": seq(), "stride": stride(), "loop": cyc(rng.choice(10000, 600, replace=False)),
     "ptrchase": cyc(rng.choice(100000, 5000, replace=False)), "noisy": noisy(),
     "zipf": zipf(N), "matmul": matmul(), "phases": phases()}
for sd in range(5):                      # seeded repeats of the random-ish workloads
    rng = np.random.default_rng(100 + sd)
    W[f"zipf_s{sd}"] = zipf(N)
    W[f"noisy_s{sd}"] = noisy()
for name, t in W.items():
    assert t.min() >= 0 and t.max() < 2**21
    np.savetxt(f"traces/{name}.txt", t, fmt="%d")
    print(f"{name:9s} {len(t):7d} refs  {len(set(t.tolist())):6d} distinct pages")
