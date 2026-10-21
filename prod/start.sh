#!/bin/sh
# MEDAS p9-search: starts (or resumes) the production run in the background, as the current user.
#   sh start.sh     then: sh status.sh   (stop: sh stop.sh; start.sh again resumes)
set -eu
cd "$(dirname "$0")"
if [ -f production.pid ] && kill -0 "$(cat production.pid)" 2>/dev/null; then
  echo "already running (pid $(cat production.pid)); sh status.sh"; exit 1
fi
[ "$(id -u)" != 0 ] || { echo "please run as a normal user, not as root"; exit 1; }
[ "${P9PROD_MODE:-gpu}" = cpu ] || command -v nvidia-smi > /dev/null 2>&1 || { echo "no nvidia-smi: is the NVIDIA driver installed?"; exit 2; }
need=$(cat bin/REQUIRES-glibc)
have=$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')
if [ -z "$have" ] || [ "$(printf '%s\n%s\n' "$need" "$have" | sort -V | head -n 1)" != "$need" ]; then
  echo "STOP: the binaries need glibc $need or newer, this system has ${have:-an unknown version}"; exit 3
fi
[ "$(sha256sum run/input.sa | cut -d' ' -f1)" = "$(cat run/INPUT-SHA256)" ] || { echo "run/input.sa does not match its sha256"; exit 2; }
command -v setsid > /dev/null 2>&1 && S=setsid || S=""
nohup $S sh run-production.sh >> production.out 2>&1 < /dev/null &
echo $! > production.pid
sleep 2
if kill -0 "$(cat production.pid)" 2>/dev/null; then
  echo "started (pid $(cat production.pid)); first the check (a few minutes), then the segments. Status: sh status.sh"
else
  echo "did not stay up; see production.log and production.out"; exit 1
fi
