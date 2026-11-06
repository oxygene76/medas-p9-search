MEDAS p9-search: segments of finished runs computed again (reproduction for the data package)
==============================================================================================

A100 window, point 3 (proposal of 2026-11-06, docs/a100-window-proposal-20261106.md): the segments listed in TARGETS
(by default segments 0, 19 and 39 of the production run and segment 19 of each V5 job of seeds 110-112) are computed
again from their stored inputs with the run's own p9gpu (checked: the production binary), with the run's settings.
Only hashes are compared: the result hash with DONE and segments.tsv, for information the flyby and removal logs.
Nothing of the content is looked at. The run directories are only read; everything is written under runs/ here.

Where: the A100 while it is otherwise idle; start.sh refuses while another compute process is on the card, and the
A100 chain starts nothing while this runs (the card is busy). Start it by hand, only when no chain transition is due.
About 10-12 h with the default TARGETS.

sh start.sh (RUNS=... if the runs are not under $HOME/runs), sh status.sh, sh stop.sh; start.sh again goes on with the
segments not yet done. Result: RESULT/VERDICT.txt, RESULT/REPRO.tsv, run.log. Results to send back: RESULT/, run.log,
start.log.
