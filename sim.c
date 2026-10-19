/* sim.c - trace-driven demand-paging simulator with prefetching (LRU eviction).
 * Policies: none | next | stride | markov (order-k, page- or delta-state, optional adaptive throttle).
 * Build: gcc -O2 -o sim sim.c -lm      Output: one CSV line (see header in run_experiments.py). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define M 4                 /* successor slots per Markov table entry */
#define OFF (1 << 20)       /* offset so negative deltas pack into 21 bits */
#define WIN 2048            /* adaptive-throttle window (references) */

typedef struct { int prev, next, page; unsigned char pf; } Node;
typedef struct { uint64_t key; int32_t val[M]; uint32_t cnt[M]; unsigned char used; } Entry;

static Node *nd; static int *where, *freel; static int head = -1, tail = -1, nfree, F;
static long refs, faults, issued, useful, useless, wUseful, wRes;
static Entry *tab; static uint64_t tmask;

/* ---------- LRU page cache ---------- */
static void unlink_node(int i) {
    if (nd[i].prev >= 0) nd[nd[i].prev].next = nd[i].next; else head = nd[i].next;
    if (nd[i].next >= 0) nd[nd[i].next].prev = nd[i].prev; else tail = nd[i].prev;
}
static void push_front(int i) {
    nd[i].prev = -1; nd[i].next = head;
    if (head >= 0) nd[head].prev = i;
    head = i; if (tail < 0) tail = i;
}
static void insert_page(int p, int pf) {
    int i;
    if (nfree > 0) i = freel[--nfree];
    else {
        i = tail; unlink_node(i); where[nd[i].page] = -1;
        if (nd[i].pf) { useless++; wRes++; }          /* prefetched but never used */
    }
    nd[i].page = p; nd[i].pf = pf; where[p] = i; push_front(i);
}
static void access_page(int p) {
    int i = where[p];
    if (i >= 0) {
        if (nd[i].pf) { useful++; wUseful++; wRes++; nd[i].pf = 0; }   /* prefetch paid off */
        unlink_node(i); push_front(i);
    } else { faults++; insert_page(p, 0); }
}
static void prefetch(long q, int P) {
    if (q < 0 || q >= P || where[q] >= 0) return;
    issued++; insert_page((int)q, 1);
}

/* ---------- Markov table (direct-mapped, tagged) ---------- */
static uint64_t hashk(uint64_t x) {
    x ^= x >> 33; x *= 0xff51afd7ed558ccdULL; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ULL; x ^= x >> 33; return x;
}
static uint64_t mkkey(const int32_t *h, int k, int delta) {
    uint64_t key = 0;
    for (int j = 0; j < k; j++) key = (key << 21) | (uint64_t)((h[j] + (delta ? OFF : 0)) & 0x1FFFFF);
    return key;
}
static void upd(uint64_t key, int32_t v) {
    Entry *e = &tab[hashk(key) & tmask];
    if (!e->used || e->key != key) { memset(e, 0, sizeof *e); e->used = 1; e->key = key; }
    int minj = 0;
    for (int j = 0; j < M; j++) {
        if (e->cnt[j] && e->val[j] == v) { if (e->cnt[j] < 1000000) e->cnt[j]++; return; }
        if (e->cnt[j] < e->cnt[minj]) minj = j;
    }
    e->val[minj] = v; e->cnt[minj] = 1;
}
static int pred(uint64_t key, double thr, int deg, int32_t *out) {
    Entry *e = &tab[hashk(key) & tmask];
    if (!e->used || e->key != key) return 0;
    uint32_t tot = 0; int n = 0, taken[M] = {0};
    for (int j = 0; j < M; j++) tot += e->cnt[j];
    while (n < deg) {
        int bj = -1;
        for (int j = 0; j < M; j++) if (!taken[j] && e->cnt[j] && (bj < 0 || e->cnt[j] > e->cnt[bj])) bj = j;
        if (bj < 0) break;
        taken[bj] = 1;
        if ((double)e->cnt[bj] / tot < thr) break;
        out[n++] = e->val[bj];
    }
    return n;
}

int main(int argc, char **argv) {
    const char *trace = NULL, *policy = "none", *state = "delta";
    int k = 1, deg = 1, adapt = 0, tbits = 14, fallback = 0; double thr = 0.0; F = 256;
    for (int a = 1; a + 1 < argc; a += 2) {
        if (!strcmp(argv[a], "-i")) trace = argv[a+1];
        else if (!strcmp(argv[a], "-p")) policy = argv[a+1];
        else if (!strcmp(argv[a], "-s")) state = argv[a+1];
        else if (!strcmp(argv[a], "-k")) k = atoi(argv[a+1]);
        else if (!strcmp(argv[a], "-d")) deg = atoi(argv[a+1]);
        else if (!strcmp(argv[a], "-t")) thr = atof(argv[a+1]);
        else if (!strcmp(argv[a], "-a")) adapt = atoi(argv[a+1]);
        else if (!strcmp(argv[a], "-T")) tbits = atoi(argv[a+1]);
        else if (!strcmp(argv[a], "-f")) F = atoi(argv[a+1]);
        else if (!strcmp(argv[a], "-F")) fallback = atoi(argv[a+1]);
    }
    if (!trace || k < 1 || k > 3) { fprintf(stderr, "usage: sim -i trace [-p none|next|stride|markov] [-s page|delta] [-k 1..3] [-d deg] [-t thr] [-a 0|1] [-T tablebits] [-f frames] [-F 0|1]\n"); return 1; }
    int delta = !strcmp(state, "delta");
    int pol = !strcmp(policy, "next") ? 1 : !strcmp(policy, "stride") ? 2 : !strcmp(policy, "markov") ? 3 : 0;

    FILE *fp = fopen(trace, "r"); if (!fp) { perror("trace"); return 1; }
    size_t cap = 1 << 20, n = 0; int *tr = malloc(cap * sizeof(int)); int x, P = 0;
    while (fscanf(fp, "%d", &x) == 1) { if (n == cap) { cap *= 2; tr = realloc(tr, cap * sizeof(int)); } tr[n++] = x; if (x + 1 > P) P = x + 1; }
    fclose(fp);

    nd = malloc(F * sizeof(Node)); freel = malloc(F * sizeof(int)); where = malloc(P * sizeof(int));
    for (int i = 0; i < P; i++) where[i] = -1;
    for (int i = 0; i < F; i++) freel[i] = F - 1 - i;
    nfree = F;
    tab = calloc((size_t)1 << tbits, sizeof(Entry)); tmask = ((uint64_t)1 << tbits) - 1;

    static const double LEV[4] = {0.1, 0.4, 0.7, 0.95}; int lev = 0;
    int32_t hist[3] = {0, 0, 0}; int hn = 0, prev = -1, lastd = 0;

    for (size_t t = 0; t < n; t++) {
        int cur = tr[t]; refs++;
        access_page(cur);
        if (pol == 1) prefetch(cur + 1, P);
        else if (pol == 2) {
            if (prev >= 0) { int d = cur - prev; if (d != 0 && d == lastd) for (int i = 1; i <= deg; i++) prefetch((long)cur + (long)d * i, P); lastd = d; }
        } else if (pol == 3) {
            int ok = 1; int32_t sym = cur;
            if (delta) { if (prev < 0) ok = 0; else sym = cur - prev; }
            if (ok) {
                if (hn >= k) upd(mkkey(hist, k, delta), sym);
                for (int j = 0; j < k - 1; j++) hist[j] = hist[j+1];
                hist[k-1] = sym; hn++;
            }
            int got = 0;
            if (hn >= k) {
                int32_t out[M]; int m = pred(mkkey(hist, k, delta), adapt ? LEV[lev] : thr, deg, out);
                for (int j = 0; j < m; j++) prefetch(delta ? (long)cur + out[j] : (long)out[j], P);
                got = m;
            }
            if (!got && fallback) prefetch(cur + 1, P);
        }
        prev = cur;
        if (adapt && refs % WIN == 0) {                 /* throttle: raise confidence bar when prefetches are wasted */
            if (wRes >= 32) { double acc = (double)wUseful / wRes; if (acc < 0.3 && lev < 3) lev++; else if (acc > 0.6 && lev > 0) lev--; }
            else if (lev > 0) lev--;                    /* too quiet: probe again */
            wUseful = wRes = 0;
        }
    }
    printf("%s,%s,%d,%d,%.2f,%d,%d,%d,%ld,%ld,%ld,%ld,%ld\n", policy, pol == 3 ? state : "-", k, deg, thr, adapt, tbits, F, refs, faults, issued, useful, useless);
    return 0;
}
