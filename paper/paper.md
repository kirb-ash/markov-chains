# When Does Markov Prefetching Pay Off? An Entropy-Based Study with an Adaptive Throttle

**Authors:** Pala Gaurav Reddy (PES1UG25AM254) and Punith VC (PES1UG25AM295) · PES University, Bengaluru · UE25CS242A Operating Systems mini project (P11)

## Abstract

Demand paging stalls a process on every page fault, and prefetching tries to hide that cost by loading pages before they are referenced. A Markov predictor learns which page (or page delta) tends to follow the recent history and prefetches the most likely successors. We built a trace-driven demand-paging simulator in C and compared no prefetching, next-page, stride and order-1 to 3 Markov predictors (page-state and delta-state) on 20 traces: eight synthetic workloads, seeded repeats of the two random ones, and two real traces captured with valgrind. We find that (i) the benefit of Markov prefetching tracks the conditional entropy of the trace (Spearman -0.89 over all 20 traces) and vanishes on high-entropy workloads; (ii) naive prefetching is actively harmful there (next-page raises the zipf fault rate from 0.542 to 0.615); (iii) delta states need a tiny table while page states need one entry per page; and (iv) a simple accuracy-driven throttle removes most wasted prefetches at essentially no cost in faults. This is a simulation study: there is no timing model, and the real-trace evidence rests on two programs.

## 1. Introduction

A page fault costs orders of magnitude more than a memory access, so anything that converts faults into prefetch hits is valuable, but a wrong prefetch wastes I/O and evicts a useful page. The question this project asks is not "does Markov prefetching work" (it can) but **when**, and how to stop it from hurting when it does not. Our contributions:

1. A reproducible C simulator and workload suite for comparing prefetchers under LRU replacement.
2. An empirical link between the entropy of a trace's reference stream and the benefit of a Markov predictor.
3. A small adaptive throttle, with an evaluation of what it saves and what it costs.

We do not claim Markov prefetching itself is new; see Section 2.

## 2. Background and related work

**Scope and search method.** This is a targeted, not a systematic, literature review. We started from the two classic works that our method rests on (Joseph and Grunwald; Vitter and Krishnan), followed their citations and later papers that cite them, and searched the web for recent learned or kernel-level prefetching work (queries such as "Markov prefetcher", "learned memory prefetching", "remote memory prefetching Linux", "prefetching survey"). We kept papers that (a) predict future accesses from past ones or (b) prefetch at page/file granularity in an OS. We did not use a fixed database list, date window or screening protocol, so the review may miss relevant work; Table R1 lists what we did verify against a publisher or proceedings page.

**Markov and compression-based prediction.** Joseph and Grunwald [1] proposed a hardware Markov prefetcher that learns miss-address transitions and issues several predicted addresses at once; the table-based predictor in this paper is a simplified, page-level, software version of that idea. Vitter and Krishnan [2] showed that a prefetcher built on a compression-style predictor of the access sequence is asymptotically optimal and that its fault rate is tied to the entropy of the source, which is the theory behind our entropy analysis (Section 4.5). Kroeger and Long [3] applied a multi-order PPM context model to file accesses and reported that a 4 MB predictive cache beat a 90 MB LRU cache in their simulations; this is the closest OS-level precedent for our order-k predictors.

**Simple and history-based prefetchers.** Chen and Baer [4] introduced reference-prediction-table stride prefetching, the model for our stride baseline. Nesbit and Smith [5] stored miss history in a global history buffer so that different correlation patterns (stride, delta, address) can be served from one structure.

**Learned and OS-level prefetching.** Hashemi et al. [6] connected prefetching to n-gram language models and replaced the table with an LSTM, reporting higher precision and recall than table-based prefetchers on their benchmarks. Leap [7] is an OS-level example: a majority-trend detector over recent page deltas, integrated into the Linux data path for remote memory, with large latency gains reported against the default path. FarSight [8] uses a small offline-trained neural model inside the Linux far-memory path and reports gains over FastSwap and Hermit. A recent survey of complex memory-access prediction [9] covers hardware, software and ML prefetchers and lists missing standard benchmarks, energy trade-offs and the lack of a theory of prefetchability as open challenges.

**Table R1.** Comparison of the closest work. "Not reported" means we did not find or did not read the item in the source; results across papers use different setups and are not comparable.

| Work | Level / granularity | Predictor | Evaluation (as described by authors) | Limitation relevant to us |
|---|---|---|---|---|
| Joseph & Grunwald 1997 [1] | Hardware, cache lines | Markov table, multiple predictions | Cycle-level simulation, commercial benchmarks | Hardware cache setting; no entropy analysis |
| Vitter & Krishnan 1996 [2] | Theory, pages/blocks | Compression-based (LZ) | Proofs; asymptotic optimality | Asymptotic; not an empirical OS study |
| Kroeger & Long 1996 [3] | File system | Multi-order PPM context | Trace simulation, cache hit rate | File events, not pages; no throttle |
| Chen & Baer 1995 [4] | Hardware, data cache | Reference prediction table (stride) | Simulation | Strides only |
| Nesbit & Smith 2004 [5] | Hardware, data cache | Global history buffer | Simulation | Hardware setting |
| Hashemi et al. 2018 [6] | Hardware, cache lines | LSTM | Benchmarks, precision/recall | Offline-trained; cost not OS-realistic |
| Leap 2020 [7] | OS, remote-memory pages | Majority delta trend | Real Linux system, RDMA | Targets remote memory; trend-based, not learned Markov |
| FarSight 2025 [8] | OS, far-memory pages | Small neural net + future maps | Real Linux, 4 workloads | Offline training; heavy machinery |
| Survey [9] | Hardware/software/ML | Survey | PRISMA-guided (per its text) | Cache-centric; not page-level OS |
| **This paper** | OS, pages (simulated) | Count-based Markov, page vs delta state, k=1..3 | Simulator; 8 synthetic + 2 real traces | No timing model; 2 real programs |

**Research gap (provisional).** From the works above we see three gaps that our project can address at small scale; each is provisional because our search was not systematic and recent work may already cover it. (G1) The entropy-benefit relationship is established theoretically [2], but we found no empirical study that plots the benefit of an order-k, page-versus-delta Markov predictor against measured trace entropy across workloads. (G2) Delta-versus-page state and its table-size cost are rarely contrasted for page-level prefetching. (G3) Prefetch harm on high-entropy traces and a cheap accuracy throttle to contain it are discussed less than prefetch gains. Our experiments address G1 to G3 in simulation only; they do not establish that the findings hold on real systems.

## 3. Method

**Simulator.** `sim.c` replays a trace of page numbers against a fixed number of frames (256 unless stated) with LRU replacement. A prefetched page is inserted like a demand page but tagged; it is counted *useful* if referenced before eviction and *useless* if evicted unreferenced. Metrics: fault rate (faults / references), prefetch accuracy (useful / issued), wasted prefetches per reference, and table size.

**Predictors.** *none*; *next-page* (always prefetch p+1); *stride* (prefetch p+d when the last two deltas equal d); and a *Markov* predictor whose state is the last k symbols (k = 1, 2, 3), where a symbol is either the page number (*page state*) or the page delta (*delta state*). A direct-mapped, tagged table (2^16 entries by default) maps each state to four successor counters; the predictor prefetches the top-m successors whose share of the counts exceeds a confidence threshold.

**Adaptive throttle.** Every 2,048 references, the fraction of resident prefetched pages that were used decides the confidence threshold level (0.1, 0.4, 0.7 or 0.95): below 0.3 accuracy it moves up one level, above 0.6 it moves down, and with fewer than 32 prefetch outcomes in the window it relaxes by one level to probe again. The levels and cut-offs were chosen by hand, not tuned.

**Workloads.** Synthetic: *seq* (cyclic scan), *stride* (stride-7 scan), *loop* (600-page loop), *ptrchase* (fixed random cycle of 5,000 pages), *matmul* (naive i-j-k, 1024x1024 doubles), *noisy* (ptrchase with 10% random pages), *zipf* (independent Zipf-distributed references over 20,000 pages), *phases* (four different behaviours in sequence). *zipf* and *noisy* were regenerated with five more seeds. Real: a 384x384 naive matrix multiply (*real_matmul*) and a breadth-first search over a random 100,000-node, 300,000-edge graph (*real_bfs*), compiled with gcc -O2 and traced with `valgrind --tool=lackey --trace-mem=yes`. Data references are converted to 4 KB page numbers, consecutive repeats are collapsed, a 200,000-reference window from the compute phase is kept, and page ids are rank-compressed with gaps clipped to 4,096 pages (this keeps small strides but changes absolute addresses).

**Entropy.** For each trace we compute the prequential (online) conditional entropy in bits per reference of the next symbol given the last k symbols, with add-lambda smoothing backed off to a unigram model, for page and delta symbols at k = 1, 2, and report the minimum of the four. This mirrors how an online predictor learns, including its learning cost.

## 4. Results

![Fault rate by policy](../figures/fig1_policies.png)

**Table 1.** Fault rate by policy (256 frames, LRU, 2^16-entry table). Lowest per row in bold.

| workload | none | next-page | stride | Markov page k=1 | Markov page k=2 | Markov delta k=1 | Markov delta k=2 | Markov delta k=3 |
|---|---|---|---|---|---|---|---|---|
| seq | 1.000 | **0.000** | 0.000 | 0.458 | 0.458 | 0.000 | 0.000 | 0.000 |
| stride | 1.000 | 1.000 | 0.000 | 0.649 | 0.653 | **0.000** | 0.000 | 0.000 |
| loop | 1.000 | 0.990 | 1.000 | 0.010 | 0.013 | 0.026 | 0.026 | **0.006** |
| ptrchase | 1.000 | 0.999 | 1.000 | **0.091** | 0.104 | 0.105 | 0.091 | 0.092 |
| matmul | 0.501 | 0.500 | 0.501 | 0.499 | **0.016** | 0.021 | 0.020 | 0.024 |
| noisy | 1.000 | 0.999 | 1.000 | **0.224** | 0.304 | 0.309 | 0.376 | 0.445 |
| zipf | **0.542** | 0.615 | **0.542** | 0.546 | 0.545 | 0.560 | 0.542 | 0.542 |
| phases | 0.885 | 0.652 | 0.385 | 0.614 | 0.615 | 0.188 | 0.176 | **0.176** |
| real_matmul | 0.376 | **0.003** | 0.376 | 0.373 | 0.057 | 0.042 | 0.046 | 0.050 |
| real_bfs | **0.222** | 0.227 | 0.222 | 0.229 | 0.228 | 0.269 | 0.236 | 0.223 |


**Structured access favours Markov, and the right state matters.** On *seq* and *stride*, delta-state Markov reaches 0.000 faults per reference while page-state is stuck at 0.458 (see 4.2). On *matmul*, page-state order 1 fails (0.499) because the same page is followed by different pages as the A and B accesses interleave, while order 2 resolves it (0.016) (Figure 4).

**Where prefetching hurts.** On *zipf* no predictor can beat chance: the Markov variants stay within 0.02 of no-prefetch (0.542 to 0.560), and next-page makes things worse (0.615 versus 0.542) by displacing useful pages with useless ones.

**Real traces.** On *real_matmul*, plain next-page prefetching is best (0.003 versus 0.376 with no prefetching); the delta Markov predictor gets to 0.042 (order 1) and a degree-2 variant does better still, but it does not beat the simple heuristic. On *real_bfs*, a pointer-chasing workload, nothing helps: no prefetching gives 0.222, next-page 0.227, delta Markov 0.236. On real_matmul, the regularity the Markov predictor learns is also captured by next-page, which needs no table.

### 4.1 Frame count

![Fault rate versus frames](../figures/fig2_frames.png)

Prefetching gains are largest when the frame count is below the working set; once everything fits, the policies converge (the 600-page *loop* trace stops faulting for every policy once 1,024 frames are available). On *zipf* and *phases* the fault rate keeps falling smoothly as frames grow and the policies stay ordered the same way.

### 4.2 Table size

![Table size sweep](../figures/fig5_tablesize.png)

A page-state predictor needs about one entry per distinct page: on *seq* (30,000 pages) its fault rate is 0.458 at 2^16 entries and 0.241 at 2^18, which I attribute to direct-mapped collisions evicting learned successors (I have not isolated this with an associative table). The delta state is insensitive: *seq* stays at 0.000 even at 2^8 entries, since a sequential stream has a single repeating delta.

### 4.3 Order and state

![Order and state heatmap](../figures/fig4_order.png)

Higher order helps with interleaved streams (matmul) but hurts under noise (noisy: fault rate rises with k for delta states) since longer contexts are seen fewer times.

### 4.4 Adaptive throttle

![Wasted prefetches](../figures/fig3_throttle.png)

**Table 2.** Page-state k=1, degree 2: aggressive (threshold 0) versus adaptive throttle.

| workload | aggressive: wasted/ref | adaptive: wasted/ref | aggressive: fault rate | adaptive: fault rate |
|---|---|---|---|---|
| seq | 0.000 | 0.000 | 0.458 | 0.458 |
| stride | 0.000 | 0.000 | 0.649 | 0.649 |
| loop | 0.000 | 0.000 | 0.010 | 0.010 |
| ptrchase | 0.000 | 0.000 | 0.091 | 0.091 |
| matmul | 0.004 | 0.004 | 0.498 | 0.498 |
| noisy | 0.852 | 0.147 | 0.223 | 0.223 |
| zipf | 0.314 | 0.032 | 0.548 | 0.543 |
| phases | 0.074 | 0.012 | 0.615 | 0.613 |
| real_matmul | 0.000 | 0.000 | 0.372 | 0.372 |
| real_bfs | 0.170 | 0.021 | 0.235 | 0.225 |


On *zipf* the throttle cuts wasted prefetches per reference from 0.314 to 0.032, and on *noisy* from 0.852 to 0.147, with essentially unchanged fault rates. On *real_bfs* with the delta predictor it brings the fault rate from 0.242 (aggressive) to 0.225, close to no-prefetch (0.222).

### 4.5 Entropy and benefit

![Entropy versus benefit](../figures/fig6_entropy.png)

**Table 3.** Entropy of each workload and the best Markov configuration's gain over no prefetching.

| workload | best model entropy (bits/ref) | best Markov config | fault rate: none | fault rate: best Markov | reduction |
|---|---|---|---|---|---|
| seq | 0.001 | mk-delta-k1 | 1.000 | 0.000 | 1.000 |
| stride | 0.002 | mk-delta-k1 | 1.000 | 0.000 | 1.000 |
| loop | 0.042 | mk-delta-k3 | 1.000 | 0.006 | 0.994 |
| ptrchase | 0.391 | mk-page-k1 | 1.000 | 0.091 | 0.909 |
| matmul | 0.105 | mk-page-k2 | 0.501 | 0.016 | 0.969 |
| noisy | 3.543 | mk-page-k1 | 1.000 | 0.224 | 0.776 |
| zipf | 11.323 | mk-delta-k3 | 0.542 | 0.542 | -0.000 |
| phases | 4.469 | mk-delta-k3 | 0.885 | 0.176 | 0.801 |
| real_matmul | 0.420 | mk-delta-k1 | 0.376 | 0.042 | 0.889 |
| real_bfs | 8.603 | mk-delta-k3 | 0.222 | 0.223 | -0.007 |


Across all 20 traces the rank correlation between entropy and fault reduction is -0.89 (and -0.98 over the ten distinct workloads): low-entropy streams (seq, stride, loop, matmul) are almost fully fixed, mid-entropy streams (noisy, phases) are partly fixed, and the high-entropy streams (zipf, real_bfs) are not fixed at all. Seed-to-seed variation of the fault rate is small (standard deviation 0.0000 for noisy, 0.0016 for zipf with no prefetch).

## 5. Discussion and limitations

- **Simulator, not system.** There is no timing model, no I/O latency or bandwidth, no multiprocess interference, and prefetches are free and instantaneous. Fault counts are a proxy for performance. Real prefetching also competes for disk bandwidth, which would make the harm on high-entropy traces worse.
- **Traces.** All eight synthetic workloads are my own constructions, designed to span predictable and unpredictable behaviour; they show *mechanism*, not typical programs. The real evidence is two programs, 200,000 page references each, with a rank-compression step that alters absolute addresses. More real programs are needed before general claims.
- **Entropy and benefit are not independent measurements.** Both come from count-based predictions over the same stream, so a strong correlation is partly expected (Vitter and Krishnan make the connection formal). The contribution here is the empirical demonstration across predictors, workloads and real traces, not the existence of the relationship. The effective sample is ten distinct workloads, not twenty traces.
- **Throttle.** Its levels and cut-offs are hand-chosen and not tuned or validated on held-out workloads.
- **Predictor.** Direct-mapped table, four successors per entry, count-based confidence; no aging of old counts, which may hurt on phase changes.

## 6. Conclusion

A Markov prefetcher is worth deploying when the reference stream has low conditional entropy, and the choice of state (page versus delta) and order matters as much as the algorithm. When entropy is high, simple prefetching hurts and Markov prefetching adds nothing, so an accuracy-based throttle is the safe default. On the two real traces we tested, the simplest heuristic (next-page) was as good as or better than the Markov predictor where any prefetching helped, so the practical case for the added complexity is, on this evidence, not established.

## 7. Future work

1. Add a timing model (fault latency, I/O bandwidth, prefetch timeliness) so that fault counts become time.
2. Run kernel-level experiments (for example, a Linux swap or userfaultfd-based prefetcher) and compare against Leap-style trend prefetching [7].
3. Add many more real traces (SPEC or GAP-style programs) and test the entropy-benefit relationship on held-out workloads.
4. Tune the throttle on held-out traces and compare with a learned predictor [6, 8].
5. Systematic literature search with a stated protocol (databases, dates, inclusion criteria) to confirm or reject gaps G1 to G3.

## References

[1] D. Joseph and D. Grunwald, "Prefetching using Markov predictors," in *Proc. 24th Int. Symp. Computer Architecture (ISCA)*, 1997. (Title, authors, venue verified on a bibliographic record; pages not verified.)

[2] J. S. Vitter and P. Krishnan, "Optimal prefetching via data compression," *Journal of the ACM*, vol. 43, no. 5, pp. 771-793, 1996. (Verified on dblp; DOI not checked.)

[3] T. M. Kroeger and D. D. E. Long, "Predicting future file-system actions from prior events," in *Proc. USENIX Annual Technical Conference*, San Diego, 1996. (Verified on usenix.org.)

[4] T.-F. Chen and J.-L. Baer, "Effective hardware-based data prefetching for high-performance processors," *IEEE Trans. Computers*, vol. 44, no. 5, pp. 609-623, 1995, doi:10.1109/12.381947. (Journal details verified on an index record; author names from our own knowledge, not on that record.)

[5] K. J. Nesbit and J. E. Smith, "Data cache prefetching using a global history buffer," in *Proc. 10th Int. Symp. High-Performance Computer Architecture (HPCA)*, 2004, pp. 96-105, doi:10.1109/HPCA.2004.10030.

[6] M. Hashemi, K. Swersky, J. A. Smith, G. Ayers, H. Litz, J. Chang, C. Kozyrakis and P. Ranganathan, "Learning memory access patterns," in *Proc. 35th Int. Conf. Machine Learning (ICML)*, PMLR vol. 80, pp. 1919-1928, 2018.

[7] H. Al Maruf and M. Chowdhury, "Effectively prefetching remote memory with Leap," in *Proc. USENIX Annual Technical Conference (ATC)*, 2020, pp. 843-857. (Verified on usenix.org.)

[8] Y. Huang, Z. Guo and Y. Zhang, "Deep-learning-driven prefetching for far memory," arXiv:2506.00384, 2025. (Preprint; peer-review status not verified.)

[9] "Toward intelligent prefetching: a survey on complex memory access prediction techniques," arXiv:2606.09955. (Preprint; author list and date not verified, cite after checking.)

*Not yet verified (from the course P11 list, add after reading):* Liu et al., OSDI 2025 (tiered memory); Sun et al., ASPLOS 2025 (M5); Chai et al., OSDI 2025 (EMT); He et al., SOSP 2025.

## Reproducibility

`make all` rebuilds the simulator, regenerates traces, runs every experiment (all random seeds fixed) and regenerates all figures and the tables in this paper. Source: `sim.c`, `gen_traces.py`, `run_experiments.py`, `analyze.py`, `make_paper.py`.
