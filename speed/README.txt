Speed comparison: p9gpu on the GPUs against REBOUND (p9sim) on the CPU cores, pinned, with a GPU scaling series

The repetition, on a server, of the notebook comparison of 2026-10-23 (runs/speed/RESULT.md in medas-p9-search-bb2021),
for publication: defined cores, pinned, native Linux (or a VM with passed-through GPUs), full-load throughput.
Before the production run, after the A100 acceptance test. Run as the user that computes (p9sim), in this directory.
Nothing outside this directory is changed. No root, no network. Needs: Linux, an NVIDIA driver (580 or newer),
glibc 2.34 or newer, bash, awk, python3, lscpu, taskset (numactl if present); gcc and make for the stage native.
No paths of a particular machine: it runs the same on another server (e.g. a rented H100) with "gpu H100".

What is measured (all jobs: Brown & Batygin (2021) configuration, seed 101, dt 0.5 yr, FP64, no FMA):
  gpu NAME   p9gpu on that GPU, the host thread pinned to one core near it:
               - the two jobs of the notebook comparison: 4,000 test bodies over 10 Myr, fixed step (wh) and v5
                 (smooth transition, collisions; the production method);
               - scaling series 4,000 / 16,000 / 64,000 / 256,000 test bodies over 1 Myr, both methods: the
                 throughput at full load (the A100 is not judged on 4,000 test bodies alone);
               - SM clock, clock event reasons, power and temperature logged every second.
  cpu1       REBOUND WHFast and MERCURIUS on one core each, 4,000 test bodies over 10 Myr (the notebook jobs);
             all repetitions at once, each process on its own physical core of NUMA node NODE (default 0), its
             memory on that node; the second hardware thread of each core stays idle.
  native     p9sim built here from its sources twice, standard flags and -march=native (both -ffp-contract=off,
             no -ffast-math): the result hash against the reference, the time against the standard build
             (1-Myr jobs, all at once on node NODE).
  cpuall     the whole CPU: the same 1-Myr slice of 4,000 test bodies on every physical core at once (one copy per
             core: the same work on every core, so the slowest is not an easier slice), WHFast then MERCURIUS.
             Throughput = cores x 4,000 x steps / time of the whole batch. SMT=1: on every hardware thread.
  A run counts only if it gives the reference result hash (jobs/<job>/EXPECTED, computed on the reference machine:
  jobs/<job>/REFERENCE). Every run is in RESULTS.tsv with its verdict SAME / DIFFERENT / FAILED.

Checks before every stage (logged in speed.log, "NOT STARTED" if they fail; FORCE=1 measures anyway and notes it):
  - GPU stages: no compute process on the card being measured (by its UUID). Processes on the other GPUs are
    logged, not checked.
  - All stages: the background load (other services, e.g. the notary or a read node) is measured over 60 s as busy
    logical CPUs and logged, with the top processes (background-<stage>.txt); the stage starts if it is at most
    LOAD_MAX (default 2).

Before (once):
  - Not changed by the scripts, only logged (stage env): CPU model, sockets, NUMA nodes, SMT, governor, turbo,
    virtualisation, kernel, GPU clocks, power limits, persistence mode, temperatures, driver and CUDA version,
    package version and binary hashes. In a VM the scripts see only the vCPUs: note how the vCPUs are pinned to
    host cores (hypervisor setting) and which host CPU it is, for the report.
  - Check the package: sha256sum -c SHA256SUMS

Order and duration (estimates; REPS=3 repetitions), in two blocks:
  day:   bash speed.sh start day      env, native, gpu A100, cpu1                about 6-9 h
           native  about 40-60 min (12 processes: node NODE needs 12 physical cores)
           gpu A100  about 1-1.5 h
           cpu1  about 4-7 h (6 processes; depends on the core's clock)
  night: bash speed.sh start night    env, gpu L40S, cpuall, report              about 5-6 h
           gpu L40S  about 3-3.5 h: everything else on the L40S stopped before (the check refuses otherwise)
           cpuall  about 1-2 h
  then:  bash speed.sh status | stop; every stage also alone in the foreground (bash speed.sh gpu L40S ...).
  A stage can be repeated; the report uses the latest run of each job and repetition.
  After the speed comparison, not before: the production run and other long runs on the machine.

Results to send back: tar -czf results-<host>.tar.gz results-<host> and its sha256sum (RESULTS.tsv, REPORT.txt,
env.txt, speed.log, monitor logs, the result lines of every run; no secrets: nvidia-smi, lscpu and ps output).
The runs' output.sa files are deleted after each run (the result hash covers them).

Programs: bin/p9gpu and bin/p9sim are those of the production package p9prod-9a084ed, unchanged (sha256 in
bin/SHA256-*); native/ holds their sources (9a084ed) and REBOUND 5.2.2. Licence GPL-3.0-or-later (LICENSE).
