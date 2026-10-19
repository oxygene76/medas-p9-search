# Operating long runs

## Processes

- Every long-running process gets a PID file in `runs/pids/` (`<name>.pid`),
  written when it is started. Checks only through these files: `kill -0 PID`
  (alive?) and `ps -p PID -o stat=,args=` (what, running or stopped). No
  `pgrep -f`/`pkill -f`: a pattern also matches the shell that searches.
- Children of a process: `ps -o pid= --ppid PID`.
- Pausing: `kill -STOP PID` / `kill -CONT PID` on the program (p9gpu/p9sim),
  noted in the run's `pause.log`.

## Campaigns: checkpoints and restart

`tools/campaign.py` (since b2caf76) continues a campaign when the same command
is started again: segments whose `result.json` belongs to their `job.json` are
kept (they are the checkpoints, one per segment); a segment that was
interrupted is moved aside (`segNNN.interrupted-<time>`) and made again from
the last finished one. Every job is deterministic, so the continued run gives
the same bits as one without interruption (`make test-resume`: a campaign
stopped in the middle of a segment and started again gives the same result
hashes in every segment). What is lost is the time of the interrupted
segment. `--t-end` ends the chains at a given time.

### The corrected 4-Gyr run `runs/gpu-4gyr-b` (worktree medas-p9-search-run4gyr)

Started 2026-10-19 18:50 with the campaign.py of 80c1649, which has neither
the restart logic nor an end time. While it runs, nothing in that worktree is
changed (a new commit there would make its next segments refuse to run: job
and program would name different commits). Its end: `runs/pids/stop-4gyr-at-end.sh`
stops it once segment 8 (beyond 4 Gyr) is made.

If it is interrupted (crash, reboot), with nothing of it running any more:

1. In the worktree: `git cherry-pick b2caf76` (only campaign.py changes; the
   integrator is the same, so the segments made again give the same bits).
2. `make` and `make gpu` there (the programs then name the new commit).
3. The start command of `start-4gyr-b.sh` with `--t-end 4e9` added. The
   finished segments are kept; the interrupted one is made again, so at most
   one segment (500 Myr, a few hours) is computed twice.
