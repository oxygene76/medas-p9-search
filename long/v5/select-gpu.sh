# MEDAS p9-search, paired long runs, group V5: sourced by start.sh and check.sh. Sets CUDA_VISIBLE_DEVICES to the
# UUID of the GPU whose name contains GPU_NAME (default A100), unless it is set already or P9EQUIV_MODE=cpu.
# Without it CUDA chooses the card by its own order (on appmdp-05 possibly the L40S of the AI services).
if [ "${P9EQUIV_MODE:-gpu}" != cpu ] && [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then
  uuid=$(nvidia-smi --query-gpu=uuid,name --format=csv,noheader | awk -F', ' -v n="${GPU_NAME:-A100}" 'index($2, n) { print $1; exit }')
  [ -n "$uuid" ] || { echo "no GPU named ${GPU_NAME:-A100} (GPU_NAME=...):"; nvidia-smi -L; exit 2; }
  CUDA_VISIBLE_DEVICES=$uuid
  export CUDA_VISIBLE_DEVICES
fi
