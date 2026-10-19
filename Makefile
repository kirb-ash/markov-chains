# make all  -> build simulator, regenerate synthetic traces, run every experiment, make figures + paper tables
CC=gcc
CFLAGS=-O2 -Wall

all: sim traces results/main.csv figures paper/paper.md

sim: sim.c
	$(CC) $(CFLAGS) -o sim sim.c

traces: gen_traces.py
	python gen_traces.py > /dev/null

results/main.csv: sim run_experiments.py traces
	python run_experiments.py

figures: results/main.csv analyze.py
	python analyze.py > results/analysis_log.txt

paper/paper.md: figures make_paper.py paper/template.md
	python make_paper.py

# optional: recapture the two real traces (needs valgrind; committed traces are enough to reproduce results)
realtraces:
	cd realtrace && gcc -O2 -o progs progs.c && gcc -O2 -o filter filter.c && ./capture.sh

clean:
	rm -f sim results/*.csv figures/*.png
.PHONY: all figures traces realtraces clean
