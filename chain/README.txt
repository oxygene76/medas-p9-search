MEDAS p9-search: chain of the A100 runs and run watcher (package p9chain)
===========================================================================

chain-a100.sh   the A100 runs one after the other: production run -> V5 of seeds 110-112 -> CPU-2 measurement ->
                V5 half of the paired tests -> set A -> set B; starts the
                next run only when the previous one is complete, the A100 is healthy and free, the log is clean, and
                for sets A and B the V2 verdict and e4-on-chain.ok exist; reports every transition by Telegram
run-watch.sh    Telegram watcher: the chain itself, the MERCURIUS part of seeds 110-112, reports twice a day
lib.sh          common functions (Telegram, A100 health, run states)
chain.env.example  settings (paths, GPU UUID, intervals); copy to chain.env
systemd/        user units: p9-chain.timer and p9-watch.timer, every 5 min
test/test-chain.sh  the whole chain with stand-ins (fake nvidia-smi, journalctl, curl and packages); no GPU needed
ANLEITUNG.md    setup and operation (German), with the expected output of each step

The usage of each script: sh chain-a100.sh (without arguments), sh run-watch.sh.
Run as the user of the runs, never as root. Nothing here stops a run or starts the production run.
