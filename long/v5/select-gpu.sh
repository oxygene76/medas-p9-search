# MEDAS p9-search, paired long runs, group V5: sourced by start.sh and check.sh. Sets CUDA_VISIBLE_DEVICES to the
# UUID of the GPU whose name contains GPU_NAME (default L40S), unless it is set already or P9EQUIV_MODE=cpu.
# Without it CUDA chooses the card by its own order (on appmdp-05 possibly the A100 of the production run).
if [ "${P9EQUIV_MODE:-gpu}" != cpu ] && [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then
  uuid=$(nvidia-smi --query-gpu=uuid,name --format=csv,noheader | awk -F', ' -v n="${GPU_NAME:-L40S}" 'index($2, n) { print $1; exit }')
  [ -n "$uuid" ] || { echo "no GPU named ${GPU_NAME:-L40S} (GPU_NAME=...):"; nvidia-smi -L; exit 2; }
  CUDA_VISIBLE_DEVICES=$uuid
  export CUDA_VISIBLE_DEVICES
fi
