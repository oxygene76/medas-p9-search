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
