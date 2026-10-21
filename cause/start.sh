#!/bin/sh
# MEDAS p9-search, cause search: starts (or resumes) the check and the jobs in the background, as the current user.
#   JOBS="J1-dt025" sh start.sh  only one job; PARALLEL=0: the jobs one after the other
#   sh start.sh     then: sh status.sh   (stop: sh stop.sh; start.sh again resumes)
set -eu
cd "$(dirname "$0")"
if [ -f run.pid ] && kill -0 "$(cat run.pid)" 2>/dev/null; then
  echo "already running (pid $(cat run.pid)); sh status.sh"; exit 1
fi
[ "$(id -u)" != 0 ] || { echo "please run as a normal user, not as root"; exit 1; }
[ "${P9CAUSE_MODE:-gpu}" = cpu ] || command -v nvidia-smi > /dev/null 2>&1 || { echo "no nvidia-smi: is the NVIDIA driver installed?"; exit 2; }
need=$(cat bin/REQUIRES-glibc)
have=$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')
if [ -z "$have" ] || [ "$(printf '%s\n%s\n' "$need" "$have" | sort -V | head -n 1)" != "$need" ]; then
  echo "STOP: the binaries need glibc $need or newer, this system has ${have:-an unknown version}"; exit 3
fi
for j in jobs/*/; do [ "$(sha256sum "$j/input.sa" | cut -d' ' -f1)" = "$(cat "$j/INPUT-SHA256")" ] || { echo "$j/input.sa does not match its sha256"; exit 2; }; done
command -v setsid > /dev/null 2>&1 && S=setsid || S=""
nohup $S sh run-all.sh >> run.out 2>&1 < /dev/null &
echo $! > run.pid
sleep 2
if kill -0 "$(cat run.pid)" 2>/dev/null; then
  echo "started (pid $(cat run.pid)); first the check (a few minutes), then the jobs. Status: sh status.sh"
else
  echo "did not stay up; see run.log and run.out"; exit 1
fi
