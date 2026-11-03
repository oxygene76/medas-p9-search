#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Stand-in for p9sim/p9gpu under tools/p9job.py run: writes the environment (P9_*) and the arguments that
# p9job.py gives the program into <job dir>/run.env, then runs the real program ($CAPTURE_REAL) unless
# CAPTURE_ONLY=1. So the speed package (speed/speed.sh) runs every job exactly as p9job.py would.
[ "$1" = version ] && exec "$CAPTURE_REAL" "$@"
d=$(dirname "$2")
{ env | grep '^P9' | LC_ALL=C sort; echo "ARGS=$1 input.sa $3 $4 $(basename "$5") $(basename "$6")"; } > "$d/run.env"
[ "${CAPTURE_ONLY:-0}" = 1 ] && exit 1
exec "$CAPTURE_REAL" "$@"
