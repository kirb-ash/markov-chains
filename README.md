# Markov Prefetching: when does it pay off?

OS mini project (P11, intelligent memory prefetching). A trace-driven demand-paging simulator in C that compares
no prefetch, next-page, stride and order-1..3 Markov predictors (page or delta state), plus an adaptive throttle,
on synthetic and real (valgrind) page-reference traces, and relates the benefit to each trace's conditional entropy.

## Reproduce everything
```bash
pip install numpy pandas matplotlib pillow
make all          # build sim.c, generate traces, run all experiments, make figures + paper/paper.md
```
All random seeds are fixed, so results are identical on every run. About a minute on a laptop.

## Layout
| Path | What |
|---|---|
| `sim.c` | the simulator: LRU frames, prefetch policies, Markov table, adaptive throttle. One CSV line per run |
| `gen_traces.py` | synthetic workloads -> `traces/*.txt` (one page number per line) |
| `traces/real_*.txt` | real traces captured with valgrind (see `realtrace/`, `make realtraces`; needs valgrind) |
| `run_experiments.py` | runs the sweeps (policies, frames, table size, seeds) -> `results/*.csv` |
| `analyze.py` | entropy analysis + figures 1-6 -> `figures/` |
| `make_paper.py`, `paper/template.md` | fills the paper with numbers computed from the CSVs -> `paper/paper.md` |

Run the simulator directly:
```bash
./sim -i traces/matmul.txt -p markov -s delta -k 2 -d 2 -a 1 -f 256
# -p none|next|stride|markov  -s page|delta  -k order 1..3  -d degree  -t threshold  -a adaptive 0|1  -T table bits  -f frames
```
Output columns: policy,state,k,deg,thr,adapt,tbits,frames,refs,faults,issued,useful,useless
