# Prefetching Under Uncertainty: A Review of Recent Memory and Page Prefetching Research and an Entropy-Based Case Study

**Authors:** Pala Gaurav Reddy (PES1UG25AM254) and Punith VC (PES1UG25AM295)

PES University, Bengaluru

UE25CS242A Operating Systems, Mini Project, Topic P11 (Intelligent Memory Prefetching)

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

## Abstract

Prefetching tries to hide the latency of memory and storage by fetching data before it is requested, but a wrong guess costs bandwidth and can evict useful data. This paper reviews {{NREV}} papers from 2024 to 2026 on prefetching and closely related page-placement work, grouped into hardware and machine-learning cache prefetchers, operating-system and page-cache prefetching, tiered and CXL memory management, and prefetching for large language model (LLM) inference. For each paper we record the technique, the evaluation platform, the result reported by its authors and the disadvantage the authors state. The comparison shows that learned cache prefetchers are almost always evaluated in simulators, that OS-level learned prefetchers need per-application training and are tested on few applications, that harm from over-aggressive prefetching recurs across all four groups, and that no common measure of how prefetchable a workload is has been adopted. To probe the last two gaps at small scale we built a trace-driven demand-paging simulator in C and compared no prefetching, next-page, stride and Markov predictors on {{NTR}} traces. The benefit of Markov prefetching tracks the conditional entropy of the trace (Spearman {{RHO}}), naive prefetching raises the zipf fault rate from {{ZN}} to {{ZX}}, and a simple accuracy-driven throttle removes most wasted prefetches. The case study is simulation only, uses two real traces, and does not establish results for real systems.

**Keywords:** prefetching, demand paging, Markov predictor, conditional entropy, tiered memory, far memory, operating systems

## 1. Introduction

A page fault costs orders of magnitude more than a memory access, so a prefetcher that turns faults into hits is valuable. The same idea appears at every level of the memory hierarchy. Hardware prefetchers fetch cache lines [@GAZE; @PATH], operating systems prefetch pages from swap or remote memory [@FARSIGHT; @FETCHBPF], tiered-memory systems decide which pages belong in fast memory [@NOMAD; @JENGA], and LLM serving systems prefetch key-value (KV) cache blocks from CPU memory or SSD [@INFINI; @OASIS]. In every case a wrong prediction is not free: it uses bandwidth, and it can displace a page that would have been used.

Recent work has moved quickly toward learned predictors, including neural networks, reinforcement learning and even LLM-designed prefetchers [@DART; @ATHENA; @WHYFAIL]. Yet it is not obvious from the papers themselves how their claims compare, because they use different platforms, workloads and baselines. This paper therefore asks three questions.

- **RQ1.** What techniques have recent (2024 to 2026) papers proposed, and on what platforms were they evaluated?
- **RQ2.** What disadvantages do the authors themselves report, and which recur?
- **RQ3.** Can a small, reproducible experiment shed light on the recurring problems of predictability and harmful prefetching?

Our contributions are: (1) a structured review of {{NREV}} recent papers with a comparative table (Table 1), a taxonomy (Figure 1) and an evidence summary (Figure 2); (2) a list of provisional research gaps drawn from that comparison; and (3) an implementation, a C simulator with a workload suite, entropy analysis and an adaptive throttle, that addresses two of those gaps in simulation. We do not claim Markov prefetching is new; it goes back to the 1990s [@JG97; @VK96].

## 2. Background

**Demand paging and prefetching.** In demand paging a page is loaded only when a process touches it, so the process stalls on every fault. A prefetcher predicts future pages and loads them early. A prefetched page that is referenced before eviction is a *useful* prefetch; one evicted unreferenced is *useless*. Useful prefetches reduce faults, while useless ones waste I/O and can raise the fault rate by displacing resident pages. Metrics used in the literature include accuracy (useful over issued), coverage (faults removed over faults without prefetching) and timeliness (whether the page arrives before it is needed).

**Classical predictors.** Stride prefetching detects a constant difference between successive addresses [@CB95]. Global-history-buffer designs keep a shared history of misses and serve several correlation patterns from one structure [@NS04]. Markov prefetching keeps a table that maps the recent history to the addresses that tended to follow it, and issues several predictions at once [@JG97]. Kroeger and Long applied a multi-order context model from data compression to file accesses [@KL96], and Vitter and Krishnan showed that a compression-based predictor is asymptotically optimal and that its fault rate is governed by the entropy of the access sequence [@VK96]. That last result is the theoretical link between how predictable a workload is and how much a predictor can help, and we return to it in Section 7.

**Learned and OS-level prefetching.** Hashemi et al. connected prefetching to n-gram language models and used recurrent networks as the predictor [@HA18]. Leap brought a lightweight majority-trend detector into the Linux data path for remote memory [@LEAP20]. The papers reviewed here build on these ideas with newer models and deployments.

**Tiered memory.** With CXL and persistent memory, a machine can have several memory tiers of different speed. Systems place hot pages in the fast tier and migrate pages between tiers, which is closely related to prefetching because both depend on predicting future accesses and both pay for wrong predictions [@NOMAD; @LINDEN; @CXLSURV].

## 3. Review Methodology

**Review type.** This is a targeted narrative review, not a systematic literature review. We did not follow a PRISMA protocol, and we did not keep a log of every record screened and rejected, so we cannot report screened-and-excluded counts.

**Sources and queries.** We searched the web and arXiv listings and then opened the page of each candidate (arXiv abstract page, USENIX, ACM or the authors' site). Queries combined terms such as *prefetching*, *page prefetching*, *far memory*, *tiered memory CXL*, *learned prefetcher*, *reinforcement learning prefetcher*, *KV cache prefetching* and *readahead eBPF*. We also followed the course reference list for topic P11 and the citations of the surveys we found [@SURVPF; @CXLSURV].

**Inclusion and exclusion.** We included papers from 2024 to 2026 that (a) predict or schedule future memory, page, file or KV-cache accesses to hide latency, or (b) manage page placement across memory tiers, which shares the prediction problem. We excluded pre-2024 work from the review set and used it only as background (seven classic papers, Section 2). Of the {{NREV}} included papers, {{N24}} are from 2024, {{N25}} from 2025 and {{N26}} from 2026.

**Data extraction.** For each paper we recorded the technique, the evaluation platform (simulator, real system, survey, none), the headline result as the authors state it, and the disadvantage the authors state. Where the text we could read did not give a field we wrote "not stated" or "not read". Numbers are the authors' own and come from different setups, so we do not compare them across papers.

**Verification status.** For {{NVER}} papers we read the abstract page or the paper itself. For {{NPART}} papers we saw only the title and venue in an index or search result and did not read the technique, so they are marked partial in Table 1 and the spreadsheet that accompanies this paper, and no claim is built on them. Several preprints have not been peer reviewed, and we mark that in the reference list.

**Threats to validity.** The search was not exhaustive and used a general web search engine, so relevant papers may be missing. Venue and year for a few preprints are unconfirmed. We read abstract-level and introduction-level information for most papers, not every experiment.

![Taxonomy of the reviewed work](../figures/fig_taxonomy.png){width=62%}

*Figure 1. Taxonomy of the reviewed work: four groups with representative papers in each.*

## 4. Literature Review

### 4.1 Hardware and machine-learning cache prefetchers

Hardware work dominates the recent literature. Gaze characterises 4 KB regions by the temporal order of the first two accesses and reports a 27.7% average single-core speedup over no prefetching with 4.46 KB of storage, but it must wait for a second access, which hurts timeliness, and it loses up to 6.9% on some irregular traces [@GAZE]. Pathfinder uses a spiking neural network with online learning and reports small gains over SPP and Pythia, but it cannot predict first touches of cold pages and still trails Voyager on some benchmarks [@PATH]. DART distils an attention model into lookup tables, cutting inference cost by orders of magnitude while keeping most of the accuracy [@DART]. Two further papers on neural and graph-based prefetching, one at ISCA 2024 and one in ACM TACO, were only partially verified and are listed for completeness [@DUONG; @TRACED]; a conceptual graph-network toolchain reports no experiments [@QOWY].

A second theme is coordination and control. Athena uses a reinforcement-learning agent to decide when a prefetcher and an off-chip predictor should act, using accuracy and bandwidth as inputs, and beats earlier coordination policies by 5.0% to 7.9%, but its parameters were tuned only for single-core runs [@ATHENA]. CRL-Pythia shares a learning table across cores, yet its own text reports 40% more over-prediction than Pythia and notes that a shared table can mix conflicting behaviour [@CRL]. Themis uses per-page hints so that the hardware prefetcher is switched off for pages where it is mostly useless, removing about 40.6% of useless prefetches, at the price of a profiling step [@THEMIS]. A headroom study finds that the best single static policy loses 1.54% to an oracle that switches policy per phase, which points to phase-aware adaptation as an open direction [@STATIC]. Bera et al. summarise Pythia, an off-chip load predictor and an RL data-placement policy, and note that combining the predictors naively under-delivers [@BERA26].

The newest hardware papers use LLMs to design prefetchers. One work lets agents diagnose the program counters a deployed prefetcher misses and synthesises 17 sub-prefetchers, reporting a 61.1% geometric-mean speedup over no prefetching in simulation [@WHYFAIL]; another evolves multi-level prefetchers for the Data Prefetching Championship and gains 0.3% over the previous champion, with weaker multi-core results [@ARCH2]. Both are simulator studies. A final group applies learned prediction to specific settings: a temporal CNN to limit cache pollution in LLM inference, evaluated only on simulated traces and with figures in the abstract and table that disagree [@ACPC], and a streaming decision tree that predicts the next file-offset class on storage traces with high reported accuracy but without a described latency method [@CHENG]. A survey of 118 papers on irregular-access prefetching organises this area and lists missing standard benchmarks, energy trade-offs and the absence of a theory of prefetchability as open challenges [@SURVPF].

### 4.2 Operating-system and page-cache prefetching

Operating-system work is closer to the setting of this course. FarSight places a small offline-trained neural model in the Linux far-memory swap path, predicts ordinals and resolves them to addresses with per-page future maps, and reports speedups of up to 3.6 times over FastSwap and 2.6 times over Hermit [@FARSIGHT]. Its authors note that each application needs its own offline training and that precision is lower than FastSwap at small local memory because it prefetches aggressively. The earlier exploration of the same idea, Memix, was evaluated on three applications and warns that aggressive prefetching increases swap-out activity that can evict useful pages, and that hash-like patterns suit it poorly [@MEMIX].

A different direction makes policy programmable. FetchBPF lets developers deploy prefetch policies through eBPF without changing the kernel, with negligible overhead against a native implementation, although its abstract gives no speedups [@FETCHBPF]. cache_ext applies the same mechanism to page-cache eviction and reports large throughput gains for custom policies [@CACHEEXT]. Linden argues that on CXL memory prefetching must be tier-aware: hardware prefetching gives a 1.26 times speedup but degrades CXL performance by 19%, and the best prefetch distance differs between tiers [@LINDEN]. ObservUVM reuses GPU access counters to drive eviction and prefetching in unified memory, with a 34% geometric-mean speedup on one GPU [@OBSERV].

### 4.3 Tiered and CXL memory management

Tiering papers ask which pages should live in fast memory, a prediction problem with the same cost of error as prefetching. Nomad uses shadow copies and transactional migration to avoid stalls, reporting up to 6 times better performance than TPP under thrashing, but multi-mapped pages fall back to synchronous migration [@NOMAD]. Zhong et al. combine hardware flat-mode tiering with a software layer that uses a random-forest model to cut worst-case VM slowdown from about 35% to under 6% [@ZHONG]. Jenga groups objects of similar hotness and decays hotness smoothly, running about 28% faster than the best prior system in its main configuration but 5% to 7% slower on workloads with abrupt hot-set changes [@JENGA]. ARMS ranks pages by relative score instead of fixed thresholds [@ARMS], and Kanellis et al. show that tuning parameters with Bayesian optimisation doubles the performance of existing systems [@KANELLIS]. Cho et al. add ping-pong detection to TPP for multi-tenant machines [@CHO]. At the buffer-pool and object level, Rayhan and Aref build an n-tier buffer pool on OS page tables [@RAYHAN], and HADES groups hot and cold objects so that page reclaim works better [@HADES]. A broad CXL survey notes that tiering addresses latency but not bandwidth [@CXLSURV]. Two further tiering papers were only partially verified [@SOAR; @NEOMEM].

### 4.4 Prefetching for LLM inference

LLM inference has created a new prefetching problem, because the KV cache and model weights often exceed GPU memory. InfiniGen predicts which KV entries the next layer needs and prefetches them from CPU memory, reporting up to 3.00 times speedup over earlier KV-cache methods while being 1.52 times slower than an ideal all-on-GPU run [@INFINI]. CLO reports 9.3% to 66.6% higher decoding throughput through head-wise caching and prefetching [@CLO]. Tutti moves KV storage to NVMe with a slack-aware scheduler [@TUTTI], OasisKV uses draft tokens from speculative decoding to predict blocks to prefetch [@OASIS], and NeuroPrefetcher predicts which sparse MLP rows to fetch from NVMe, with I/O still 80% to 87% of per-token latency [@NEURO]. A prefetching scheme for retrieval-augmented generation predicts retrieval needs from hidden states [@RAG]. One simulator study is notable for a negative result: across its grid of placement policies, prefetching never beat no prefetching, even with an oracle that reads the future [@KVPLACE].

## 5. Comparative Analysis

Table 1 lists all {{NREV}} reviewed papers with the platform, the result as stated by the authors and the disadvantage as stated by the authors. Because setups differ, the results are not comparable across rows; the table supports comparison of kinds of evidence and kinds of disadvantage.

**Table 1.** Comparison of the reviewed papers (2024 to 2026). "Not read" means we did not read that item; P marks partially verified entries.

{{LITTABLE}}

![Evidence by group](../figures/fig_evidence.png){width=62%}

*Figure 2. How the reviewed papers were evaluated, by group.*

Figure 2 shows that, of the {{NHW}} hardware and ML cache-prefetcher papers, {{NHWSIM}} use a simulator or trace replay, while every OS-level paper we could classify used a real system. Three patterns stand out in the comparison.

**Different evidence in different layers.** Hardware prefetchers are judged by IPC in cycle-level simulators on SPEC, GAP and CloudSuite style traces, while OS-level and tiering papers report throughput or latency on real machines but with small application sets (three to four applications is common). Neither layer shows how the same predictor behaves across both.

**Learned predictors carry deployment costs.** FarSight and Memix need per-application offline training [@FARSIGHT; @MEMIX]; Pathfinder and DART trade accuracy for hardware cost [@PATH; @DART]; the LLM-designed prefetcher needs about 110 KB of state and a large token budget [@WHYFAIL]. A count-based predictor needs none of this training, which motivates our case study, although it is also less powerful.

**Over-aggressive prefetching recurs.** Memix warns that aggressive prefetching evicts useful pages [@MEMIX], CRL-Pythia reports 40% more over-prediction [@CRL], Linden finds hardware prefetching degrades CXL performance by 19% [@LINDEN], FarSight has lower precision than FastSwap [@FARSIGHT], Themis removes about 40.6% useless prefetches [@THEMIS], and the KV placement study finds prefetching never beat no prefetching [@KVPLACE]. Throttling and coordination are therefore not minor details.

## 6. Research Gaps

The gaps below come from the comparison above. Each is provisional: our search was not systematic, and a paper we did not find may already address it.

**G1. Learned prefetchers are rarely tested both in simulators and on real systems.** Hardware prefetchers are mostly simulated (Figure 2), and OS-level ones use few applications. Evidence: Table 1 and Figure 2. Confidence: moderate, since it rests on the papers we could classify.

**G2. OS-level learned prefetchers depend on offline, per-application training.** FarSight and Memix both state this limitation [@FARSIGHT; @MEMIX]. We did not find a comparison of a lightweight online count-based predictor with these heavier models at page granularity. Confidence: low to moderate.

**G3. There is no common measure of how prefetchable a workload is.** The prefetching survey lists the lack of a theory of prefetchability and of standard benchmarks as open challenges [@SURVPF], while Vitter and Krishnan gave a theoretical link between entropy and fault rate decades ago [@VK96]. We did not find a recent empirical study that measures trace entropy and relates it to the benefit of different predictor types. Confidence: low to moderate.

**G4. Containing the harm of wrong prefetches is treated as an add-on.** Section 5 lists six papers that report some form of harm or over-prediction. Throttles are usually built into one design rather than evaluated on their own. Confidence: moderate.

**G5. LLM-era prefetching is evaluated on single platforms and sometimes shows no benefit.** Several LLM papers use one server or one edge device [@TUTTI; @NEURO], and the KV placement study reports no benefit from prefetching [@KVPLACE]. Confidence: low, because this area is moving quickly.

Our implementation in Section 7 addresses G3 and G4 at small scale and gives a data point for G2. It does not address G1 or G5.

## 7. Implementation and Case Study

### 7.1 Method

**Simulator.** `sim.c` replays a trace of page numbers against a fixed number of frames (256 unless stated) with LRU replacement. A prefetched page is inserted like a demand page but tagged; it is counted *useful* if referenced before eviction and *useless* if evicted unreferenced. Metrics: fault rate (faults / references), prefetch accuracy (useful / issued), wasted prefetches per reference, and table size.

**Predictors.** *none*; *next-page* (always prefetch p+1); *stride* (prefetch p+d when the last two deltas equal d); and a *Markov* predictor whose state is the last k symbols (k = 1, 2, 3), where a symbol is either the page number (*page state*) or the page delta (*delta state*). A direct-mapped, tagged table (2^16 entries by default) maps each state to four successor counters; the predictor prefetches the top-m successors whose share of the counts exceeds a confidence threshold.

**Adaptive throttle.** Every 2,048 references, the fraction of resident prefetched pages that were used decides the confidence threshold level (0.1, 0.4, 0.7 or 0.95): below 0.3 accuracy it moves up one level, above 0.6 it moves down, and with fewer than 32 prefetch outcomes in the window it relaxes by one level to probe again. The levels and cut-offs were chosen by hand, not tuned.

**Workloads.** Synthetic: *seq* (cyclic scan), *stride* (stride-7 scan), *loop* (600-page loop), *ptrchase* (fixed random cycle of 5,000 pages), *matmul* (naive i-j-k, 1024x1024 doubles), *noisy* (ptrchase with 10% random pages), *zipf* (independent Zipf-distributed references over 20,000 pages), *phases* (four different behaviours in sequence). *zipf* and *noisy* were regenerated with five more seeds. Real: a 384x384 naive matrix multiply (*real_matmul*) and a breadth-first search over a random 100,000-node, 300,000-edge graph (*real_bfs*), compiled with gcc -O2 and traced with `valgrind --tool=lackey --trace-mem=yes`. Data references are converted to 4 KB page numbers, consecutive repeats are collapsed, a 200,000-reference window from the compute phase is kept, and page ids are rank-compressed with gaps clipped to 4,096 pages (this keeps small strides but changes absolute addresses).

**Entropy.** For each trace we compute the prequential (online) conditional entropy in bits per reference of the next symbol given the last k symbols, with add-lambda smoothing backed off to a unigram model, for page and delta symbols at k = 1, 2, and report the minimum of the four. This mirrors how an online predictor learns, including its learning cost.

### 7.2 Results

![Fault rate by policy](../figures/fig1_policies.png){width=62%}

*Figure 3. Fault rate by policy and workload.*

**Table 2.** Fault rate by policy (256 frames, LRU, 2^16-entry table). Lowest per row in bold.

{{T1}}

**Structured access favours Markov, and the right state matters.** On *seq* and *stride*, delta-state Markov reaches {{SEQD}} faults per reference while page-state is stuck at {{SEQP}} (see 7.2.2). On *matmul*, page-state order 1 fails ({{MMP1}}) because the same page is followed by different pages as the A and B accesses interleave, while order 2 resolves it ({{MMP2}}) (Figure 4).

**Where prefetching hurts.** On *zipf* no predictor can beat chance: the Markov variants stay within 0.02 of no-prefetch (0.542 to 0.560), and next-page makes things worse ({{ZX}} versus {{ZN}}) by displacing useful pages with useless ones.

**Real traces.** On *real_matmul*, plain next-page prefetching is best ({{RMX}} versus {{RMN}} with no prefetching); the delta Markov predictor gets to {{RMD}} (order 1) and a degree-2 variant does better still, but it does not beat the simple heuristic. On *real_bfs*, a pointer-chasing workload, nothing helps: no prefetching gives {{RBN}}, next-page {{RBX}}, delta Markov {{RBM}}. On real_matmul, the regularity the Markov predictor learns is also captured by next-page, which needs no table.

#### 7.2.1 Frame count

Prefetching gains are largest when the frame count is below the working set; once everything fits, the policies converge (the 600-page *loop* trace (curves for every workload are in `figures/fig2_frames.png` in the repository) stops faulting for every policy once 1,024 frames are available). On *zipf* and *phases* the fault rate keeps falling smoothly as frames grow and the policies stay ordered the same way.

#### 7.2.2 Table size

(Sweep plot: `figures/fig5_tablesize.png` in the repository.) A page-state predictor needs about one entry per distinct page: on *seq* (30,000 pages) its fault rate is {{SEQ16}} at 2^16 entries and {{SEQ18}} at 2^18, which we attribute to direct-mapped collisions evicting learned successors (we have not isolated this with an associative table). The delta state is insensitive: *seq* stays at {{SEQ8D}} even at 2^8 entries, since a sequential stream has a single repeating delta.

#### 7.2.3 Order and state

![Order and state heatmap](../figures/fig4_order.png){width=62%}

*Figure 4. Fault rate by Markov order and state type.*

Higher order helps with interleaved streams (matmul) but hurts under noise (noisy: fault rate rises with k for delta states) since longer contexts are seen fewer times.

#### 7.2.4 Adaptive throttle

![Wasted prefetches](../figures/fig3_throttle.png){width=62%}

*Figure 5. Wasted prefetches per reference, aggressive versus adaptive.*

**Table 3.** Page-state k=1, degree 2: aggressive (threshold 0) versus adaptive throttle.

{{T2}}

On *zipf* the throttle cuts wasted prefetches per reference from {{ZWA}} to {{ZWD}}, and on *noisy* from {{NWA}} to {{NWD}}, with essentially unchanged fault rates. On *real_bfs* with the delta predictor it brings the fault rate from {{RBAG}} (aggressive) to {{RBAD}}, close to no-prefetch ({{RBN}}).

#### 7.2.5 Entropy and benefit

![Entropy versus benefit](../figures/fig6_entropy.png){width=62%}

*Figure 6. Trace entropy against the fault reduction from the best Markov configuration.*

**Table 4.** Entropy of each workload and the best Markov configuration's gain over no prefetching.

{{T3}}

Across all {{NTR}} traces the rank correlation between entropy and fault reduction is {{RHO}} (and {{RHO10}} over the ten distinct workloads): low-entropy streams (seq, stride, loop, matmul) are almost fully fixed, mid-entropy streams (noisy, phases) are partly fixed, and the high-entropy streams (zipf, real_bfs) are not fixed at all. Seed-to-seed variation of the fault rate is small (standard deviation {{NZS}} for noisy, {{ZZS}} for zipf with no prefetch).


## 8. Discussion and limitations

- **Simulator, not system.** There is no timing model, no I/O latency or bandwidth, no multiprocess interference, and prefetches are free and instantaneous. Fault counts are a proxy for performance. Real prefetching also competes for disk bandwidth, which would make the harm on high-entropy traces worse.
- **Traces.** All eight synthetic workloads are our own constructions, designed to span predictable and unpredictable behaviour; they show *mechanism*, not typical programs. The real evidence is two programs, 200,000 page references each, with a rank-compression step that alters absolute addresses. More real programs are needed before general claims.
- **Entropy and benefit are not independent measurements.** Both come from count-based predictions over the same stream, so a strong correlation is partly expected (Vitter and Krishnan make the connection formal). The contribution here is the empirical demonstration across predictors, workloads and real traces, not the existence of the relationship. The effective sample is ten distinct workloads, not twenty traces.
- **Throttle.** Its levels and cut-offs are hand-chosen and not tuned or validated on held-out workloads.
- **Predictor.** Direct-mapped table, four successors per entry, count-based confidence; no aging of old counts, which may hurt on phase changes.


## 9. Conclusion

Recent prefetching research is rich but uneven. Hardware prefetchers are mostly simulated, OS-level learned prefetchers need training and are tested on few applications, tiering work shares the same prediction problem, and LLM-serving systems are adopting prefetching quickly. Across all of them, the cost of wrong predictions keeps reappearing, and no common measure of prefetchability is in use. Our case study shows, in simulation, that the benefit of a Markov prefetcher follows the entropy of the reference stream, that naive prefetching hurts high-entropy workloads, and that a simple accuracy throttle removes most wasted prefetches. On the two real traces we tested, the simplest heuristic (next-page) was as good as or better than the Markov predictor where prefetching helped at all, so the practical case for added complexity is not established by this evidence.

### 9.1 Future work

1. Add a timing model so that fault counts become time, then run in a real kernel and compare with trend-based prefetching [@LEAP20] and learned OS prefetchers [@FARSIGHT].
2. Collect many more real traces and test the entropy-benefit relationship on held-out workloads.
3. Tune the throttle on held-out traces and compare with learned coordination [@ATHENA].
4. Replace this targeted review with a systematic one that has a stated protocol and a screening log, to confirm or reject G1 to G5.

## Reproducibility

`make all` rebuilds the simulator, regenerates traces, runs every experiment (all random seeds fixed) and regenerates all figures and the tables in this paper. Source: `sim.c`, `gen_traces.py`, `run_experiments.py`, `analyze.py`, `make_paper.py`.

## References

{{REFS}}

