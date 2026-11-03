Start of the production run on the A100 (start-a100.sh, status-a100.sh; not part of the package, tools/make_prod_package.sh copies only its named files) (p9prod-9a084ed unchanged; docs/production-criteria.md of medas-p9-search)

Before (all must hold, production-criteria.md section 2): the A100 acceptance test passed (including the reboot test),
the speed benchmark done, entry 3 on the chain, the project lead's explicit word, the maintenance window over.

As p9sim, next to the unpacked package:
  sh start-a100.sh ../p9prod-9a084ed      CUDA_VISIBLE_DEVICES = the A100's UUID, pinned to CPU 2 (socket 1), nice 10
  sh status-a100.sh ../p9prod-9a084ed     the package's status, the card p9gpu really runs on, the check times
  sh ../p9prod-9a084ed/stop.sh            stops (the running segment is computed again on the next start)
  sh start-a100.sh ../p9prod-9a084ed      resumes, with the same settings

The check runs first (check.sh, about 1 minute on the A100); only with ALL SAME do the segments start. Its header line
"gpu: ..." names the first card of nvidia-smi, not the one used: status-a100.sh shows the real one and the check times
(A100 about 14.5 s for deep-57, L40S about 33 s). Settings: GPU_NAME=... (another card), SOCKET=... (other cores).
