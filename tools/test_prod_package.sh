#!/bin/sh
# Tests a production package (tools/make_prod_package.sh) unpacked into a plain ubuntu:22.04 container, on the CPU
# (P9PROD_MODE=cpu, the CPU twin gives the GPU's bits): the whole check, then the run shortened to 2 segments of
# 5,000 years (its last segment must give the check's "chain" hash), then a resume after a simulated interruption
# (the second segment's result removed and its output damaged: computed again, the same hash).
#   tools/test_prod_package.sh build/p9prod-<rev>.tar.gz
set -eu
PKG=$(readlink -f "$1")
NAME=$(basename "$PKG" .tar.gz)
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PKG:/pkg.tar.gz:ro" ubuntu:22.04 sh -c "
  set -eu; cd /tmp; tar -xzf /pkg.tar.gz; cd $NAME
  sed -i 's/^SEGMENT_YR=.*/SEGMENT_YR=5000/; s/^SEGMENTS=.*/SEGMENTS=2/; s/^SNAPSHOTS_PER_SEGMENT=.*/SNAPSHOTS_PER_SEGMENT=1/' params.env
  export P9PROD_MODE=cpu
  sh start.sh
  while [ -f production.pid ] && kill -0 \$(cat production.pid) 2>/dev/null; do sleep 5; done
  cat check/report.txt | tail -n 3; cat production.log
  want=\$(awk '\$1 == \"chain\" { print \$6 }' check/EXPECTED)
  got=\$(tail -n 1 segments.tsv | cut -f5)
  [ \"\$got\" = \"\$want\" ] && echo \"TEST segments: SAME as chain (\$got)\" || { echo \"TEST segments: DIFFERENT \$got, expected \$want\"; exit 1; }
  rm segments/seg001/DONE; head -c 1000 segments/seg001/output.sa > x && mv x segments/seg001/output.sa; sed -i '\$d' segments.tsv
  sh start.sh
  while [ -f production.pid ] && kill -0 \$(cat production.pid) 2>/dev/null; do sleep 5; done
  got2=\$(tail -n 1 segments.tsv | cut -f5)
  [ \"\$got2\" = \"\$want\" ] && echo \"TEST resume: SAME (\$got2)\" || { echo \"TEST resume: DIFFERENT \$got2\"; exit 1; }
  sh status.sh
  sh start.sh || true; sh stop.sh
  echo 'TEST PASSED'"
