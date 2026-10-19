#!/bin/sh
# Re-creates traces/real_matmul.txt and traces/real_bfs.txt (page numbers, rank-compressed with gaps clipped to 4096 pages).
set -e
run() { valgrind --tool=lackey --trace-mem=yes ./progs $1 2>&1 >/dev/null | ./filter $2 200000 > raw_$3.txt; }
run "mm 384" 450000 real_matmul
run "bfs 100000 300000" 1200000 real_bfs
python - <<'PY'
import numpy as np
for nm in ("real_matmul", "real_bfs"):
    r = np.loadtxt(f"raw_{nm}.txt", dtype=np.int64); u = np.unique(r)
    gaps = np.minimum(np.diff(u, prepend=u[0]), 4096); gaps[0] = 0
    m = dict(zip(u.tolist(), np.cumsum(gaps).tolist()))
    np.savetxt(f"../traces/{nm}.txt", np.array([m[x] for x in r.tolist()]), fmt="%d")
PY
