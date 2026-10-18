#!/bin/sh
# Downloads REBOUND 5.2.2 (GPL-3.0-or-later) into third_party/ and checks its sha256.
set -eu
cd "$(dirname "$0")/.."
V=5.2.2
SUM=86038080c4392c8c19c4df2004d1804b30ca2aebd3c0329bfd1b02afc41d6eda
F=third_party/rebound-$V.tar.gz
mkdir -p third_party
[ -f "$F" ] || curl -fsSL -o "$F" "https://codeload.github.com/hannorein/rebound/tar.gz/refs/tags/$V"
echo "$SUM  $F" | sha256sum -c -
[ -d "third_party/rebound-$V" ] || tar -xzf "$F" -C third_party
echo "REBOUND $V in third_party/rebound-$V"
