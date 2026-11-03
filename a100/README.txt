Acceptance test of the A100 in appmdp-05 (before the speed benchmark and any production run)

Run as p9sim, in this directory. Results go to acc-<host>/ (SUMMARY.txt, logs); every stage can be repeated.
The A100 is selected by name; the L40S is not touched (CUDA_VISIBLE_DEVICES = the A100's UUID).

Before (root, once):
  - driver loaded, card passed through:   nvidia-smi -L   (the A100 listed)
  - persistence mode:                      sudo nvidia-smi -i <A100 UUID> -pm 1   (or nvidia-persistenced)
  - DCGM for stage dcgm:                   sudo apt install datacenter-gpu-manager-4-cuda13   (or -cuda12 for an
                                           older driver); sudo systemctl enable --now nvidia-dcgm; dcgmi discovery -l
  - kernel log for Xid errors:             p9sim needs read access (journalctl -k), else the burn notes "not checked"
  - the production package unpacked:       tar -xzf p9prod-9a084ed.tar.gz   (sha256 caff4812...d9b12e)

Order and duration:
  bash acceptance.sh inventory                      1 min
  bash acceptance.sh dcgm                           about 30-60 min (DCGM level 3)
  bash acceptance.sh check ../p9prod-9a084ed        about 3-5 min (the 38 cases on sm_80)
  bash acceptance.sh throughput                     1 min
  bash acceptance.sh burn 1.5                       1.5 h (1-2 h; HOURS as argument)
  bash acceptance.sh reboot-before                  then: sudo reboot (appmdp-05; the card stays passed through)
  bash acceptance.sh reboot-after ../p9prod-9a084ed about 5 min
  bash acceptance.sh report                         SUMMARY.txt; "== PASSED" only if every stage is PASS
  (or: bash acceptance.sh all ../p9prod-9a084ed 1.5, then the three reboot steps and report)

Pass rules (fixed here, before the card is installed):
  inventory   ECC enabled; no remapped rows pending, no remapping failure; aggregate uncorrected ECC 0; PCIe x16
  dcgm        dcgmi diag -r 3 exits 0 and reports no failure
  check       check.sh of p9prod-9a084ed on the A100: "== ALL SAME" (all 38 cases bit for bit as on the reference)
  throughput  double add and double multiply each >= 80 % of 32 x SMs x max SM clock (A100: 4.9e12 ops/s at 1410 MHz)
  burn        fp64burn: every launch bit-identical to the first; no hardware/thermal slowdown or power brake active;
              GPU temperature <= 85 C; no uncorrected ECC error, aggregate counter and uncorrectable remapped rows
              unchanged; no Xid in the kernel log
  reboot      after the reboot: the same card (UUID, serial, PCI address), driver, VBIOS, ECC mode, counters; peak
              runs; check.sh again ALL SAME

Return: tar -czf acc-<host>.tar.gz acc-<host> and its sha256sum (no secrets in it: nvidia-smi output, logs).

bin/peak and bin/fp64burn: built with CUDA 13.3 (bin/NVCC-VERSION) in Ubuntu 22.04 (glibc 2.35), --fmad=false,
machine code for sm_80 and sm_120 and PTX for compute_80; sources in src/.

Addendum 2026-11-03 (written after the throughput result on the A100; the pass rules above are unchanged)
  throughput  The stage stays as it ran: FAIL. Cause found by the project lead: an nvidia-smi log every 200 ms
              shows 765 MHz (base clock, from idle) during bin/peak and 1365-1410 MHz only after about 0.4 s;
              765/1410 = 0.543, the measured FP64 ratio. bin/peak measures each operation over 5 launches right
              after one launch, so without warm-up.
              New stage, as an addendum:  bash acceptance.sh throughput-warm
                - bin/peak 5 2: 5 s of double add without pause (>= 3 s of load before the window), then every
                  operation over at least 2 s; each line ends with its window in Unix time;
                - nvidia-smi logs SM clock, clock event reasons, power and temperature every 100 ms
                  (peak-warm-clocks.csv); for double add and double mul the samples inside the window are reported;
                - same limit: >= 80 % of 32 x SMs x max SM clock.
              The result goes to ADDENDUM.txt, not to SUMMARY.txt. The report shows the verdict by the rules above
              and then the addenda; what an addendum means for the verdict is the project lead's decision.
              bin/peak without arguments behaves as before (reboot-after uses it so).
  burn        Clarified before the burn ran on the A100: judged are only HW slowdown (0x8), SW thermal slowdown
              (0x20), HW thermal slowdown (0x40) and HW power brake (0x80). SW power cap (0x4) is normal under FP64
              load at the power limit (250 W on the A100 PCIe); it is counted for information and not judged.
              Changes in the evaluation, same rule:
                - the reasons are read from their own columns and from the bit mask clocks_event_reasons.active;
                - if neither can be read from the monitor log, the burn fails ("not readable") instead of passing
                  without a check;
                - each monitoring field is probed up to three times (a single query can fail while the card wakes);
                - for information: SW power cap samples, and the driver's time counters per reason before and after.
  dcgm        On the A100 dcgmi warned "CUDA_VISIBLE_DEVICES is set on dcgmi process ... Failed to get hostengine
              environment variable", and the evaluation (case-insensitive grep for "fail" in the whole output)
              counted that warning as a failure although every test passed. The run of 2026-11-03 is evaluated by
              the project lead from its raw output by the rule above, and documented. From now on:
                - dcgmi runs without CUDA_VISIBLE_DEVICES; the card is chosen by -i with its DCGM id, found in
                  dcgmi discovery -l by the A100's UUID (dcgm-discovery.txt; fallback: the nvidia-smi index);
                - judged are only the result lines of the table (result Pass, Fail, Skip or Warn, also per GPU);
                  rule unchanged: exit 0 and no Fail; additionally FAIL if no result line is found.
  Use the new acceptance.sh with the existing result directory, so the earlier stages and the FAIL stay in it:
    ACC=<directory of the first package>/acc-<host> bash acceptance.sh throughput-warm
